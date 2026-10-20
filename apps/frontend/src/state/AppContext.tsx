import { getSessionEpoch, historyStorageKey, SESSION_ENDED } from '../services/session';
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { PredictionHistoryItem, RoleCode, UserProfile } from '@shared/types';
import { applyTheme, getInitialTheme, THEME_KEY, Theme } from './theme';
import {
  checkBackendHealth,
  getCurrentUserApi,
  mapBackendUser,
  clearStoredTokens,
} from '../services/api';

export type NavigationPage =
  | 'home'
  | 'dashboard'
  | 'about'
  | 'contact'
  | 'profile'
  | 'admin-users'
  | 'advisor'
  | 'lecturer'
  | 'student';

const VALID_NAV_PAGES: NavigationPage[] = [
  'home',
  'dashboard',
  'about',
  'contact',
  'profile',
  'admin-users',
  'advisor',
  'lecturer',
  'student',
];

function defaultViewForRole(roleCode?: RoleCode): NavigationPage {
  switch (roleCode) {
    case 'ADVISOR':
      return 'advisor';
    case 'LECTURER':
      return 'lecturer';
    case 'STUDENT':
      return 'student';
    case 'ADMIN':
      return 'admin-users';
    default:
      return 'home';
  }
}
export type BackendStatus = 'checking' | 'ok' | 'down';
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
}

