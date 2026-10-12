import React from 'react';
import { useApp, NavigationPage } from '../../state/AppContext';
import { BrandLogo } from './BrandLogo';
import {
  LayoutDashboard,
  User,
  Home,
  Layers,
  PhoneCall,
  GraduationCap,
  ChevronLeft,
  ChevronRight,
  LogOut,
  LogIn,
  ShieldCheck,
  X,
  UserCheck,
  BookOpen,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  setIsOpen,
  isCollapsed,
  setIsCollapsed,
}) => {
  const {
    currentView,
    setCurrentView,
    user,
    logout,
    setIsAuthModalOpen,
  } = useApp();

  const handleNavClick = (view: NavigationPage) => {
    setCurrentView(view);
    setIsOpen(false);
  };

  // Main workspace pages (Profile & Dashboard prioritized on the left)
  const primaryNavItems: {
    id: NavigationPage;
    label: string;
    icon: React.ReactNode;
    badge?: string;
  }[] = (() => {
    const roleItems: {
      id: NavigationPage;
      label: string;
      icon: React.ReactNode;
      badge?: string;
    }[] = [];
    if (user?.roleCode === 'ADMIN') {
      roleItems.push({
        id: 'admin-users',
        label: 'Quản lý tài khoản',
        icon: <ShieldCheck className="w-5 h-5 shrink-0" />,
        badge: 'ADMIN',
      });
    }
    if (user?.roleCode === 'ADVISOR') {
      roleItems.push({
        id: 'advisor',
        label: 'Quản lý lớp chủ nhiệm',
        icon: <UserCheck className="w-5 h-5 shrink-0" />,
        badge: 'GVCN',
      });
    }
    if (user?.roleCode === 'LECTURER') {
      roleItems.push({
        id: 'lecturer',
        label: 'Lớp học phần phụ trách',
        icon: <BookOpen className="w-5 h-5 shrink-0" />,
        badge: 'GVBM',
      });
    }
    if (user?.roleCode === 'STUDENT') {
      roleItems.push({
        id: 'student',
        label: 'Dự báo & nhiệm vụ học tập',
        icon: <GraduationCap className="w-5 h-5 shrink-0" />,
        badge: 'SV',
      });
    }
    return [
      ...roleItems,
      {
        id: 'dashboard',
        label: 'Dashboard Phân tích',
        icon: <LayoutDashboard className="w-5 h-5 shrink-0" />,
        badge: 'Live AI',
      },
      {
        id: 'profile',
        label: 'Hồ sơ cá nhân',
        icon: <User className="w-5 h-5 shrink-0" />,
      },
    ];
  })();

  // Secondary platform pages
  const secondaryNavItems: {
    id: NavigationPage;
    label: string;
    icon: React.ReactNode;
  }[] = [
    {
      id: 'home',
      label: 'Trang chủ',
      icon: <Home className="w-5 h-5 shrink-0" />,
    },
    {
      id: 'about',
      label: 'Kiến trúc giải pháp',
      icon: <Layers className="w-5 h-5 shrink-0" />,
    },
    {
      id: 'contact',
      label: 'Liên hệ hợp tác',
      icon: <PhoneCall className="w-5 h-5 shrink-0" />,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop overlay */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-slate-900/95 border-r border-slate-800/80 backdrop-blur-xl transition-all duration-300 ease-in-out ${
          isCollapsed ? 'lg:w-20' : 'lg:w-64'
        } ${
          isOpen ? 'translate-x-0 w-72' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Sidebar Header (Brand Logo) */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
          <div
            onClick={() => handleNavClick('home')}
            className={`flex items-center gap-3 cursor-pointer group overflow-hidden ${
              isCollapsed ? 'lg:justify-center lg:w-full' : ''
            }`}
          >
            <BrandLogo
              compact={isCollapsed && !isOpen}
              className={isCollapsed && !isOpen ? '' : 'w-[190px] max-w-full'}
            />
          </div>

          {/* Mobile close button */}
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Menus (Scrollable) */}
        <div className="flex-1 py-4 px-3 space-y-6 overflow-y-auto">
          {/* Section 1: Main Workspace (Dashboard & Profile) */}
          <div className="space-y-1.5">
            {(!isCollapsed || isOpen) && (
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                Không gian làm việc
              </div>
            )}

            {primaryNavItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  title={item.label}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    active
                      ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  } ${isCollapsed && !isOpen ? 'lg:justify-center lg:px-2' : ''}`}
                >
                  <span className={active ? 'text-brand-400' : 'text-slate-400'}>
                    {item.icon}
                  </span>

                  {(!isCollapsed || isOpen) && (
                    <div className="flex-1 flex items-center justify-between text-left truncate">
                      <span className="truncate">{item.label}</span>
                      {item.badge && (
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full font-bold ${
                            active
                              ? 'bg-brand-500/30 text-brand-200'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Section 2: Platform & Support */}
          <div className="space-y-1.5 pt-2 border-t border-slate-800/60">
            {(!isCollapsed || isOpen) && (
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                Nền tảng &amp; Hỗ trợ
              </div>
            )}

            {secondaryNavItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  title={item.label}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    active
                      ? 'bg-slate-800 text-white border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  } ${isCollapsed && !isOpen ? 'lg:justify-center lg:px-2' : ''}`}
                >
                  <span className={active ? 'text-white' : 'text-slate-400'}>
                    {item.icon}
                  </span>

                  {(!isCollapsed || isOpen) && (
                    <span className="truncate text-left">{item.label}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Sidebar Bottom (User profile & Collapse toggle) */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 space-y-2.5">
          {/* User Profile Bar */}
          {user ? (
            <div
              className={`flex items-center gap-2.5 p-2 rounded-xl bg-slate-850/60 border border-slate-800 ${
                isCollapsed && !isOpen ? 'lg:justify-center' : ''
              }`}
            >
              <div
                onClick={() => handleNavClick('profile')}
                className="w-8 h-8 rounded-lg bg-brand-600/30 border border-brand-500/40 text-brand-300 font-bold text-xs flex items-center justify-center shrink-0 cursor-pointer hover:opacity-90"
                title="Nhấp để mở Hồ sơ chuyên gia"
              >
                {user.initials}
              </div>

              {(!isCollapsed || isOpen) && (
                <div
                  onClick={() => handleNavClick('profile')}
                  className="flex-1 min-w-0 cursor-pointer hover:opacity-90"
                >
                  <div className="text-xs font-semibold text-slate-200 truncate">{user.name}</div>
                  <div className="text-[10px] text-brand-400 truncate flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" />
                    <span>{user.role}</span>
                  </div>
                </div>
              )}

              {(!isCollapsed || isOpen) && (
                <button
                  type="button"
                  onClick={logout}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors shrink-0"
                  title="Đăng xuất"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setIsAuthModalOpen(true)}
              className={`w-full flex items-center gap-2 p-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-600/20 transition-all ${
                isCollapsed && !isOpen ? 'lg:justify-center' : 'justify-center'
              }`}
            >
              <LogIn className="w-4 h-4 shrink-0" />
              {(!isCollapsed || isOpen) && <span>Đăng nhập</span>}
            </button>
          )}

          {/* Desktop Collapse / Expand Toggle Button */}
          <div className="hidden lg:block pt-1">
            <button
              type="button"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="w-full flex items-center justify-center p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title={isCollapsed ? 'Mở rộng sidebar' : 'Thu gọn sidebar'}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <ChevronLeft className="w-4 h-4" />
                  <span>Thu gọn sidebar</span>
                </div>
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
