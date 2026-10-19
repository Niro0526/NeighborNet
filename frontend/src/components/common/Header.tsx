import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  Search,
  ShieldAlert,
  Leaf,
  ChevronDown,
  RotateCcw,
  User as UserIcon,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Users,
  HandHeart,
  LogOut,
  SlidersHorizontal,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
} from 'lucide-react';
import { useAuth, useOperational, useLivePolling } from '../../hooks';
import { UserRole } from '../../types';
import { notificationService } from '../../services/notificationService';
import { SystemNotification } from '../../types';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { isApiMode } from '../../services/apiClient';

export const Header: React.FC = () => {
  const { currentUser, assignedRoles, hasRole, allUsers, switchUser, logout, resetDemoData } = useAuth();
  const { isDisasterMode, setMode } = useOperational();
  const navigate = useNavigate();
  const location = useLocation();

  const isAdminWorkspace = location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator');

  const [notifications, setNotifications] = useState<SystemNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showDisasterConfirm, setShowDisasterConfirm] = useState(false);
  const [permissionAlert, setPermissionAlert] = useState<string | null>(null);

  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  const [unreadCount, setUnreadCount] = useState(0);

  const refreshNotifications = async () => {
    const [notifs, count] = await Promise.all([
      notificationService.getNotifications(currentUser.assignedRoles[0] || 'FOOD_PROVIDER', currentUser.id),
      notificationService.getUnreadCount(),
    ]);
    setNotifications(notifs);
    setUnreadCount(count);
  };

  useEffect(() => {
    refreshNotifications();
  }, [currentUser.id, currentUser.assignedRoles]);

  useLivePolling({
    fetcher: async () => {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    },
    intervalMs: 30000,
    enabled: true,
  });

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const roleLabels: Record<UserRole, { label: string; badge: string; icon: React.ComponentType<{ className?: string }> }> = {
    FOOD_PROVIDER: { label: 'Food Provider', badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Building2 },
    RECIPIENT: { label: 'NGO / Recipient', badge: 'bg-blue-50 text-blue-700 border-blue-200', icon: Users },
    VOLUNTEER: { label: 'Volunteer Courier', badge: 'bg-amber-50 text-amber-700 border-amber-200', icon: HandHeart },
    COORDINATOR: { label: 'Coordinator / Admin', badge: 'bg-purple-50 text-purple-700 border-purple-200', icon: ShieldAlert },
  };

  const handleModeToggle = () => {
    if (!hasRole('COORDINATOR')) {
      setPermissionAlert('Action restricted: Only approved Disaster Coordinators can activate or resolve emergency disaster modes.');
      return;
    }
    if (!isDisasterMode) {
      setShowDisasterConfirm(true);
    } else {
      setMode('NORMAL');
    }
  };

  const confirmDisasterActivation = () => {
    setMode('DISASTER');
    setShowDisasterConfirm(false);
  };

  const handleAccountSwitch = async (userId: string) => {
    await switchUser(userId);
    setShowProfileMenu(false);
    const target = allUsers.find((u) => u.id === userId);
    if (target) {
      // Coordinator-only goes to admin, otherwise unified dashboard
      if (target.assignedRoles.length === 1 && target.assignedRoles[0] === 'COORDINATOR') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-[#E5EAE7] bg-white px-4 md:px-6 shadow-xs">
        {/* Left: Search Bar & Workspace Context */}
        <div className="flex items-center gap-3 md:gap-4 flex-1 max-w-md">
          <div className="relative w-full hidden sm:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#64748B]" />
            <input
              type="text"
              placeholder="Search surplus listings, delivery tasks, shelters..."
              className="w-full rounded-xl border border-[#E5EAE7] bg-[#F8FAF9] py-1.5 pl-9 pr-4 text-xs md:text-sm text-[#182B25] placeholder-[#94A3B8] focus:border-[#16866A] focus:outline-none focus:ring-1 focus:ring-[#16866A]"
            />
          </div>
        </div>

        {/* Right Controls: Workspace Navigation, Operational Mode, Notifications, User Profile */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* Quick Workspace Switch for Coordinators */}
          {hasRole('COORDINATOR') && (
            <div className="hidden sm:block">
              {isAdminWorkspace ? (
                <Link
                  to="/dashboard"
                  className="flex items-center gap-1.5 rounded-xl border border-purple-200 bg-purple-50 px-3 py-1.5 text-xs font-bold text-purple-800 hover:bg-purple-100 transition-all shadow-2xs"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Personal Dashboard</span>
                </Link>
              ) : (
                <Link
                  to="/admin/dashboard"
                  className="flex items-center gap-1.5 rounded-xl bg-purple-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-purple-800 transition-all shadow-xs"
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Admin Workspace</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
            </div>
          )}

          {/* Operational Mode Indicator & Coordinator Trigger */}
          <div className="flex items-center bg-[#F8FAF9] p-1 rounded-xl border border-[#E5EAE7]">
            <button
              onClick={handleModeToggle}
              title={hasRole('COORDINATOR') ? 'Click to toggle Normal Mode' : 'Operational status: Normal Community Mode'}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                !isDisasterMode
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-[#64748B] hover:text-[#182B25]'
              }`}
            >
              <Leaf className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Normal Mode</span>
            </button>
            <button
              onClick={handleModeToggle}
              title={hasRole('COORDINATOR') ? 'Click to toggle Disaster Mode' : 'Operational status: Disaster Emergency Mode'}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                isDisasterMode
                  ? 'bg-red-600 text-white shadow-xs animate-pulse'
                  : 'text-[#64748B] hover:text-[#182B25]'
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Disaster Mode</span>
            </button>
          </div>

          {/* Notifications Dropdown */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[#E5EAE7] bg-white text-[#182B25] hover:bg-[#F8FAF9] shadow-2xs cursor-pointer"
            >
              <Bell className="h-4 w-4 text-[#64748B]" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[9px] font-bold text-white">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl border border-[#E5EAE7] bg-white p-3 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="flex items-center justify-between pb-2 border-b border-[#E5EAE7]">
                  <h4 className="text-xs font-bold text-[#182B25]">Platform Notifications</h4>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        notificationService.markAllAsRead();
                        setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
                        setUnreadCount(0);
                      }}
                      className="text-[11px] font-medium text-[#16866A] hover:underline"
                    >
                      Mark all read
                    </button>
                  </div>
                </div>
                <div className="max-h-72 overflow-y-auto divide-y divide-[#E5EAE7]">
                  {notifications.length === 0 ? (
                    <div className="py-6 text-center text-xs text-[#64748B]">No notifications right now</div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`py-2.5 px-1.5 transition-colors ${!n.read ? 'bg-emerald-50/40 rounded-lg' : ''}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs font-semibold text-[#182B25]">{n.title}</p>
                          <span className="text-[10px] text-[#64748B] whitespace-nowrap">
                            {new Date(n.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] text-[#64748B] leading-relaxed">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
                <div className="pt-2 border-t border-[#E5EAE7]">
                  <Link
                    to="/notifications"
                    onClick={() => setShowNotifications(false)}
                    className="block text-center text-xs font-bold text-[#16866A] hover:underline py-1.5"
                  >
                    View All Notifications
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-[#F8FAF9] border border-transparent hover:border-[#E5EAE7] transition-all cursor-pointer"
            >
              {currentUser.avatarUrl ? (
                <img
                  src={currentUser.avatarUrl}
                  alt={currentUser.name}
                  className="h-8 w-8 rounded-full object-cover ring-2 ring-[#16866A]/20"
                />
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#16866A] text-xs font-bold text-white">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
              <div className="hidden sm:block text-left">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-[#182B25] leading-tight">{currentUser.name}</span>
                  {assignedRoles.length > 1 && (
                    <span className="rounded-md bg-emerald-100 px-1 py-0.2 text-[9px] font-extrabold text-emerald-800">
                      Multi-Role
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-[#64748B]">
                  {assignedRoles.map((r) => roleLabels[r]?.label.replace(' / Admin', '').replace(' / Recipient', '')).join(' + ')}
                </p>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-[#64748B] ml-0.5" />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-[#E5EAE7] bg-white p-3 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                {/* User Identity Header */}
                <div className="pb-3 border-b border-[#E5EAE7]">
                  <div className="flex items-center gap-2.5">
                    {currentUser.avatarUrl ? (
                      <img
                        src={currentUser.avatarUrl}
                        alt={currentUser.name}
                        className="h-10 w-10 rounded-full object-cover ring-2 ring-[#16866A]/20"
                      />
                    ) : (
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#16866A] text-sm font-bold text-white">
                        <UserIcon className="h-5 w-5" />
                      </div>
                    )}
                    <div className="overflow-hidden">
                      <p className="text-xs font-bold text-[#182B25] truncate">{currentUser.name}</p>
                      <p className="text-[11px] text-[#64748B] truncate">{currentUser.email}</p>
                    </div>
                  </div>

                  {/* Approved roles badges */}
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {assignedRoles.map((role) => (
                      <span
                        key={role}
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${roleLabels[role].badge}`}
                      >
                        {roleLabels[role].label}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Coordinator Administration Access */}
                {hasRole('COORDINATOR') && (
                  <div className="py-2.5 border-b border-[#E5EAE7]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-purple-900">Coordinator Workspace:</span>
                      <Link
                        to={isAdminWorkspace ? '/dashboard' : '/admin/dashboard'}
                        onClick={() => setShowProfileMenu(false)}
                        className="text-xs font-bold text-purple-700 hover:text-purple-900 underline"
                      >
                        {isAdminWorkspace ? 'Go to Personal Dashboard' : 'Open Admin Workspace →'}
                      </Link>
                    </div>
                  </div>
                )}

                {/* Account Navigation */}
                <div className="py-2 border-b border-[#E5EAE7] space-y-1">
                  <Link
                    to="/profile"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-[#182B25] hover:bg-[#F8FAF9]"
                  >
                    <UserIcon className="h-3.5 w-3.5 text-[#64748B]" />
                    <span>My Profile & Organization</span>
                  </Link>
                  <Link
                    to="/settings"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-[#182B25] hover:bg-[#F8FAF9]"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 text-[#64748B]" />
                    <span>Preferences & Settings</span>
                  </Link>
                </div>

                {/* Persona Switcher / API Mode status */}
                <div className="py-2.5 border-b border-[#E5EAE7]">
                  <div className="flex items-center justify-between px-1 pb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#94A3B8]">
                      {isApiMode() ? 'Live PostgreSQL Session' : 'Dev Demo Personas'}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${isApiMode() ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                      {isApiMode() ? 'API Mode' : 'Mock Mode'}
                    </span>
                  </div>
                  {!isApiMode() && (
                    <div className="max-h-36 overflow-y-auto space-y-1 mt-1">
                      {allUsers.map((u) => (
                        <button
                          key={u.id}
                          onClick={() => handleAccountSwitch(u.id)}
                          className={`flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[11px] text-left transition-colors ${
                            u.id === currentUser.id
                              ? 'bg-[#F8FAF9] font-bold text-[#16866A]'
                              : 'text-[#182B25] hover:bg-[#F8FAF9]'
                          }`}
                        >
                          <div className="truncate">
                            <span>{u.name}</span>
                            <span className="text-[10px] text-[#64748B] block truncate">
                              {u.assignedRoles.map((r) => r.replace('_', ' ')).join(' + ')}
                            </span>
                          </div>
                          {u.id === currentUser.id && <CheckCircle2 className="h-3.5 w-3.5 text-[#16866A] shrink-0" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions & Utilities */}
                <div className="pt-2 space-y-1">
                  {!isApiMode() && (
                    <button
                      onClick={async () => {
                        await resetDemoData();
                        setShowProfileMenu(false);
                      }}
                      className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-amber-700 hover:bg-amber-50 cursor-pointer"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      <span>Reset All Demo Data</span>
                    </button>
                  )}

                  <button
                    onClick={async () => {
                      await logout();
                      setShowProfileMenu(false);
                      navigate('/login');
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-red-600 hover:bg-red-50 cursor-pointer"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Permission Restriction Toast Modal */}
      {permissionAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl border border-red-200">
            <div className="flex items-center gap-3 text-red-600 mb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-sm font-bold text-[#182B25]">Authorization Notice</h3>
            </div>
            <p className="text-xs text-[#64748B] leading-relaxed mb-4">{permissionAlert}</p>
            <div className="flex justify-end">
              <button
                onClick={() => setPermissionAlert(null)}
                className="rounded-xl bg-[#16866A] px-4 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disaster Mode Activation Confirmation Modal */}
      {showDisasterConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-red-200">
            <div className="flex items-center gap-3 text-red-600 mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-100">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#182B25]">Activate Disaster Response Mode?</h3>
                <p className="text-xs text-[#64748B]">Authorized Incident Coordinator Action</p>
              </div>
            </div>

            <p className="text-xs text-[#64748B] leading-relaxed mb-6">
              Activating Disaster Mode will prioritize emergency relief allocations (potable water, sanitation packs, cooked meals) across Moratuwa/Colombo affected sectors and activate rapid courier response teams.
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setShowDisasterConfirm(false)}
                className="rounded-xl border border-[#E5EAE7] px-4 py-2 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAF9] cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmDisasterActivation}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-700 shadow-md transition-colors cursor-pointer"
              >
                Confirm Disaster Activation
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
