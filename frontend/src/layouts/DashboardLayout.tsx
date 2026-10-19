import { useState } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/common/Sidebar';
import { Header } from '../components/common/Header';
import { MobileBottomNavigation } from '../components/common/MobileBottomNavigation';
import { PilotFeedbackModal } from '../components/common/PilotFeedbackModal';
import { useAuth } from '../hooks';
import { isApiMode } from '../services/apiClient';

export const DashboardLayout: React.FC = () => {
  const { currentUser, isLoading } = useAuth();
  const location = useLocation();
  const [showFeedback, setShowFeedback] = useState(false);

  if (isApiMode()) {
    if (isLoading) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[#F8FAF9]">
          <div className="text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#16866A] border-t-transparent mx-auto" />
            <p className="mt-3 text-xs font-semibold text-[#64748B]">Verifying session...</p>
          </div>
        </div>
      );
    }

    if (!currentUser.id) {
      return <Navigate to="/login" state={{ from: location }} replace />;
    }
  }

  return (
    <div className="flex min-h-screen bg-[#F8FAF9]">
      {/* Desktop & Tablet Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main className="flex-1 p-4 md:p-6 lg:p-8 pb-20 lg:pb-8">
          <Outlet />
        </main>
        {/* Mobile Bottom Navigation */}
        <MobileBottomNavigation />
      </div>

      {/* Floating Pilot Feedback Button */}
      <button
        onClick={() => setShowFeedback(true)}
        title="Submit Pilot Feedback"
        className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-[#16866A] text-white shadow-lg hover:bg-[#09664F] transition-all hover:scale-110 cursor-pointer lg:bottom-8 lg:right-8"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>

      {/* Pilot Feedback Modal */}
      <PilotFeedbackModal isOpen={showFeedback} onClose={() => setShowFeedback(false)} />
    </div>
  );
};

