import React, { useEffect } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../../hooks';
import { UserRole } from '../../types';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface Props {
  requiredRole: UserRole;
}

export const WorkspaceProtectedRoute: React.FC<Props> = ({ requiredRole }) => {
  const { currentUser, assignedRoles, activeRole, switchRole } = useAuth();

  const isApproved = assignedRoles.includes(requiredRole);

  useEffect(() => {
    if (isApproved && activeRole !== requiredRole) {
      switchRole?.(requiredRole).catch(() => {});
    }
  }, [isApproved, activeRole, requiredRole, switchRole]);

  if (!isApproved) {
    const fallbackPath =
      activeRole === 'FOOD_PROVIDER'
        ? '/provider/dashboard'
        : activeRole === 'RECIPIENT'
        ? '/recipient/dashboard'
        : activeRole === 'VOLUNTEER'
        ? '/volunteer/dashboard'
        : '/coordinator/dashboard';

    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-red-600 mb-4">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h2 className="text-lg font-bold text-[#182B25]">Workspace Access Restricted</h2>
        <p className="mt-1 text-xs text-[#64748B] max-w-md">
          Your account ({currentUser.name}) is not approved for the{' '}
          <span className="font-semibold text-[#182B25]">{requiredRole.replace('_', ' ')}</span> role.
        </p>
        <div className="mt-2 text-[11px] text-[#64748B]">
          Your approved roles: {assignedRoles.map((r) => r.replace('_', ' ')).join(', ')}
        </div>
        <Link
          to={fallbackPath}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] transition-all"
        >
          <span>Return to Your {activeRole.replace('_', ' ')} Workspace</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    );
  }

  return <Outlet />;
};
