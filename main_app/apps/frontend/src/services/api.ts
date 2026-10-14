import { HistoricalCasesResponse, PredictionRequest, PredictionResponse, StudentFeatures } from '@shared/types';

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
}

export async function checkBackendHealth(baseUrl: string): Promise<{ data: HealthResponse; latency: number }> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const startTime = performance.now();
  
  const res = await fetch(`${cleanUrl}/api/v1/health`, {
    signal: AbortSignal.timeout(6000),
  });

  const latency = Math.round(performance.now() - startTime);
  if (!res.ok) {
    throw new Error(`Máy chủ trả về mã lỗi HTTP ${res.status}`);
  }

  const data = (await res.json()) as HealthResponse;
  return { data, latency };
}

export async function predictStudentRisk(
  baseUrl: string,
  features: StudentFeatures
): Promise<PredictionResponse> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const payload: PredictionRequest = { features };

  const res = await fetch(`${cleanUrl}/api/v1/predictions/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(20000),
  });

  if (!res.ok) {
    let errorDetail = `Lỗi HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      if (res.status === 503) {
        errorDetail = 'Mô hình học máy LightGBM chưa được nạp sẵn trên máy chủ Backend.';
      } else if (res.status === 422 && Array.isArray(errorJson.detail)) {
        const item = errorJson.detail[0];
        const field = (item.loc || []).slice(-1)[0];
        errorDetail = `Dữ liệu không hợp lệ tại trường '${field}': ${item.msg}`;
      } else if (typeof errorJson.detail === 'string') {
        errorDetail = errorJson.detail;
      }
    } catch {
      // Fallback to HTTP error
    }
    throw new Error(errorDetail);
  }

  return (await res.json()) as PredictionResponse;
}

export async function compareHistoricalCases(
  baseUrl: string,
  features: StudentFeatures,
  signal: AbortSignal,
): Promise<HistoricalCasesResponse> {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal.addEventListener('abort', cancel, { once: true });
  if (signal.aborted) controller.abort();
  const timeout = setTimeout(cancel, 20000);
  try {
    const response = await fetch(`${baseUrl.trim().replace(/\/+$/, '')}/api/v1/historical-cases/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ features, cutoff_fraction: 0.75 }),
      signal: controller.signal,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new Error(typeof error?.detail === 'string' ? error.detail : `Không thể đối chiếu lịch sử (HTTP ${response.status}).`);
    }
    return await response.json() as HistoricalCasesResponse;
  } finally {
    clearTimeout(timeout);
    signal.removeEventListener('abort', cancel);
  }
}
