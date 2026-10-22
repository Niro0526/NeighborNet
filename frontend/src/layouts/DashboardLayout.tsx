import { Navigate, useLocation } from 'react-router-dom';
import { AppShell } from './AppShell';
import { useAuth } from '../hooks';
import { isApiMode } from '../services/apiClient';

export const DashboardLayout: React.FC = () => {
  const { currentUser, isLoading } = useAuth();
  const location = useLocation();

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

  return <AppShell />;
};
