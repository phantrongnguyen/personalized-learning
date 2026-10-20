import { authenticatedFetch, getStoredToken, setStoredTokens, clearStoredTokens, getSessionEpoch } from './session';
import {
  PredictionRequest,
  PredictionResponse,
  StudentFeatures,
  AuthTokens,
  BackendUser,
  UserProfile,
  AdvisorClassSummary,
  AdvisorStudentItem,
  CreateInterventionPlanPayload,
  LecturerCourseItem,
  CourseStudentRiskItem,
  CourseSuggestionResponse,
  StudentCourseItem,
  CourseReminder,
  StudentProfileDetail,
  StudentRiskPrediction,
  StudentRadarData,
  StudentTaskItem,
  StudentHelpRequestItem,
} from '@shared/types';

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
}

function cleanBase(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, '');
}

/**
 * Chuyển đổi dữ liệu người dùng trả về từ Backend (BackendUser)
 * sang interface hiển thị ở Frontend (UserProfile).
 */
export function mapBackendUser(user: BackendUser): UserProfile {
  const primaryRole = user.roles.find((role) => role.code === 'ADMIN') || user.roles[0];
  const department =
    user.advisor_profile?.department ||
    user.lecturer_profile?.department || undefined;

  const derivedInitials = user.full_name
    .trim()
    .split(/\s+/)
    .map((word) => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return {
    userId: user.id,
    name: user.full_name,
    email: user.email,
    role: primaryRole?.name || 'Thành viên',
    roleCode: primaryRole?.code,
    initials: derivedInitials || 'US',
    department,
    phone: user.phone_number || undefined,
    avatarUrl: user.avatar_url || undefined,
    studentCode: user.student_profile?.student_code,
    lecturerCode: user.lecturer_profile?.lecturer_code,
    academicRank: user.lecturer_profile?.academic_rank,
    officeLocation: user.advisor_profile?.office_location || undefined,
    organization: 'Trường Đại học Công Thương TP. Hồ Chí Minh',
  };
}

export { TOKEN_KEY, REFRESH_TOKEN_KEY, getStoredToken, setStoredTokens, clearStoredTokens } from './session';
function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// -------------------------------------------------------------
// 1. HEALTH & PREDICTIONS
// -------------------------------------------------------------
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

  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/predictions/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
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
      // Fallback
    }
    throw new Error(errorDetail);
  }

  return (await res.json()) as PredictionResponse;
}

// -------------------------------------------------------------
// 2. AUTHENTICATION APIS
// -------------------------------------------------------------
export async function loginApi(
  baseUrl: string,
  username: string,
  password: string
): Promise<{ user: BackendUser; tokens: AuthTokens }> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await fetch(`${cleanUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: username.trim(), password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Đăng nhập không thành công');
  }

  const tokens = (await res.json()) as AuthTokens;
  setStoredTokens(tokens.access_token, tokens.refresh_token);

  // Lấy thông tin user hiện tại
  const meRes = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!meRes.ok) {
    clearStoredTokens();
    throw new Error('Không thể tải thông tin tài khoản');
  }

  const user = (await meRes.json()) as BackendUser;
  return { user, tokens };
}

export async function getCurrentUserApi(baseUrl: string): Promise<BackendUser | null> {
  const token = getStoredToken();
  if (!token) return null;

  const cleanUrl = cleanBase(baseUrl);
  try {
    const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      return (await res.json()) as BackendUser;
    }
    if (res.status === 401 || res.status === 403) clearStoredTokens();
    return null;
  } catch {
    return null;
  }
}

export interface UpdateProfilePayload {
  full_name?: string;
  phone_number?: string;
  avatar_url?: string;
}

export async function updateProfileApi(
  baseUrl: string,
  payload: UpdateProfilePayload
): Promise<BackendUser> {
  const cleanUrl = cleanBase(baseUrl);
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/auth/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể cập nhật hồ sơ cá nhân');
  }
  return (await res.json()) as BackendUser;
}

export async function uploadAvatarApi(baseUrl: string, file: File): Promise<BackendUser> {
  const data = new FormData();
  data.append('file', file);
  const res = await authenticatedFetch(baseUrl, `${cleanBase(baseUrl)}/api/v1/auth/profile/avatar`, {
    method: 'POST', headers: authHeaders(), body: data,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Không thể tải ảnh đại diện');
  }
  return (await res.json()) as BackendUser;
}

// -------------------------------------------------------------
// 3. ADVISOR APIS (GIÁO VIÊN CHỦ NHIỆM)
// -------------------------------------------------------------
export async function getAdvisorClassesApi(baseUrl: string): Promise<AdvisorClassSummary[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/advisor/classes`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải danh sách lớp chủ nhiệm');
  return res.json();
}

