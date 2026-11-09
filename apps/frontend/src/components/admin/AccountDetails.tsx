import React, { useEffect, useRef, useState } from 'react';
import { BackendUser } from '@shared/types';
import { useApp } from '../../state/AppContext';
import { mapBackendUser } from '../../services/api';
import { deleteAccount, getAccount, updateAccount, UpdateAccountPayload } from '../../services/admin';

export function AccountDetails({ id, mode, onClose, onChanged }: { id: string; mode: 'view' | 'edit' | 'delete'; onClose: () => void; onChanged: () => void }) {
  const { apiBase, user, updateUser, addToast } = useApp();
  const dialog = useRef<HTMLDialogElement>(null);
  const [account, setAccount] = useState<BackendUser | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => { dialog.current?.showModal(); }, []);
  useEffect(() => {
    const abort = new AbortController(); setAccount(null); setError('');
    getAccount(apiBase, id, abort.signal).then(data => { if (!abort.signal.aborted) setAccount(data); }).catch(err => { if (!abort.signal.aborted) setError(err instanceof Error ? err.message : 'Không thể tải tài khoản.'); });
    return () => abort.abort();
  }, [apiBase, id, attempt]);
  const editable = mode === 'edit';
  const fields: { name: keyof UpdateAccountPayload; label: string; value?: string | null; required?: boolean; max: number; type?: string }[] = account ? [
    { name: 'full_name', label: 'Họ và tên', value: account.full_name, required: true, max: 150 },
    { name: 'email', label: 'Email', value: account.email, required: true, max: 255, type: 'email' },
    { name: 'phone_number', label: 'Số điện thoại', value: account.phone_number, max: 20, type: 'tel' },
    ...(account.student_profile ? [{ name: 'student_code' as const, label: 'Mã sinh viên', value: account.student_profile.student_code, required: true, max: 50 }] : []),
    ...(account.lecturer_profile ? [{ name: 'lecturer_code' as const, label: 'Mã giảng viên', value: account.lecturer_profile.lecturer_code, required: true, max: 50 }, { name: 'academic_rank' as const, label: 'Học hàm / học vị', value: account.lecturer_profile.academic_rank, required: true, max: 50 }] : []),
    ...(account.advisor_profile || account.lecturer_profile ? [{ name: 'department' as const, label: 'Khoa / đơn vị', value: account.advisor_profile?.department || account.lecturer_profile?.department, required: true, max: 150 }] : []),
    ...(account.advisor_profile ? [{ name: 'office_location' as const, label: 'Phòng làm việc', value: account.advisor_profile.office_location, max: 100 }] : []),
  ] : [];
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!account || busy || !editable) return;
    const form = new FormData(event.currentTarget); const payload: UpdateAccountPayload = {};
    for (const field of fields) {
      const value = String(form.get(field.name) || '').trim();
      if (field.required && !value) { setError(`${field.label} không được để trống.`); return; }
      if (value !== (field.value || '')) payload[field.name] = value;
    }
    if (!Object.keys(payload).length) { onClose(); return; }
    setBusy(true); setError('');
    try {
      const updated = await updateAccount(apiBase, id, payload);
      if (account.email === user?.email) updateUser(mapBackendUser(updated)); else addToast('Đã cập nhật tài khoản.', 'success');
      onChanged(); onClose();
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể cập nhật tài khoản.'); }
    finally { setBusy(false); }
  }
  async function remove() {
    if (!account || busy || confirmation !== account.email || account.email === user?.email) return;
    setBusy(true); setError('');
    try { const result = await deleteAccount(apiBase, id); addToast(result.message, 'success'); onChanged(); onClose(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Không thể xóa tài khoản.'); }
    finally { setBusy(false); }
  }
  const title = mode === 'view' ? 'Chi tiết tài khoản' : editable ? 'Sửa tài khoản' : 'Xóa tài khoản';
  return <dialog ref={dialog} aria-label={title} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }} className="admin-dialog w-[calc(100%_-_2rem)] max-w-xl rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-2xl">
    <div className="flex justify-between items-center mb-5"><h2 className="text-xl font-bold">{title}</h2><button aria-label="Đóng hộp thoại" disabled={busy} onClick={onClose} className="px-3 py-2 rounded-lg border">Đóng</button></div>
    {error && <p role="alert" className="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    {!account ? <div className="text-sm text-slate-500">{error ? <button onClick={() => setAttempt(v => v + 1)} className="text-brand-600">Thử lại</button> : 'Đang tải thông tin…'}</div> : mode === 'delete' ? <div className="space-y-4">
      <p className="font-semibold">{account.full_name} · {account.email}</p>
      <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">Xóa vĩnh viễn tài khoản, hồ sơ, phân công và dữ liệu học tập liên quan theo quan hệ database. Thao tác không thể hoàn tác. Bạn có thể khóa tài khoản để giữ lại dữ liệu.</p>
      <label className="block text-sm">Nhập email tài khoản để xác nhận<input autoComplete="off" value={confirmation} disabled={busy} onChange={e => setConfirmation(e.target.value)} className="mt-2 w-full rounded-xl border px-3 py-2" /></label>
      <button disabled={busy || confirmation !== account.email || account.email === user?.email} onClick={remove} className="rounded-xl bg-rose-600 px-4 py-3 text-white font-semibold disabled:opacity-40">{busy ? 'Đang xóa…' : 'Xóa vĩnh viễn'}</button>
    </div> : <form onSubmit={submit} className="space-y-4">
      <p className="text-sm text-slate-500">Vai trò: {account.roles.map(role => role.name).join(', ')} · {account.is_active ? 'Đang hoạt động' : 'Đã khóa'}</p>
      {!editable && <p className="text-xs text-slate-500">Ngày cấp: {new Date(account.created_at).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}</p>}
      <fieldset disabled={busy} className="space-y-4">{fields.map(field => <label key={field.name} className="block text-sm font-medium">{field.label}{editable ? <input name={field.name} defaultValue={field.value || ''} type={field.type || 'text'} required={field.required} maxLength={field.max} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5" /> : <span className="mt-1 block break-words font-normal text-slate-600">{field.value || 'Chưa cập nhật'}</span>}</label>)}</fieldset>
      {editable && <button disabled={busy} className="rounded-xl bg-brand-600 px-5 py-3 text-white font-semibold disabled:opacity-40">{busy ? 'Đang lưu…' : 'Lưu thay đổi'}</button>}
    </form>}
  </dialog>;
}
