import React, { useState } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Package,
  Truck,
  Bell,
  User,
  ShoppingBag,
  HandHeart,
  MapPin,
  Sparkles,
  ShieldCheck,
  Menu,
  X,
  SlidersHorizontal,
  Flame,
  Layers,
  Building2,
  BarChart3,
} from 'lucide-react';
import { useAuth } from '../../hooks';

export const MobileBottomNavigation: React.FC = () => {
  const { isFoodProvider, isRecipient, isVolunteer, isCoordinator, currentUser, assignedRoles } = useAuth();
  const location = useLocation();
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  const isAdmin = location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator');

  // Build top 4 primary items (max 5 with More)
  const getPrimaryItems = () => {
    if (isAdmin) {
      return [
        { label: 'Overview', path: '/admin/dashboard', icon: LayoutDashboard },
        { label: 'AI Match', path: '/admin/matching', icon: Sparkles },
        { label: 'Map', path: '/admin/map', icon: MapPin },
        { label: 'Alerts', path: '/notifications', icon: Bell },
      ];
    }

    const items = [{ label: 'Home', path: '/dashboard', icon: LayoutDashboard }];

    if (isFoodProvider) {
      items.push({ label: 'My Food', path: '/food/listings', icon: Package });
    } else if (isRecipient) {
      items.push({ label: 'Requests', path: '/requests/my-requests', icon: Package });
    } else if (isVolunteer) {
      items.push({ label: 'Tasks', path: '/volunteer/tasks', icon: HandHeart });
    }

    if (isVolunteer && isFoodProvider) {
      items.push({ label: 'Tasks', path: '/volunteer/tasks', icon: HandHeart });
    } else if (isVolunteer && isRecipient) {
      items.push({ label: 'Tasks', path: '/volunteer/tasks', icon: HandHeart });
    } else if (isRecipient && !isVolunteer) {
      items.push({ label: 'Available', path: '/requests/available-food', icon: ShoppingBag });
    } else if (isFoodProvider && !isVolunteer) {
      items.push({ label: 'Pickups', path: '/food/pickups', icon: Truck });
    }

    // Add Notifications to bring total to 4 (or 3) before More
    items.push({ label: 'Alerts', path: '/notifications', icon: Bell });

    return items.slice(0, 4);
  };

  const primaryItems = getPrimaryItems();

  return (
    <>
      {/* Slide-up "More" Drawer for Mobile */}
      {showMoreMenu && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
            onClick={() => setShowMoreMenu(false)}
          />
          <div className="fixed bottom-0 left-0 right-0 max-h-[85vh] overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl animate-in slide-in-from-bottom">
            <div className="flex items-center justify-between pb-4 border-b border-[#E5EAE7]">
              <div>
                <h3 className="text-base font-bold text-[#182B25]">All Permitted Actions</h3>
                <p className="text-xs text-[#64748B]">
                  {currentUser.name} • {assignedRoles.join(', ')}
                </p>
              </div>
              <button
                onClick={() => setShowMoreMenu(false)}
                className="rounded-full p-2 text-[#64748B] hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Coordinator Workspace Link in Mobile Drawer */}
            {isCoordinator && (
              <div className="mt-4 p-3 rounded-2xl bg-purple-50 border border-purple-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-purple-700" />
                    <div>
                      <h4 className="text-xs font-bold text-purple-900">
                        {isAdmin ? 'Personal User Dashboard' : 'Administration Workspace'}
                      </h4>
                      <p className="text-[10px] text-purple-700">
                        {isAdmin ? 'Return to regular food rescue operations' : 'Command center, AI matching & disasters'}
                      </p>
                    </div>
                  </div>
                  <Link
                    to={isAdmin ? '/dashboard' : '/admin/dashboard'}
                    onClick={() => setShowMoreMenu(false)}
                    className="rounded-xl bg-purple-700 px-3 py-1.5 text-xs font-bold text-white shadow-xs"
                  >
                    {isAdmin ? 'Open User' : 'Open Admin'}
                  </Link>
                </div>
              </div>
            )}

            {/* Permitted destinations list */}
            <div className="mt-4 space-y-3">
              {isFoodProvider && (
                <div>
                  <span className="text-[10px] font-bold text-[#94A3B8] uppercase">Food Provider</span>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <Link
                      to="/food/add"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <PlusCircle className="h-4 w-4 text-emerald-600" />
                      <span>Add Surplus Food</span>
                    </Link>
                    <Link
                      to="/food/pickups"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <Truck className="h-4 w-4 text-emerald-600" />
                      <span>Pickup Status</span>
                    </Link>
                  </div>
                </div>
              )}

              {isRecipient && (
                <div>
                  <span className="text-[10px] font-bold text-[#94A3B8] uppercase">Recipient / NGO</span>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <Link
                      to="/requests/create"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <PlusCircle className="h-4 w-4 text-blue-600" />
                      <span>Create Request</span>
                    </Link>
                    <Link
                      to="/requests/deliveries"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <Truck className="h-4 w-4 text-blue-600" />
                      <span>Deliveries</span>
                    </Link>
                  </div>
                </div>
              )}

              {isVolunteer && (
                <div>
                  <span className="text-[10px] font-bold text-[#94A3B8] uppercase">Volunteer</span>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <Link
                      to="/deliveries/active"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <Truck className="h-4 w-4 text-amber-600" />
                      <span>Current Delivery</span>
                    </Link>
                    <Link
                      to="/volunteer/history"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                    >
                      <HandHeart className="h-4 w-4 text-amber-600" />
                      <span>Delivery History</span>
                    </Link>
                  </div>
                </div>
              )}

              {/* Admin Pages if in Admin */}
              {isAdmin && (
                <div>
                  <span className="text-[10px] font-bold text-[#94A3B8] uppercase">Admin Management</span>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <Link
                      to="/admin/organizations"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2 rounded-xl border border-[#E5EAE7] text-xs font-medium"
                    >
                      <Building2 className="h-4 w-4 text-purple-600" />
                      <span>Organizations</span>
                    </Link>
                    <Link
                      to="/admin/allocations"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2 rounded-xl border border-[#E5EAE7] text-xs font-medium"
                    >
                      <Layers className="h-4 w-4 text-purple-600" />
                      <span>Allocations</span>
                    </Link>
                    <Link
                      to="/admin/disasters"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2 rounded-xl border border-[#E5EAE7] text-xs font-medium"
                    >
                      <Flame className="h-4 w-4 text-red-600" />
                      <span>Disasters</span>
                    </Link>
                    <Link
                      to="/admin/analytics"
                      onClick={() => setShowMoreMenu(false)}
                      className="flex items-center gap-2 p-2 rounded-xl border border-[#E5EAE7] text-xs font-medium"
                    >
                      <BarChart3 className="h-4 w-4 text-purple-600" />
                      <span>Analytics</span>
                    </Link>
                  </div>
                </div>
              )}

              {/* Core Account Pages */}
              <div className="pt-2 border-t border-[#E5EAE7] grid grid-cols-2 gap-2">
                <Link
                  to="/profile"
                  onClick={() => setShowMoreMenu(false)}
                  className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                >
                  <User className="h-4 w-4 text-slate-600" />
                  <span>My Profile</span>
                </Link>
                <Link
                  to="/settings"
                  onClick={() => setShowMoreMenu(false)}
                  className="flex items-center gap-2 p-2.5 rounded-xl border border-[#E5EAE7] text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                >
                  <SlidersHorizontal className="h-4 w-4 text-slate-600" />
                  <span>Settings</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Primary 5-destination bottom navigation bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 lg:hidden border-t border-[#E5EAE7] bg-white/95 backdrop-blur-md px-2 py-1 shadow-lg">
        <div className="flex items-center justify-around">
          {primaryItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all ${
                    isActive
                      ? isAdmin
                        ? 'text-purple-700 font-bold'
                        : 'text-[#16866A] font-bold'
                      : 'text-[#64748B] hover:text-[#182B25]'
                  }`
                }
              >
                <Icon className="h-5 w-5" />
                <span className="text-[10px] mt-0.5">{item.label}</span>
              </NavLink>
            );
          })}

          {/* 5th button: More drawer trigger */}
          <button
            onClick={() => setShowMoreMenu(true)}
            className="flex flex-col items-center justify-center py-1 px-2 rounded-xl text-[#64748B] hover:text-[#182B25] transition-all"
          >
            <Menu className="h-5 w-5" />
            <span className="text-[10px] mt-0.5">More</span>
          </button>
        </div>
      </div>
    </>
  );
};
