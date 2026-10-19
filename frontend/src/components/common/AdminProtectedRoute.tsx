import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../../hooks';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const AdminProtectedRoute: React.FC = () => {
  const { currentUser, hasRole, assignedRoles } = useAuth();

  const isCoordinator = hasRole('COORDINATOR');

  if (!isCoordinator) {
    return (
      <div className="flex min-h-[65vh] flex-col items-center justify-center p-6 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-100 text-purple-700 mb-4 shadow-xs">
          <ShieldAlert className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-black text-[#182B25]">Coordinator Authorization Required</h2>
        <p className="mt-2 text-xs text-[#64748B] max-w-md leading-relaxed">
          The Administration Workspace is strictly restricted to designated Disaster Coordinators and Incident Commanders. Your account (<strong>{currentUser.name}</strong>) is not granted Coordinator authority.
        </p>
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-700">
          <span>Your Approved Roles: {assignedRoles.join(', ')}</span>
        </div>
        <div className="mt-6">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-[#16866A] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#09664F] transition-all shadow-xs"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Return to Personal Dashboard</span>
          </Link>
        </div>
      </div>
    );
  }

  return <Outlet />;
};
