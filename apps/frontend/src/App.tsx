import React, { useState } from 'react';
import { AppProvider, useApp } from './state/AppContext';
import { Sidebar } from './components/common/Sidebar';
import { Navbar } from './components/common/Navbar';
import { Footer } from './components/common/Footer';
import { ToastContainer } from './components/common/ToastContainer';
import { AuthModal } from './components/common/AuthModal';

import { AuthPage } from './pages/AuthPage';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';
import { ProfilePage } from './pages/ProfilePage';
import { AdvisorPage } from './pages/AdvisorPage';
import { LecturerPage } from './pages/LecturerPage';
import { StudentPage } from './pages/StudentPage';
import { AdminUsersPage } from './pages/AdminUsersPage';

const AppContent: React.FC = () => {
  const { currentView, user } = useApp();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      return localStorage.getItem('edurisk_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  // If user is not authenticated, display the Auth Portal first before entering home page
  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <AuthPage />
        <ToastContainer />
      </div>
    );
  }

  const toggleCollapsed = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('edurisk_sidebar_collapsed', String(next));
      } catch {
        // Ignore
      }
      return next;
    });
  };

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Persistent / Responsive Left Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
        isCollapsed={isCollapsed}
        setIsCollapsed={toggleCollapsed}
      />

      {/* Main Content Area (offset by left sidebar width on desktop) */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out ${
          isCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        }`}
      >
        {/* Top Header */}
        <Navbar
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isCollapsed={isCollapsed}
          onToggleCollapse={toggleCollapsed}
        />

        {/* View Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {currentView === 'dashboard' && <DashboardPage />}
          {currentView === 'profile' && <ProfilePage />}
          {currentView === 'home' && <HomePage />}
          {currentView === 'about' && <AboutPage />}
          {currentView === 'contact' && <ContactPage />}
          {currentView === 'advisor' && <AdvisorPage />}
          {currentView === 'lecturer' && <LecturerPage />}
          {currentView === 'student' && <StudentPage />}
          {currentView === 'admin-users' && <AdminUsersPage />}
        </main>

        {/* Enterprise Footer */}
        <Footer />
      </div>

      {/* Global Modals & Notifications */}
      <ToastContainer />
      <AuthModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;
