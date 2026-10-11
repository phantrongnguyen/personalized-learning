import React from 'react';
import { useApp } from '../../state/AppContext';
import {
  Menu,
  ChevronRight,
  Activity,
  LogIn,
  LogOut,
  LayoutDashboard,
  User,
  Home,
  Layers,
  PhoneCall,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

interface NavbarProps {
  onToggleSidebar: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onToggleSidebar,
  isCollapsed,
  onToggleCollapse,
}) => {
  const {
    currentView,
    setCurrentView,
    backendStatus,
    latency,
    user,
    logout,
    setIsAuthModalOpen,
    setIsBackendModalOpen,
  } = useApp();

  const getViewInfo = () => {
    switch (currentView) {
      case 'dashboard':
        return {
          title: 'Dashboard Phân tích Nguy cơ',
          subtitle: 'Mô hình LightGBM Cutoff 75%',
          icon: <LayoutDashboard className="w-4 h-4 text-emerald-400" />,
        };
      case 'profile':
        return {
          title: 'Hồ sơ Chuyên gia & Cài đặt',
          subtitle: 'Phân quyền & Tích hợp LMS LTI 1.3',
          icon: <User className="w-4 h-4 text-emerald-400" />,
        };
      case 'about':
        return {
          title: 'Kiến trúc Giải pháp Cốt lõi',
          subtitle: 'Thuật toán lai HCO-VNLS',
          icon: <Layers className="w-4 h-4 text-cyan-400" />,
        };
      case 'contact':
        return {
          title: 'Liên hệ Hợp tác Doanh nghiệp',
          subtitle: 'Tư vấn triển khai & Hỗ trợ kỹ thuật',
          icon: <PhoneCall className="w-4 h-4 text-purple-400" />,
        };
      default:
        return {
          title: 'EduRisk AI Enterprise Platform',
          subtitle: 'Quản trị rủi ro học tập & Can thiệp cá nhân hóa',
          icon: <Home className="w-4 h-4 text-emerald-400" />,
        };
    }
  };

  const currentInfo = getViewInfo();

  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center justify-between gap-2 h-16">
          {/* Left: Sidebar Toggles & Breadcrumb */}
          <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
            {/* Mobile Hamburger Drawer Toggle */}
            <button
              type="button"
              onClick={onToggleSidebar}
              className="shrink-0 p-2 rounded-xl text-slate-400 hover:text-foreground hover:bg-slate-850 lg:hidden border border-slate-800"
              title="Mở menu điều hướng"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Desktop Collapse/Expand Toggle */}
            <button
              type="button"
              onClick={onToggleCollapse}
              className="hidden lg:flex p-2 rounded-xl text-slate-400 hover:text-foreground hover:bg-slate-850 border border-slate-800 transition-colors"
              title={isCollapsed ? 'Mở rộng thanh sidebar' : 'Thu gọn thanh sidebar'}
            >
              {isCollapsed ? (
                <PanelLeftOpen className="w-4 h-4 text-emerald-400" />
              ) : (
                <PanelLeftClose className="w-4 h-4" />
              )}
            </button>

            {/* Breadcrumb Path */}
            <div className="flex min-w-0 items-center gap-2 text-xs">
              <span
                onClick={() => setCurrentView('home')}
                className="text-slate-400 hover:text-slate-200 cursor-pointer hidden sm:inline"
              >
                EduRisk Platform
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600 hidden sm:inline" />
              <div className="flex min-w-0 items-center gap-1.5 font-semibold text-slate-100">
                {currentInfo.icon}
                <span className="text-sm font-bold truncate">{currentInfo.title}</span>
              </div>
            </div>
          </div>

          {/* Right: Actions (API Status, User Profile) */}
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            {/* Backend status pill */}
            <button
              type="button"
              onClick={() => setIsBackendModalOpen(true)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono font-medium border transition-colors ${
                backendStatus === 'ok'
                  ? 'border-emerald-500/30 bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/40'
                  : backendStatus === 'checking'
                  ? 'border-amber-500/30 bg-amber-950/40 text-amber-300 hover:bg-amber-900/40'
                  : 'border-rose-500/30 bg-rose-950/40 text-rose-300 hover:bg-rose-900/40'
              }`}
              title="Nhấp để cấu hình và kiểm tra kết nối API"
            >
              <span
                className={`w-2 h-2 rounded-full animate-pulse ${
                  backendStatus === 'ok'
                    ? 'bg-emerald-400'
                    : backendStatus === 'checking'
                    ? 'bg-amber-400'
                    : 'bg-rose-400'
                }`}
              />
              <span className="hidden sm:inline">
                {backendStatus === 'ok'
                  ? `API OK (${latency ?? 0}ms)`
                  : backendStatus === 'checking'
                  ? 'Đang ping API…'
                  : 'Mất kết nối API'}
              </span>
              <Activity className="w-3.5 h-3.5 sm:hidden" />
            </button>

            {/* Auth Profile / Login */}
            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
                <div
                  onClick={() => setCurrentView('profile')}
                  className="flex items-center gap-2 cursor-pointer hover:opacity-85 transition-opacity"
                  title="Nhấp để xem Hồ sơ chuyên gia"
                >
                  <div className="w-8 h-8 rounded-lg bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 font-bold text-xs flex items-center justify-center">
                    {user.initials}
                  </div>
                  <div className="text-left hidden md:block">
                    <div className="text-xs font-semibold text-slate-200">{user.name}</div>
                    <div className="text-[10px] text-emerald-400">{user.role}</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
                  title="Đăng xuất"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-emerald-600/20 transition-all"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Đăng nhập</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
