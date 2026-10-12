import { BackendUser, RoleCode } from '@shared/types';
import { getStoredToken } from './api';

export interface CreateAccountPayload {
  email: string;
  password: string;
  full_name: string;
  phone_number?: string;
  role_codes: RoleCode[];
  student_code?: string;
  lecturer_code?: string;
  department?: string;
}

export interface UpdateAccountPayload {
  email?: string; full_name?: string; phone_number?: string; student_code?: string;
  lecturer_code?: string; department?: string; academic_rank?: string; office_location?: string;
}
export const getAccount = (base: string, id: string, signal?: AbortSignal) =>
  adminRequest<BackendUser>(base, `/users/${encodeURIComponent(id)}`, { signal });
export const updateAccount = (base: string, id: string, payload: UpdateAccountPayload) =>
  adminRequest<BackendUser>(base, `/users/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(payload) });
export const deleteAccount = (base: string, id: string) =>
  adminRequest<{ message: string }>(base, `/users/${encodeURIComponent(id)}`, { method: 'DELETE' });

async function adminRequest<T>(base: string, path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  if (!token) throw new Error('Vui lòng đăng nhập bằng tài khoản quản trị để tiếp tục.');
  const response = await fetch(`${base.trim().replace(/\/+$/, '')}/api/v1/admin${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    signal: options.signal
      ? AbortSignal.any([options.signal, AbortSignal.timeout(15000)])
      : AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
    if (response.status === 403) throw new Error('Bạn không có quyền quản lý tài khoản.');
    const detail = typeof data.detail === 'string' ? data.detail
      : Array.isArray(data.detail) ? data.detail.map((item: { msg: string }) => item.msg).join('; ') : null;
    throw new Error(detail || `Không thể thực hiện thao tác (HTTP ${response.status}).`);
  }
  return response.json();
}

export const listAccounts = (base: string, skip: number, limit: number, signal?: AbortSignal) =>
  adminRequest<BackendUser[]>(base, `/users?skip=${skip}&limit=${limit}`, { signal });

export const createAccount = (base: string, payload: CreateAccountPayload) =>
  adminRequest<BackendUser>(base, '/users', { method: 'POST', body: JSON.stringify(payload) });

export const setAccountStatus = (base: string, id: string, active: boolean) =>
  adminRequest<{ message: string }>(base, `/users/${encodeURIComponent(id)}/status`, {
    method: 'PUT', body: JSON.stringify({ is_active: active }),
  });
