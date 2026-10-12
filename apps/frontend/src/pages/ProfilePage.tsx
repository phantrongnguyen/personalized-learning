import React, { useEffect, useState } from 'react';
import { RoleCode } from '@shared/types';
import { NavigationPage, useApp } from '../state/AppContext';
import { mapBackendUser, updateProfileApi } from '../services/api';
import { ArrowRight, LogIn, Mail, Save, ShieldCheck, User } from 'lucide-react';

const roles: Record<RoleCode, { label: string; description: string; workspace: string; page: NavigationPage; tasks: string[] }> = {
  ADMIN: { label: 'Quản trị viên', description: 'Thông tin cá nhân và không gian quản lý tài khoản của hệ thống.', workspace: 'Quản lý tài khoản', page: 'admin-users', tasks: ['Cấp tài khoản sinh viên, giảng viên và cố vấn.', 'Tra cứu tài khoản và quản lý trạng thái hoạt động.'] },
  ADVISOR: { label: 'Cố vấn học tập', description: 'Thông tin công tác và không gian hỗ trợ sinh viên được phân công.', workspace: 'Không gian cố vấn', page: 'advisor', tasks: ['Theo dõi lớp và tình hình học tập của sinh viên.', 'Lập kế hoạch hỗ trợ và theo dõi tiến độ can thiệp.'] },
  LECTURER: { label: 'Giảng viên', description: 'Thông tin giảng dạy và các học phần phụ trách.', workspace: 'Không gian giảng viên', page: 'lecturer', tasks: ['Theo dõi học phần và sinh viên trong học phần.', 'Giao nhiệm vụ học tập và hỗ trợ sinh viên.'] },
  STUDENT: { label: 'Sinh viên', description: 'Thông tin cá nhân và hành trình học tập của bạn.', workspace: 'Không gian học tập', page: 'student', tasks: ['Xem học phần, nhiệm vụ và tiến độ học tập cá nhân.', 'Theo dõi gợi ý học tập và gửi yêu cầu hỗ trợ.'] },
};

const Detail = ({ label, value }: { label: string; value?: string }) => (
  <div className="py-3 border-b border-slate-100 last:border-0"><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 font-medium text-slate-800 break-words">{value || 'Chưa cập nhật'}</dd></div>
);

export const ProfilePage: React.FC = () => {
  const { user, logout, updateUser, addToast, apiBase, setCurrentView, setIsAuthModalOpen } = useApp();
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    setName(user?.name || ''); setPhone(user?.phone || ''); setError('');
  }, [user?.email, user?.name, user?.phone]);

  if (!user) return (
    <section className="max-w-xl mx-auto rounded-2xl border border-slate-200 bg-white p-10 text-center">
      <User className="mx-auto h-12 w-12 text-brand-600" /><h1 className="mt-4 text-2xl font-bold text-slate-900">Hồ sơ cá nhân</h1>
      <p className="mt-3 text-slate-500">Đăng nhập để xem và cập nhật hồ sơ của bạn.</p>
      <button onClick={() => setIsAuthModalOpen(true)} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-white font-semibold"><LogIn size={18} /> Đăng nhập</button>
    </section>
  );
  const content = user.roleCode ? roles[user.roleCode] : undefined;
  const changed = name.trim() !== user.name || phone.trim() !== (user.phone || '');
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving || !changed) return;
    if (!name.trim()) { setError('Vui lòng nhập họ và tên.'); return; }
    setSaving(true); setError('');
    try {
      const result = await updateProfileApi(apiBase, { full_name: name.trim(), phone_number: phone.trim() });
      updateUser(mapBackendUser(result));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Không thể cập nhật hồ sơ. Vui lòng thử lại.';
      setError(message); addToast(message, 'error');
    } finally { setSaving(false); }
  };
  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-8">
      <header><p className="text-sm font-semibold text-brand-600">TÀI KHOẢN CỦA BẠN</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Hồ sơ {content?.label.toLocaleLowerCase('vi') || 'cá nhân'}</h1><p className="mt-2 text-slate-500">{content?.description || 'Xem và cập nhật thông tin cá nhân của bạn.'}</p></header>
      <section className="rounded-2xl border border-brand-100 bg-white p-6 sm:p-8 flex flex-col sm:flex-row gap-5 sm:items-center">
        <div className="h-20 w-20 shrink-0 rounded-2xl bg-brand-100 text-brand-700 flex items-center justify-center text-2xl font-bold">{user.initials}</div>
        <div className="flex-1 min-w-0"><span className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">{content?.label || user.role}</span><h2 className="mt-2 text-2xl font-bold text-slate-900 break-words">{user.name}</h2><p className="mt-2 flex items-center gap-2 text-sm text-slate-500 break-all"><Mail size={16} className="shrink-0" /> {user.email}</p></div>
        <button onClick={logout} className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">Đăng xuất</button>
      </section>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
          <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900"><User size={21} className="text-brand-600" /> Thông tin cá nhân</h2><p className="mt-2 text-sm text-slate-500">Cập nhật tên hiển thị và thông tin liên hệ của bạn.</p>
          <form onSubmit={save} className="mt-6 space-y-5">
            <div><label htmlFor="profile-name" className="block text-sm font-medium text-slate-700 mb-2">Họ và tên</label><input id="profile-name" value={name} onChange={e => setName(e.target.value)} required disabled={saving} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900" autoComplete="name" /></div>
            <div><label htmlFor="profile-phone" className="block text-sm font-medium text-slate-700 mb-2">Số điện thoại</label><input id="profile-phone" type="tel" value={phone} onChange={e => setPhone(e.target.value)} disabled={saving} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900" placeholder="Chưa cập nhật" autoComplete="tel" /></div>
            <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-500">Email, vai trò và mã tài khoản do hệ thống quản lý. Liên hệ quản trị viên nếu cần điều chỉnh.</div>
            {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
            <button type="submit" disabled={saving || !changed} className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed"><Save size={18} /> {saving ? 'Đang lưu…' : 'Lưu thay đổi'}</button>
          </form>
        </section>
        <aside className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="flex items-center gap-2 font-bold text-slate-900"><ShieldCheck size={20} className="text-brand-600" /> Thông tin tài khoản</h2><dl className="mt-3">
            <Detail label="Email đăng nhập" value={user.email} /><Detail label="Vai trò" value={content?.label || user.role} />
            {user.roleCode === 'STUDENT' && <Detail label="Mã sinh viên" value={user.studentCode} />}
            {user.roleCode === 'LECTURER' && <><Detail label="Mã giảng viên" value={user.lecturerCode} /><Detail label="Học hàm / học vị" value={user.academicRank} /></>}
            {user.roleCode !== 'STUDENT' && <Detail label="Khoa / đơn vị" value={user.department} />}
            {user.roleCode === 'ADVISOR' && <Detail label="Phòng làm việc" value={user.officeLocation} />}
            <Detail label="Trường" value={user.organization} />
          </dl></section>
          {content && <section className="rounded-2xl border border-brand-100 bg-brand-50 p-6"><h2 className="font-bold text-brand-800">{content.workspace}</h2><ul className="mt-4 space-y-3 text-sm text-slate-600 list-disc pl-4">{content.tasks.map(task => <li key={task}>{task}</li>)}</ul><button onClick={() => setCurrentView(content.page)} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-brand-700 hover:underline">Mở không gian làm việc <ArrowRight size={16} /></button></section>}
        </aside>
      </div>
    </div>
  );
};