interface AppContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  currentView: NavigationPage;
  setCurrentView: (view: NavigationPage) => void;
  studentEnrollmentToOpen: string | null;
  openStudentEnrollment: (enrollmentId: string) => void;
  clearStudentEnrollmentToOpen: () => void;
  apiBase: string;
  setApiBase: (url: string) => void;
  backendStatus: BackendStatus;
  modelLoaded: boolean | null;
  latency: number | null;
  user: UserProfile | null;
  login: (user: UserProfile) => void;
  logout: () => void;
  updateUser: (updated: Partial<UserProfile>) => void;
  refreshUser: () => Promise<UserProfile | null>;
  history: PredictionHistoryItem[];
  addHistory: (item: PredictionHistoryItem) => void;
  removeHistoryItem: (id: string) => void;
  clearHistory: () => void;
  toasts: ToastItem[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
  refreshHealth: () => Promise<void>;
  isAuthModalOpen: boolean;
  setIsAuthModalOpen: (open: boolean) => void;
  isBackendModalOpen: boolean;
  setIsBackendModalOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

const API_BASE_KEY = 'edurisk_api_base';
const USER_KEY = 'edurisk_current_user';

function getDefaultApiBase(): string {
  if (typeof window !== 'undefined' && window.location.origin.startsWith('http')) {
    // If running on Vite dev server (port 5173), point to default FastAPI port 8000
    if (window.location.port === '5173') {
      return 'http://127.0.0.1:8000';
    }
    return window.location.origin;
  }
  return 'http://127.0.0.1:8000';
}

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  const setTheme = useCallback((next: Theme) => {
    applyTheme(next);
    setThemeState(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // Switching still works when browser storage is unavailable.
    }
  }, []);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const syncTheme = (event: StorageEvent) => {
      if (event.storageArea === localStorage && (event.key === THEME_KEY || event.key === null)) {
        const next = event.newValue === 'dark' && event.key === THEME_KEY ? 'dark' : 'light';
        applyTheme(next);
        setThemeState(next);
      }
    };
    window.addEventListener('storage', syncTheme);
    return () => window.removeEventListener('storage', syncTheme);
  }, []);
  const [currentView, setCurrentViewState] = useState<NavigationPage>('home');
  const [studentEnrollmentToOpen, setStudentEnrollmentToOpen] = useState<string | null>(null);
  const clearStudentEnrollmentToOpen = useCallback(() => setStudentEnrollmentToOpen(null), []);
  const [apiBase, setApiBaseState] = useState<string>(() => {
    return localStorage.getItem(API_BASE_KEY) || getDefaultApiBase();
  });
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking');
  const [modelLoaded, setModelLoaded] = useState<boolean | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  // Restore identity only after /me confirms it; never display the last account's cached data.
  const [user, setUser] = useState<UserProfile | null>(null);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const historyKey = historyStorageKey(apiBase, user?.userId);
  const restoreHistory = (profile: UserProfile) => {
    const key = historyStorageKey(apiBase, profile.userId);
    try {
      const stored = key ? JSON.parse(localStorage.getItem(key) || '[]') : [];
      setHistory(Array.isArray(stored) ? stored : []);
    } catch { setHistory([]); }
  };
  useEffect(() => {
    const end = () => {
      setUser(null); setHistory([]); setStudentEnrollmentToOpen(null);
      localStorage.removeItem(USER_KEY);
    };
    const sync = (event: StorageEvent) => {
      if (event.key === 'edurisk_jwt_access_token' || event.key === null) end();
    };
    window.addEventListener(SESSION_ENDED, end);
    window.addEventListener('storage', sync);
    return () => { window.removeEventListener(SESSION_ENDED, end); window.removeEventListener('storage', sync); };
  }, []);

  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isBackendModalOpen, setIsBackendModalOpen] = useState(false);

  // Sync hash routing
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '') as NavigationPage;
      if (VALID_NAV_PAGES.includes(hash)) {
        setCurrentViewState(hash);
      } else {
        setCurrentViewState('home');
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const setCurrentView = (view: NavigationPage) => {
    window.location.hash = view;
    setCurrentViewState(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const openStudentEnrollment = (enrollmentId: string) => {
    setStudentEnrollmentToOpen(enrollmentId);
    setCurrentView('student');
  };

  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 3500) => {
    const id = Math.random().toString(36).slice(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const setApiBase = (url: string) => {
    const clean = url.trim().replace(/\/+$/, '');
    clearStoredTokens();
    setApiBaseState(clean);
    localStorage.setItem(API_BASE_KEY, clean);
    addToast(`Đã cập nhật máy chủ API: ${clean}`, 'info');
  };

  const refreshHealth = useCallback(async () => {
    setBackendStatus('checking');
    try {
      const { data, latency } = await checkBackendHealth(apiBase);
      setLatency(latency);
      if (data.status === 'ok') {
        setBackendStatus('ok');
        setModelLoaded(Boolean(data.model_loaded));
      } else {
        setBackendStatus('down');
        setModelLoaded(false);
      }
    } catch {
      setBackendStatus('down');
      setModelLoaded(false);
      setLatency(null);
    }
  }, [apiBase]);

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, [refreshHealth]);

  const login = (newUser: UserProfile) => {
    setHistory([]);
    restoreHistory(newUser);
    setUser(newUser);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setIsAuthModalOpen(false);
    addToast(`Chào mừng ${newUser.name} (${newUser.role})!`, 'success');

    // Điều hướng tới không gian làm việc phù hợp với vai trò
    setCurrentViewState(defaultViewForRole(newUser.roleCode));
  };

  const logout = () => {
    setStudentEnrollmentToOpen(null);
    setUser(null);
    setHistory([]);
    localStorage.removeItem(USER_KEY);
    clearStoredTokens();
    setCurrentViewState('home');
    addToast('Bạn đã đăng xuất khỏi hệ thống.', 'info');
  };

  const refreshUser = useCallback(async (): Promise<UserProfile | null> => {
    const epoch = getSessionEpoch();
    const backendUser = await getCurrentUserApi(apiBase);
    if (epoch !== getSessionEpoch()) return null;
    if (backendUser) {
      const mapped = mapBackendUser(backendUser);
      restoreHistory(mapped);
      setUser(mapped);
      localStorage.setItem(USER_KEY, JSON.stringify(mapped));
      return mapped;
    }
    setUser(null);
    setHistory([]);
    return null;
  }, [apiBase]);

  useEffect(() => {
    // Khôi phục phiên đăng nhập từ token đã lưu (nếu có)
    refreshUser();
  }, [refreshUser]);

  const updateUser = (updated: Partial<UserProfile>) => {
    if (!user) return;
    const next: UserProfile = { ...user, ...updated };
    setUser(next);
    localStorage.setItem(USER_KEY, JSON.stringify(next));
    addToast('Đã lưu thông tin hồ sơ thành công!', 'success');
  };

  const addHistory = (item: PredictionHistoryItem) => {
    if (!historyKey) return;
    setHistory((prev) => {
      const next = [item, ...prev].slice(0, 50);
      localStorage.setItem(historyKey, JSON.stringify(next));
      return next;
    });
  };

  const removeHistoryItem = (id: string) => {
    if (!historyKey) return;
    setHistory((prev) => {
      const next = prev.filter((h) => h.id !== id);
      localStorage.setItem(historyKey, JSON.stringify(next));
      return next;
    });
    addToast('Đã xóa 1 bản ghi lịch sử.', 'info');
  };

  const clearHistory = () => {
    setHistory([]);
    if (historyKey) localStorage.removeItem(historyKey);
    addToast('Đã dọn sạch toàn bộ lịch sử dự đoán.', 'info');
  };

  return (
    <AppContext.Provider
      value={{
        theme,
        setTheme,
        currentView,
        setCurrentView,
        studentEnrollmentToOpen,
        openStudentEnrollment,
        clearStudentEnrollmentToOpen,
        apiBase,
        setApiBase,
        backendStatus,
        modelLoaded,
        latency,
        user,
        login,
        logout,
        updateUser,
        refreshUser,
        history,
        addHistory,
        removeHistoryItem,
        clearHistory,
        toasts,
        addToast,
        removeToast,
        refreshHealth,
        isAuthModalOpen,
        setIsAuthModalOpen,
        isBackendModalOpen,
        setIsBackendModalOpen,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};
