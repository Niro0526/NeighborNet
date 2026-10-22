import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  User as UserIcon,
  CheckCircle2,
  LogOut,
  RotateCcw,
  ChevronDown,
  ShieldAlert,
  Leaf,
} from 'lucide-react';
import { useAuth, useOperational, useLivePolling } from '../../hooks';
import { UserRole, SystemNotification } from '../../types';
import { notificationService } from '../../services/notificationService';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { isApiMode } from '../../services/apiClient';
import { getPageTitle, ROLE_LABELS } from '../../config/navigation';

export const Header: React.FC = () => {
  const { currentUser, assignedRoles, hasRole, allUsers, switchUser, logout, resetDemoData } = useAuth();
  const { isDisasterMode, setMode } = useOperational();
  const navigate = useNavigate();
  const location = useLocation();
  const isAdminWorkspace = location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator');
  const pageTitle = getPageTitle(location.pathname);

  const [notifications, setNotifications] = useState<SystemNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDisasterConfirm, setShowDisasterConfirm] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

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
    fetcher: refreshNotifications,
    intervalMs: 30000,
    enabled: true,
  });

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

  const handleAccountSwitch = async (userId: string) => {
    await switchUser(userId);
    setShowProfileMenu(false);
    const target = allUsers.find((u) => u.id === userId);
    if (target) {
      if (target.assignedRoles.length === 1 && target.assignedRoles[0] === 'COORDINATOR') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between gap-3 border-b border-[#E5EAE7] bg-white px-3 md:px-5">
        <div className="flex items-center gap-3 min-w-0">
          <Link to="/dashboard" className="flex items-center gap-2 shrink-0 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#16866A] text-white">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
              </svg>
            </div>
          </Link>
          <div className="hidden lg:flex items-center gap-2 shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#16866A] text-white">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
              </svg>
            </div>
            <span className="text-sm font-extrabold text-[#182B25]">NeighborNet</span>
          </div>
          <span className="hidden sm:block h-5 w-px bg-[#E5EAE7] shrink-0" />
          <h1 className="text-sm md:text-base font-bold text-[#182B25] truncate">{pageTitle}</h1>
        </div>

        <div className="flex items-center gap-2">
          {hasRole('COORDINATOR') && isAdminWorkspace && (
            <button
              type="button"
              onClick={() => (isDisasterMode ? setMode('NORMAL') : setShowDisasterConfirm(true))}
              className={`hidden md:inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-bold border ${
                isDisasterMode
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-[#E5EAE7] bg-[#F8FAF9] text-[#64748B]'
              }`}
            >
              {isDisasterMode ? <ShieldAlert className="h-3.5 w-3.5" /> : <Leaf className="h-3.5 w-3.5" />}
              {isDisasterMode ? 'Disaster on' : 'Normal'}
            </button>
          )}

          <div className="relative" ref={notifRef}>
            <button
              type="button"
              onClick={() => { setShowNotifications(!showNotifications); refreshNotifications(); }}
              className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-[#E5EAE7] bg-white text-[#64748B] hover:bg-[#F8FAF9]"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 min-w-4 px-0.5 items-center justify-center rounded-full bg-red-600 text-[9px] font-bold text-white">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-[#E5EAE7] bg-white p-3 shadow-xl z-50">
                <div className="flex items-center justify-between pb-2 border-b border-[#E5EAE7]">
                  <h4 className="text-xs font-bold text-[#182B25]">Notifications</h4>
                  <button
                    type="button"
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
                <div className="max-h-72 overflow-y-auto divide-y divide-[#E5EAE7]">
                  {notifications.length === 0 ? (
                    <div className="py-6 text-center text-xs text-[#64748B]">No notifications</div>
                  ) : (
                    notifications.map((n) => (
                      <div key={n.id} className={`py-2.5 ${!n.read ? 'bg-emerald-50/40' : ''}`}>
                        <p className="text-xs font-semibold text-[#182B25]">{n.title}</p>
                        <p className="mt-1 text-[11px] text-[#64748B]">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
                <Link
                  to="/notifications"
                  onClick={() => setShowNotifications(false)}
                  className="block text-center text-xs font-bold text-[#16866A] hover:underline pt-2"
                >
                  View all
                </Link>
              </div>
            )}
          </div>

          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              aria-label={currentUser.name || 'Account menu'}
              className="flex items-center gap-2 rounded-lg p-1 hover:bg-[#F8FAF9]"
            >
              {currentUser.avatarUrl ? (
                <img src={currentUser.avatarUrl} alt="" className="h-8 w-8 rounded-full object-cover" />
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#16866A] text-white">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
              <span className="hidden sm:block text-xs font-bold text-[#182B25] max-w-[9rem] truncate">
                {currentUser.name}
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-[#64748B] hidden sm:block" />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-72 max-w-[calc(100vw-2rem)] rounded-xl border border-[#E5EAE7] bg-white p-3 shadow-xl z-50">
                <div className="pb-3 border-b border-[#E5EAE7]">
                  <p className="text-xs font-bold text-[#182B25] truncate">{currentUser.name}</p>
                  <p className="text-[11px] text-[#64748B] truncate">{currentUser.email}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {assignedRoles.map((role: UserRole) => (
                      <span key={role} className="text-[10px] font-bold px-2 py-0.5 rounded-md border border-[#E5EAE7] bg-[#F8FAF9]">
                        {ROLE_LABELS[role]}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="py-2 border-b border-[#E5EAE7]">
                  <Link
                    to="/profile"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-[#182B25] hover:bg-[#F8FAF9]"
                  >
                    <UserIcon className="h-3.5 w-3.5 text-[#64748B]" />
                    Profile
                  </Link>
                </div>

                {!isApiMode() && (
                  <div className="py-2 border-b border-[#E5EAE7]">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[#94A3B8] px-1 mb-1">Demo personas</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {allUsers.map((u) => (
                        <button
                          key={u.id}
                          type="button"
                          onClick={() => handleAccountSwitch(u.id)}
                          className={`flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[11px] text-left ${
                            u.id === currentUser.id ? 'bg-[#F8FAF9] font-bold text-[#16866A]' : 'text-[#182B25] hover:bg-[#F8FAF9]'
                          }`}
                        >
                          <span className="truncate">{u.name}</span>
                          {u.id === currentUser.id && <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />}
                        </button>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={async () => {
                        await resetDemoData();
                        setShowProfileMenu(false);
                      }}
                      className="mt-1 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-amber-700 hover:bg-amber-50"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      Reset demo data
                    </button>
                  </div>
                )}

                <button
                  type="button"
                  onClick={async () => {
                    await logout();
                    setShowProfileMenu(false);
                    navigate('/login');
                  }}
                  className="mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-red-600 hover:bg-red-50"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {showDisasterConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl border border-red-200">
            <h3 className="text-sm font-bold text-[#182B25]">Activate disaster mode?</h3>
            <p className="text-xs text-[#64748B] mt-2">
              This prioritizes emergency allocations. Only coordinators can change operational mode.
            </p>
            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => setShowDisasterConfirm(false)}
                className="rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    await setMode('DISASTER');
                    setShowDisasterConfirm(false);
                  } catch (error: any) {
                    alert(error.message || 'Could not activate disaster mode.');
                  }
                }}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
