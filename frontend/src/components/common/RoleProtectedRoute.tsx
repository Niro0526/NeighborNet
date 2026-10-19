import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../../hooks';
import { UserRole } from '../../types';
import { AlertTriangle, ArrowLeft } from 'lucide-react';

interface Props {
  requiredRole: UserRole;
  title?: string;
}

export const RoleProtectedRoute: React.FC<Props> = ({ requiredRole, title }) => {
  const { currentUser, hasRole, assignedRoles } = useAuth();

  // Coordinator can view, or user with requiredRole
  const isApproved = hasRole(requiredRole) || hasRole('COORDINATOR');

  if (!isApproved) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 mb-4 shadow-xs">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h2 className="text-lg font-bold text-[#182B25]">{title || 'Role Permission Required'}</h2>
        <p className="mt-1 text-xs text-[#64748B] max-w-md">
          This section requires the <strong>{requiredRole.replace('_', ' ')}</strong> permission. Your account ({currentUser.name}) does not have this approved role.
        </p>
        <div className="mt-2 text-[11px] text-[#64748B]">
          Your approved roles: {assignedRoles.map((r) => r.replace('_', ' ')).join(', ')}
        </div>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] transition-all"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Return to Personal Dashboard</span>
        </Link>
      </div>
    );
  }

  return <Outlet />;
};
