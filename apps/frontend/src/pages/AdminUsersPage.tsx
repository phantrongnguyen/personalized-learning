import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BackendUser, RoleCode } from '@shared/types';
import { AlertCircle, ChevronLeft, ChevronRight, Eye, EyeOff, Loader2, LockKeyhole, Plus, RefreshCw, Search, ShieldCheck, UnlockKeyhole, Users, X } from 'lucide-react';
import { useApp } from '../state/AppContext';
import { createAccount, CreateAccountPayload, listAccounts, setAccountStatus } from '../services/admin';
import { AccountDetails } from '../components/admin/AccountDetails';

const PAGE_SIZE = 25;
const ROLE_LABELS: Record<RoleCode, string> = {
  STUDENT: 'Sinh viên', LECTURER: 'Giảng viên', ADVISOR: 'Cố vấn học tập', ADMIN: 'Quản trị viên',
};
const fieldClass = 'w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100';
const messageOf = (error: unknown) => error instanceof Error ? error.message : 'Có lỗi xảy ra. Vui lòng thử lại.';

function Modal({ title, children, onClose, busy = false }: { title: string; children: React.ReactNode; onClose: () => void; busy?: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  return (
    <dialog ref={dialog} aria-label={title} onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}
      className="admin-dialog w-[calc(100%_-_2rem)] max-w-xl rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-2xl">
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-6 py-4">
        <h2 className="text-lg font-bold">{title}</h2>
        <button type="button" disabled={busy} onClick={onClose} aria-label="Đóng hộp thoại" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 disabled:opacity-50"><X size={18} /></button>
      </div>
      {children}
    </dialog>
  );
}

function AccountForm({ onClose, onCreated }: { onClose: () => void; onCreated: (account: BackendUser) => void }) {
  const { apiBase } = useApp();
  const [role, setRole] = useState<RoleCode>('STUDENT');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const values = new FormData(event.currentTarget);
    const value = (name: string) => String(values.get(name) || '').trim();
    const password = String(values.get('password') || '');
    if (new TextEncoder().encode(password).length > 72) {
      setError('Mật khẩu không được vượt quá 72 byte.'); return;
    }
    const payload: CreateAccountPayload = {
      email: value('email'), full_name: value('full_name'), password, role_codes: [role],
      ...(value('phone_number') ? { phone_number: value('phone_number') } : {}),
      ...(role === 'STUDENT' ? { student_code: value('student_code') } : {}),
      ...(role === 'LECTURER' ? { lecturer_code: value('lecturer_code') } : {}),
      ...(role === 'LECTURER' || role === 'ADVISOR' ? { department: value('department') } : {}),
    };
    setBusy(true); setError('');
    try { onCreated(await createAccount(apiBase, payload)); }
    catch (err) { setError(messageOf(err)); }
    finally { setBusy(false); }
  }

  return (
    <Modal title="Cấp tài khoản mới" onClose={onClose} busy={busy}>
      <form onSubmit={submit} className="space-y-5 p-6">
        <p className="text-sm text-slate-500">Tạo tài khoản và hồ sơ phù hợp cho sinh viên, giảng viên hoặc cố vấn học tập.</p>
        {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        <fieldset disabled={busy} className="space-y-4 disabled:opacity-70">
          <label className="block space-y-1.5 text-sm font-semibold">Vai trò
            <select autoFocus value={role} onChange={(e) => { setRole(e.target.value as RoleCode); setError(''); }} className={fieldClass}>
              {(['STUDENT', 'LECTURER', 'ADVISOR'] as RoleCode[]).map((code) => <option key={code} value={code}>{ROLE_LABELS[code]}</option>)}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm font-semibold">Họ và tên <span className="text-rose-600">*</span>
            <input name="full_name" required maxLength={255} pattern=".*\S.*" autoComplete="name" placeholder="Nguyễn Văn An" className={fieldClass} />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block space-y-1.5 text-sm font-semibold">Email <span className="text-rose-600">*</span>
              <input name="email" required type="email" autoComplete="off" placeholder="taikhoan@huit.edu.vn" className={fieldClass} />
            </label>
            <label className="block space-y-1.5 text-sm font-semibold">Số điện thoại
              <input name="phone_number" type="tel" maxLength={30} autoComplete="tel" placeholder="Số điện thoại liên hệ" className={fieldClass} />
            </label>
          </div>
          {role === 'STUDENT' && <label className="block space-y-1.5 text-sm font-semibold">Mã sinh viên <span className="text-rose-600">*</span>
            <input name="student_code" required maxLength={50} pattern=".*\S.*" placeholder="2001234567" className={fieldClass} />
          </label>}
          {role === 'LECTURER' && <label className="block space-y-1.5 text-sm font-semibold">Mã giảng viên <span className="text-rose-600">*</span>
            <input name="lecturer_code" required maxLength={50} pattern=".*\S.*" placeholder="GV001" className={fieldClass} />
          </label>}
          {(role === 'LECTURER' || role === 'ADVISOR') && <label className="block space-y-1.5 text-sm font-semibold">Khoa / Bộ môn <span className="text-rose-600">*</span>
            <input name="department" required maxLength={150} pattern=".*\S.*" placeholder="Khoa Công nghệ Thông tin" className={fieldClass} />
          </label>}
          <label className="block space-y-1.5 text-sm font-semibold">Mật khẩu ban đầu <span className="text-rose-600">*</span>
            <span className="relative block">
              <input name="password" required minLength={6} type={showPassword ? 'text' : 'password'} autoComplete="new-password" placeholder="Tối thiểu 6 ký tự" className={`${fieldClass} pr-12`} />
              <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} className="absolute right-3 top-3 text-slate-500">{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
            </span>
          </label>
        </fieldset>
        <p className="rounded-xl bg-brand-50 p-3 text-xs leading-relaxed text-brand-700">Tài khoản được kích hoạt ngay sau khi tạo. Cung cấp mật khẩu ban đầu trực tiếp cho người nhận và hướng dẫn đổi mật khẩu sau khi đăng nhập.</p>
        <div className="flex justify-end gap-3 border-t border-slate-200 pt-4">
          <button type="button" disabled={busy} onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold disabled:opacity-50">Hủy</button>
          <button disabled={busy} className="flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50">{busy ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}{busy ? 'Đang cấp tài khoản…' : 'Cấp tài khoản'}</button>
        </div>
      </form>
    </Modal>
  );
}