export async function getAdvisorStudentsApi(
  baseUrl: string,
  className?: string
): Promise<AdvisorStudentItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const url = className
    ? `${cleanUrl}/api/v1/advisor/students?class_name=${encodeURIComponent(className)}`
    : `${cleanUrl}/api/v1/advisor/students`;

  return fetchAllPages<AdvisorStudentItem>(baseUrl, url, 'Không thể tải danh sách sinh viên lớp chủ nhiệm');
}

async function fetchAllPages<T>(baseUrl: string, url: string, message: string): Promise<T[]> {
  const result: T[] = [];
  const epoch = getSessionEpoch();
  const limit = 100;
  for (let offset = 0; ; offset += limit) {
    if (getSessionEpoch() !== epoch) throw new DOMException('Session changed', 'AbortError');
    const res = await authenticatedFetch(baseUrl,
      `${url}${url.includes('?') ? '&' : '?'}limit=${limit}&offset=${offset}`, { headers: authHeaders() });
    if (!res.ok) throw new Error(message);
    const page: T[] = await res.json();
    if (getSessionEpoch() !== epoch) throw new DOMException('Session changed', 'AbortError');
    result.push(...page);
    if (page.length < limit) return result;
  }
}

export async function createInterventionPlanApi(
  baseUrl: string,
  payload: CreateInterventionPlanPayload
): Promise<any> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/advisor/interventions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể tạo kế hoạch can thiệp');
  }
  return res.json();
}

// -------------------------------------------------------------
// 4. LECTURER APIS (GIÁO VIÊN BỘ MÔN)
// -------------------------------------------------------------
export async function getLecturerCoursesApi(baseUrl: string): Promise<LecturerCourseItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/lecturer/courses`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải danh sách lớp học phần phụ trách');
  return res.json();
}

export async function getCourseRiskBoardApi(
  baseUrl: string,
  presentationId: string
): Promise<CourseStudentRiskItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  return fetchAllPages<CourseStudentRiskItem>(baseUrl,
    `${cleanUrl}/api/v1/lecturer/courses/${presentationId}/risk-board`, 'Không thể tải bảng cảnh báo nguy cơ học phần');
}

// -------------------------------------------------------------
// 5. STUDENT APIS (SINH VIÊN)
// -------------------------------------------------------------
export async function getCourseSuggestionsApi(baseUrl: string, presentationId: string, studentId: string): Promise<CourseSuggestionResponse> {
  const res = await authenticatedFetch(baseUrl, `${cleanBase(baseUrl)}/api/v1/lecturer/courses/${presentationId}/students/${studentId}/suggestions`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải gợi ý cho sinh viên trong học phần');
  return res.json();
}

export async function getCourseRemindersApi(baseUrl: string, signal?: AbortSignal): Promise<CourseReminder[]> {
  const res = await authenticatedFetch(baseUrl, `${cleanBase(baseUrl)}/api/v1/student/reminders`, { headers: authHeaders(), signal });
  if (!res.ok) throw new Error('Không thể tải thông báo nhắc nhở môn học.');
  return res.json();
}

export async function getStudentProfileApi(baseUrl: string): Promise<StudentProfileDetail> {
  const res = await authenticatedFetch(baseUrl, `${cleanBase(baseUrl)}/api/v1/student/profile`, { headers: authHeaders() });
  if (!res.ok) {
    throw new Error(res.status === 404 ? 'Tài khoản chưa có hồ sơ sinh viên.' : 'Không thể tải thông tin sinh viên.');
  }
  return res.json();
}

export async function getStudentCoursesApi(baseUrl: string): Promise<StudentCourseItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/courses`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải danh sách môn học của sinh viên');
  return res.json();
}

