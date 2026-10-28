import React, { useEffect, useId, useRef, useState } from 'react';
import { ChevronDown, LayoutDashboard, LogOut, User } from 'lucide-react';
import { NavigationPage, useApp } from '../../state/AppContext';
import { Avatar } from './Avatar';

const workspaces = {
  ADMIN: { page: 'admin-users', label: 'Quản lý tài khoản' },
  ADVISOR: { page: 'advisor', label: 'Không gian cố vấn' },
  LECTURER: { page: 'lecturer', label: 'Lớp học phần phụ trách' },
  STUDENT: { page: 'student', label: 'Không gian học tập' },
} satisfies Record<string, { page: NavigationPage; label: string }>;

export const ProfileDropdown: React.FC = () => {
  const { user, currentView, setCurrentView, logout } = useApp();
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const focusLast = useRef(false);
  const id = useId();
  const workspace = user?.roleCode ? workspaces[user.roleCode] : undefined;

  useEffect(() => { setOpen(false); }, [currentView, user?.email]);

  useEffect(() => {
    if (!open) return;
    const items = menu.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]');
    const index = focusLast.current ? (items?.length || 1) - 1 : 0;
    items?.[index]?.focus();
    const onPointerDown = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [open]);

  if (!user) return null;

  const close = () => {
    setOpen(false);
    trigger.current?.focus();
  };

  const navigate = (page: NavigationPage) => {
    close();
    setCurrentView(page);
  };

  const onMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      close();
      return;
    }
    const items = Array.from(menu.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') || []);
    const index = items.indexOf(document.activeElement as HTMLButtonElement);
    let next: number;
    switch (event.key) {
      case 'ArrowDown': next = (index + 1) % items.length; break;
      case 'ArrowUp': next = (index - 1 + items.length) % items.length; break;
      case 'Home': next = 0; break;
      case 'End': next = items.length - 1; break;
      default: return;
    }
    event.preventDefault();
    items[next]?.focus();
  };

  return (
    <div ref={root} className="relative border-l border-slate-800 pl-2"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}>
      <button ref={trigger} type="button" id={`${id}-trigger`}
        aria-label={`Menu tài khoản ${user.name}`} aria-haspopup="menu"
        aria-expanded={open} aria-controls={open ? `${id}-menu` : undefined}
        onClick={() => { focusLast.current = false; setOpen(value => !value); }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            focusLast.current = event.key === 'ArrowUp';
            setOpen(true);
          } else if (event.key === 'Escape') close();
        }}
        className="inline-flex items-center gap-2 rounded-xl px-2 py-1.5 text-left text-slate-200 transition-colors hover:bg-slate-800">
        <Avatar src={user.avatarUrl} initials={user.initials} className="h-8 w-8 rounded-full border border-brand-500/40 text-xs" />
        <span className="hidden min-w-0 md:block">
          <span className="block text-[10px] text-brand-400">{user.role}</span>
        </span>
        <ChevronDown aria-hidden="true" className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-72 max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
          <div className="border-b border-slate-800 px-4 py-3">
            <p className="truncate text-sm font-semibold text-slate-100">{user.name}</p>
            <p className="mt-0.5 break-all text-xs text-slate-400">{user.email}</p>
            <p className="mt-2 text-xs font-medium text-brand-400">{user.role}</p>
          </div>
          <div ref={menu} id={`${id}-menu`} role="menu" aria-labelledby={`${id}-trigger`}
            onKeyDown={onMenuKeyDown} className="space-y-1 p-2">
            <button type="button" role="menuitem" tabIndex={-1} onClick={() => navigate('profile')}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-200 hover:bg-slate-800 focus:bg-slate-800">
              <User aria-hidden="true" className="h-4 w-4 text-slate-400" /> Hồ sơ cá nhân
            </button>
            {workspace && (
              <button type="button" role="menuitem" tabIndex={-1} onClick={() => navigate(workspace.page)}
                className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-200 hover:bg-slate-800 focus:bg-slate-800">
                <LayoutDashboard aria-hidden="true" className="h-4 w-4 text-slate-400" /> {workspace.label}
              </button>
            )}
            <div role="separator" className="my-1 border-t border-slate-800" />
            <button type="button" role="menuitem" tabIndex={-1} onClick={() => { close(); logout(); }}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-rose-400 hover:bg-rose-950/30 focus:bg-rose-950/30">
              <LogOut aria-hidden="true" className="h-4 w-4" /> Đăng xuất
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