export const AdminUsersPage: React.FC = () => {
  const { user, apiBase, addToast } = useApp();
  const isAdmin = user?.roleCode === 'ADMIN';
  const [accounts, setAccounts] = useState<BackendUser[]>([]);
  const [page, setPage] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState<{ id: string; mode: 'view' | 'edit' | 'delete' } | null>(null);
  const [selected, setSelected] = useState<BackendUser | null>(null);
  const [updating, setUpdating] = useState(false);
  const [statusError, setStatusError] = useState('');

  useEffect(() => {
    if (!isAdmin) return;
    const abort = new AbortController();
    setLoading(true); setError(''); setAccounts([]); setHasNext(false);
    listAccounts(apiBase, page * PAGE_SIZE, PAGE_SIZE + 1, abort.signal)
      .then((rows) => { if (!abort.signal.aborted) { setAccounts(rows.slice(0, PAGE_SIZE)); setHasNext(rows.length > PAGE_SIZE); } })
      .catch((err) => { if (!abort.signal.aborted) setError(messageOf(err)); })
      .finally(() => { if (!abort.signal.aborted) setLoading(false); });
    return () => abort.abort();
  }, [apiBase, isAdmin, page, revision]);

  const filtered = useMemo(() => accounts.filter((account) => {
    const code = account.student_profile?.student_code || account.lecturer_profile?.lecturer_code || '';
    const text = `${account.full_name} ${account.email} ${code}`.toLocaleLowerCase('vi');
    return text.includes(search.trim().toLocaleLowerCase('vi'))
      && (roleFilter === 'ALL' || account.roles.some((role) => role.code === roleFilter))
      && (statusFilter === 'ALL' || account.is_active === (statusFilter === 'ACTIVE'));
  }), [accounts, search, roleFilter, statusFilter]);

  async function confirmStatus() {
    if (!selected || updating) return;
    setUpdating(true); setStatusError('');
    try {
      const result = await setAccountStatus(apiBase, selected.id, !selected.is_active);
      setAccounts((rows) => rows.map((row) => row.id === selected.id ? { ...row, is_active: !selected.is_active } : row));
      addToast(result.message, 'success'); setSelected(null);
    } catch (err) { setStatusError(messageOf(err)); }
    finally { setUpdating(false); }
  }

  if (!isAdmin) return <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-800"><ShieldCheck className="mb-3" /><h1 className="font-bold">Quyền truy cập bị giới hạn</h1><p className="mt-2 text-sm">Chỉ quản trị viên được phép quản lý và cấp tài khoản.</p></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><div className="mb-2 text-xs font-semibold uppercase tracking-wider text-brand-600">Không gian quản trị</div><h1 className="flex items-center gap-3 text-2xl font-bold text-slate-900"><Users className="text-brand-600" />Quản lý tài khoản</h1><p className="mt-2 text-sm text-slate-500">Cấp tài khoản và quản lý truy cập cho sinh viên, giảng viên, cố vấn học tập.</p></div>
        <button onClick={() => setCreateOpen(true)} className="flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700"><Plus size={18} />Cấp tài khoản</button>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          ['Tài khoản trong trang', accounts.length],
          ['Sinh viên', accounts.filter((item) => item.roles.some((role) => role.code === 'STUDENT')).length],
          ['Giảng viên / Cố vấn', accounts.filter((item) => item.roles.some((role) => ['LECTURER', 'ADVISOR'].includes(role.code))).length],
          ['Đang hoạt động', accounts.filter((item) => item.is_active).length],
        ].map(([label, count]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-3 text-3xl font-bold text-brand-600">{loading || error ? '—' : count}</p></div>)}
      </div>
      <section aria-label="Danh sách tài khoản" className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 p-5">
          <label className="relative min-w-56 flex-1"><span className="sr-only">Tìm tài khoản trong trang hiện tại</span><Search size={17} className="absolute left-3 top-3 text-slate-400" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm tên, email, mã SV/GV trong trang…" className={`${fieldClass} pl-10`} /></label>
          <select aria-label="Lọc theo vai trò" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className={`${fieldClass} sm:w-auto`}><option value="ALL">Tất cả vai trò</option>{Object.entries(ROLE_LABELS).map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select>
          <select aria-label="Lọc trạng thái" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={`${fieldClass} sm:w-auto`}><option value="ALL">Tất cả trạng thái</option><option value="ACTIVE">Đang hoạt động</option><option value="LOCKED">Đã khóa</option></select>
          <button onClick={() => setRevision((v) => v + 1)} disabled={loading} aria-label="Tải lại danh sách" className="rounded-xl border border-slate-200 p-3 text-brand-600 disabled:opacity-50"><RefreshCw size={17} className={loading ? 'animate-spin' : ''} /></button>
        </div>
        {error ? <div role="alert" className="space-y-3 p-8 text-center"><AlertCircle className="mx-auto text-rose-600" /><p className="text-sm text-rose-700">{error}</p><button onClick={() => setRevision((v) => v + 1)} className="text-sm font-semibold text-brand-600">Thử lại</button></div>
          : <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr>{['Tài khoản', 'Mã SV / GV', 'Vai trò', 'Trạng thái', 'Ngày cấp', 'Thao tác'].map((label) => <th key={label} scope="col" className="px-5 py-4 font-semibold">{label}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? <tr><td colSpan={6} className="p-12 text-center text-slate-500"><Loader2 size={22} className="mx-auto mb-3 animate-spin" />Đang tải tài khoản…</td></tr>
                : filtered.length === 0 ? <tr><td colSpan={6} className="p-12 text-center text-slate-500">{accounts.length ? 'Không có tài khoản phù hợp với bộ lọc trong trang này.' : 'Chưa có tài khoản trong trang này.'}</td></tr>
                : filtered.map((account) => <tr key={account.id} className="hover:bg-slate-50">
                  <td className="px-5 py-4"><div className="font-semibold text-slate-900">{account.full_name}</div><div className="mt-1 text-xs text-slate-500">{account.email}</div><div className="mt-2 flex gap-3 text-xs"><button onClick={() => setDetail({ id: account.id, mode: 'view' })} className="text-brand-600 font-semibold">Xem</button><button onClick={() => setDetail({ id: account.id, mode: 'edit' })} className="text-brand-600 font-semibold">Sửa</button><button disabled={account.email === user?.email} onClick={() => setDetail({ id: account.id, mode: 'delete' })} className="text-rose-600 font-semibold disabled:opacity-30">Xóa</button></div></td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-600">{account.student_profile?.student_code || account.lecturer_profile?.lecturer_code || '—'}</td>
                  <td className="px-5 py-4"><div className="flex flex-wrap gap-1">{account.roles.map((role) => <span key={role.code} className="rounded-lg bg-brand-50 px-2 py-1 text-xs font-medium text-brand-700">{ROLE_LABELS[role.code]}</span>)}</div></td>
                  <td className="px-5 py-4"><span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${account.is_active ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-700'}`}><span className={`h-1.5 w-1.5 rounded-full ${account.is_active ? 'bg-brand-600' : 'bg-rose-600'}`} />{account.is_active ? 'Hoạt động' : 'Đã khóa'}</span></td>
                  <td className="px-5 py-4 text-xs text-slate-500">{new Date(account.created_at).toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}</td>
                  <td className="px-5 py-4"><button disabled={account.email === user?.email} title={account.email === user?.email ? 'Không thể khóa tài khoản đang sử dụng' : undefined} onClick={() => { setSelected(account); setStatusError(''); }} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40">{account.is_active ? <LockKeyhole size={14} /> : <UnlockKeyhole size={14} />}{account.is_active ? 'Khóa' : 'Mở khóa'}</button></td>
                </tr>)}
            </tbody>
          </table></div>}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-xs text-slate-500">
          <span>Trang {page + 1} · {filtered.length}/{accounts.length} tài khoản · Bộ lọc áp dụng trong trang hiện tại</span>
          <div className="flex gap-2"><button aria-label="Trang trước" disabled={page === 0 || loading} onClick={() => setPage((v) => v - 1)} className="rounded-lg border border-slate-200 p-2 disabled:opacity-40"><ChevronLeft size={16} /></button><button aria-label="Trang tiếp theo" disabled={!hasNext || loading} onClick={() => setPage((v) => v + 1)} className="rounded-lg border border-slate-200 p-2 disabled:opacity-40"><ChevronRight size={16} /></button></div>
        </div>
      </section>
      {createOpen && <AccountForm onClose={() => setCreateOpen(false)} onCreated={(account) => { setCreateOpen(false); setPage(0); setRevision((v) => v + 1); setSearch(''); setRoleFilter('ALL'); setStatusFilter('ALL'); addToast(`Đã cấp tài khoản cho ${account.full_name}.`, 'success'); }} />}
      {detail && <AccountDetails key={detail.id + detail.mode} {...detail} onClose={() => setDetail(null)} onChanged={() => { setPage(0); setRevision(v => v + 1); }} />}
      {selected && <Modal title={selected.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'} busy={updating} onClose={() => setSelected(null)}>
        <div className="space-y-5 p-6"><p className="text-sm text-slate-600">{selected.is_active ? 'Tài khoản sẽ không thể đăng nhập hoặc sử dụng hệ thống.' : 'Tài khoản sẽ được phép đăng nhập và sử dụng hệ thống trở lại.'}</p><div className="rounded-xl bg-slate-50 p-4"><p className="font-semibold">{selected.full_name}</p><p className="mt-1 text-sm text-slate-500">{selected.email}</p></div>{statusError && <p role="alert" className="text-sm text-rose-700">{statusError}</p>}<div className="flex justify-end gap-3"><button disabled={updating} onClick={() => setSelected(null)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold">Hủy</button><button disabled={updating} onClick={confirmStatus} className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 ${selected.is_active ? 'bg-rose-600' : 'bg-brand-600'}`}>{updating && <Loader2 size={16} className="animate-spin" />}{selected.is_active ? 'Xác nhận khóa' : 'Xác nhận mở khóa'}</button></div></div>
      </Modal>}
    </div>
  );
};