export async function getStudentRiskPredictionApi(
  baseUrl: string,
  enrollmentId: string
): Promise<StudentRiskPrediction | null> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/courses/${enrollmentId}/risk-prediction`, {
    headers: authHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Không thể tải dự báo nguy cơ học tập');
  return res.json();
}

export async function getStudentRadarApi(
  baseUrl: string,
  enrollmentId: string
): Promise<StudentRadarData | null> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/courses/${enrollmentId}/radar`, {
    headers: authHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Không thể tải biểu đồ Radar năng lực 6D');
  return res.json();
}

export async function getStudentTasksApi(baseUrl: string, enrollmentId?: string): Promise<StudentTaskItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/tasks${enrollmentId ? `?enrollment_id=${encodeURIComponent(enrollmentId)}` : ''}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải danh sách nhiệm vụ cần làm');
  return res.json();
}

export async function completeStudentTaskApi(
  baseUrl: string,
  taskId: string,
  feedback?: string,
  enrollmentId?: string
): Promise<StudentTaskItem> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/tasks/${taskId}/complete`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ student_feedback: feedback || '', enrollment_id: enrollmentId }),
  });
  if (!res.ok) throw new Error('Không thể cập nhật trạng thái nhiệm vụ');
  return res.json();
}

export async function getStudentHelpRequestsApi(baseUrl: string, enrollmentId?: string): Promise<StudentHelpRequestItem[]> {
  const cleanUrl = baseUrl.trim().replace(/\/+$/, '');
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/help-requests${enrollmentId ? `?enrollment_id=${encodeURIComponent(enrollmentId)}` : ''}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải danh sách yêu cầu trợ giúp');
  return res.json();
}

export interface CreateHelpRequestPayload {
  enrollment_id?: string;
  target_role: 'ADVISOR' | 'LECTURER';
  presentation_id?: string;
  target_user_id?: string;
  subject: string;
  content: string;
}

export async function createHelpRequestApi(
  baseUrl: string,
  payload: CreateHelpRequestPayload
): Promise<StudentHelpRequestItem> {
  const cleanUrl = cleanBase(baseUrl);
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/student/help-requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể gửi yêu cầu trợ giúp');
  }
  return res.json();
}

// -------------------------------------------------------------
// 6. LECTURER EXTRA APIS
// -------------------------------------------------------------
export interface AssignCourseTaskPayload {
  student_id: string;
  title: string;
  description: string;
  priority?: 'HIGH' | 'MEDIUM' | 'LOW';
  target_metric?: string;
}

export async function assignCourseTaskApi(
  baseUrl: string,
  presentationId: string,
  payload: AssignCourseTaskPayload
): Promise<StudentTaskItem> {
  const cleanUrl = cleanBase(baseUrl);
  const res = await authenticatedFetch(baseUrl,
    `${cleanUrl}/api/v1/lecturer/courses/${presentationId}/tasks`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể giao bài tập bổ trợ cho sinh viên');
  }
  return res.json();
}

export interface AlertAdvisorPayload {
  presentation_id: string;
  subject?: string;
  content: string;
}

export async function alertAdvisorApi(
  baseUrl: string,
  studentId: string,
  payload: AlertAdvisorPayload
): Promise<{ message: string; alert_id: string }> {
  const cleanUrl = cleanBase(baseUrl);
  const res = await authenticatedFetch(baseUrl,
    `${cleanUrl}/api/v1/lecturer/students/${studentId}/alert-advisor`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể gửi cảnh báo học vụ');
  }
  return res.json();
}

// -------------------------------------------------------------
// 7. ADVISOR EXTRA APIS
// -------------------------------------------------------------
export interface AdvisingNotePayload {
  enrollment_id: string;
  meeting_date: string;
  meeting_type?: string;
  content: string;
  agreed_actions?: string;
}

export async function createAdvisingNoteApi(
  baseUrl: string,
  payload: AdvisingNotePayload
): Promise<any> {
  const cleanUrl = cleanBase(baseUrl);
  const res = await authenticatedFetch(baseUrl, `${cleanUrl}/api/v1/advisor/advising-notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể lưu ghi chép tư vấn');
  }
  return res.json();
}


export async function getAdvisorStudentCoursesApi(baseUrl: string, studentId: string): Promise<StudentCourseItem[]> {
  const res = await authenticatedFetch(baseUrl, `${cleanBase(baseUrl)}/api/v1/advisor/students/${encodeURIComponent(studentId)}/overview`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Không thể tải học phần của sinh viên');
  const overview = await res.json();
  return overview.courses;
}
