import { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/common/Sidebar';
import { Header } from '../components/common/Header';
import { MobileBottomNavigation } from '../components/common/MobileBottomNavigation';
import { PilotFeedbackModal } from '../components/common/PilotFeedbackModal';
import { useLocation } from 'react-router-dom';

const COLLAPSE_KEY = 'nn-sidebar-collapsed';

export const AppShell: React.FC = () => {
  const location = useLocation();
  const isAdminWorkspace = location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator');
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(COLLAPSE_KEY) === '1';
    } catch {
      return false;
    }
  });
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0');
    } catch {
      /* ignore */
    }
  }, [collapsed]);

  return (
    <div className="flex min-h-screen bg-[#F8FAF9] overflow-x-hidden">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} isAdminWorkspace={isAdminWorkspace} />

      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main className="flex-1 p-4 md:p-6 pb-20 lg:pb-6 w-full">
          <Outlet />
        </main>
        <MobileBottomNavigation />
      </div>

      <button
        type="button"
        onClick={() => setShowFeedback(true)}
        title="Submit pilot feedback"
        className="fixed bottom-20 right-4 z-30 flex h-10 w-10 items-center justify-center rounded-full bg-[#16866A] text-white shadow-md hover:bg-[#09664F] lg:bottom-6 lg:right-6"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>

      <PilotFeedbackModal isOpen={showFeedback} onClose={() => setShowFeedback(false)} />
    </div>
  );
};
