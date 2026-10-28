import React, { useEffect, useRef, useState } from 'react';
import { BackendUser } from '@shared/types';
import { Eye, EyeOff, KeyRound, Loader2, X } from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { resetAccountPassword } from '../../services/admin';

export function ResetPasswordDialog({ account, onClose }: { account: BackendUser; onClose: () => void }) {
  const { apiBase, addToast } = useApp();
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [visible, setVisible] = useState(false);
  useEffect(() => { dialog.current?.showModal(); }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const password = String(data.get('new_password') || '');
    const confirmation = String(data.get('confirm_password') || '');
    if (password.length < 6 || !password.trim()) { setError('Mật khẩu phải có ít nhất 6 ký tự và không được chỉ chứa khoảng trắng.'); return; }
    if (new TextEncoder().encode(password).length > 72) { setError('Mật khẩu không được vượt quá 72 byte UTF-8.'); return; }
    if (password !== confirmation) { setError('Xác nhận mật khẩu không khớp.'); return; }
    setBusy(true); setError('');
    try {
      const result = await resetAccountPassword(apiBase, account.id, password);
      form.reset();
      addToast(result.message, 'success');
      onClose();
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể đặt lại mật khẩu. Vui lòng thử lại.'); }
    finally { setBusy(false); }
  }

  return <dialog ref={dialog} aria-label="Đặt lại mật khẩu" onCancel={event => { event.preventDefault(); if (!busy) onClose(); }} className="admin-dialog w-[calc(100%_-_2rem)] max-w-xl rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-2xl">
    <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
      <h2 className="flex items-center gap-2 text-lg font-bold"><KeyRound size={20} className="text-brand-600" />Đặt lại mật khẩu</h2>
      <button type="button" disabled={busy} onClick={onClose} aria-label="Đóng hộp thoại" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 disabled:opacity-50"><X size={18} /></button>
    </div>
    <form onSubmit={submit} className="space-y-5 p-6">
      <div className="rounded-xl bg-slate-50 p-4"><p className="font-semibold">{account.full_name}</p><p className="mt-1 text-sm text-slate-500 break-all">{account.email}</p></div>
      <p className="text-sm text-slate-500">Mật khẩu mới sẽ thay thế mật khẩu hiện tại. Cung cấp mật khẩu mới trực tiếp cho chủ tài khoản.</p>
      {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      <fieldset disabled={busy} className="space-y-4 disabled:opacity-70">
        <label className="block space-y-2 text-sm font-semibold">Mật khẩu mới
          <span className="relative block"><input name="new_password" autoFocus required minLength={6} maxLength={72} type={visible ? 'text' : 'password'} autoComplete="new-password" className="w-full rounded-xl border border-slate-200 px-3 py-2.5 pr-12 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" />
            <button type="button" aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} onClick={() => setVisible(value => !value)} className="absolute right-3 top-3 text-slate-500">{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button>
          </span>
        </label>
        <label className="block space-y-2 text-sm font-semibold">Xác nhận mật khẩu mới<input name="confirm_password" required minLength={6} maxLength={72} type={visible ? 'text' : 'password'} autoComplete="new-password" className="block w-full rounded-xl border border-slate-200 px-3 py-2.5 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" /></label>
        <p className="text-xs text-slate-500">Tối thiểu 6 ký tự, tối đa 72 byte UTF-8.</p>
      </fieldset>
      {!account.is_active && <p className="text-sm text-amber-700">Tài khoản đang khóa. Đặt lại mật khẩu không mở khóa tài khoản.</p>}
      <div className="flex justify-end gap-3 border-t border-slate-200 pt-4">
        <button type="button" disabled={busy} onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold disabled:opacity-50">Hủy</button>
        <button disabled={busy} className="flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50">{busy && <Loader2 size={16} className="animate-spin" />}{busy ? 'Đang đặt lại…' : 'Xác nhận đặt lại'}</button>
      </div>
    </form>
  </dialog>;
}
