import React from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Package,
  Truck,
  History,
  Bell,
  User,
  ShoppingBag,
  HandHeart,
  MapPin,
  Sparkles,
  Layers,
  Flame,
  ShieldCheck,
  Building2,
  FileText,
  BarChart3,
  RefreshCw,
  SlidersHorizontal,
  ArrowLeft,
  ChevronRight,
} from 'lucide-react';
import { useAuth, useOperational } from '../../hooks';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeColor?: string;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

export const Sidebar: React.FC = () => {
  const { isFoodProvider, isRecipient, isVolunteer, isCoordinator } = useAuth();
  const { isDisasterMode } = useOperational();
  const location = useLocation();

  const isAdminWorkspace = location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator');

  // Admin Workspace Navigation Items
  const adminSections: NavSection[] = [
    {
      title: 'COMMAND & CONTROL',
      items: [
        { label: 'Admin Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
        { label: 'Organizations', path: '/admin/organizations', icon: Building2 },
        { label: 'Resources & Inventory', path: '/admin/resources', icon: Package },
        { label: 'Resource Requests', path: '/admin/requests', icon: ShoppingBag },
        { label: 'Volunteer Fleet', path: '/admin/volunteers', icon: HandHeart },
      ],
    },
    {
      title: 'INTELLIGENCE & OPERATIONS',
      items: [
        { label: 'AI Matching Engine', path: '/admin/matching', icon: Sparkles, badge: 'AI', badgeColor: 'bg-emerald-100 text-emerald-800' },
        { label: 'Resource Allocations', path: '/admin/allocations', icon: Layers },
        { label: 'Geospatial Command', path: '/admin/map', icon: MapPin },
        {
          label: 'Disaster Management',
          path: '/admin/disasters',
          icon: Flame,
          badge: isDisasterMode ? 'ACTIVE' : undefined,
          badgeColor: 'bg-red-100 text-red-700 animate-pulse',
        },
        { label: 'Recovery & Transition', path: '/admin/recovery', icon: RefreshCw },
      ],
    },
    {
      title: 'GOVERNANCE & AUDIT',
      items: [
        { label: 'Approvals & Verify', path: '/admin/approvals', icon: ShieldCheck },
        { label: 'Platform Analytics', path: '/admin/analytics', icon: BarChart3 },
        { label: 'Audit Trail Logs', path: '/admin/audit', icon: FileText },
      ],
    },
  ];

  // Smart Unified Personal Workspace Navigation
  const personalSections: NavSection[] = [
    {
      items: [
        { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
      ],
    },
  ];

  if (isFoodProvider) {
    personalSections.push({
      title: 'FOOD PROVIDER',
      items: [
        { label: 'My Food', path: '/food/listings', icon: Package },
        { label: 'Add Food', path: '/food/add', icon: PlusCircle },
        { label: 'Pickups', path: '/food/pickups', icon: Truck },
      ],
    });
  }

  if (isRecipient) {
    personalSections.push({
      title: 'RECIPIENT / NGO',
      items: [
        { label: 'Resource Requests', path: '/requests/my-requests', icon: Package },
        { label: 'Available Resources', path: '/requests/available-food', icon: ShoppingBag },
        { label: 'Deliveries', path: '/requests/deliveries', icon: Truck },
      ],
    });
  }

  if (isVolunteer) {
    personalSections.push({
      title: 'VOLUNTEER COURIER',
      items: [
        { label: 'Volunteer Tasks', path: '/volunteer/tasks', icon: HandHeart },
        { label: 'Current Delivery', path: '/deliveries/active', icon: Truck },
        { label: 'History', path: '/volunteer/history', icon: History },
      ],
    });
  }

  if (isCoordinator) {
    personalSections.push({
      title: 'ADMINISTRATION',
      items: [
        {
          label: 'Administration Workspace',
          path: '/admin/dashboard',
          icon: ShieldCheck,
          badge: 'Admin',
          badgeColor: 'bg-purple-100 text-purple-700',
        },
      ],
    });
  }

  // Always show system/utility destinations
  personalSections.push({
    title: 'ACCOUNT & SYSTEM',
    items: [
      { label: 'Notifications', path: '/notifications', icon: Bell },
      { label: 'Profile', path: '/profile', icon: User },
      { label: 'Settings', path: '/settings', icon: SlidersHorizontal },
    ],
  });

  const activeSections = isAdminWorkspace ? adminSections : personalSections;

  return (
    <aside className="hidden lg:flex w-64 flex-col border-r border-[#E5EAE7] bg-white h-screen sticky top-0 shrink-0">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-2.5 px-6 border-b border-[#E5EAE7]">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#16866A] text-white shadow-xs">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
            <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
          </svg>
        </div>
        <div>
          <span className="font-extrabold text-[#182B25] text-base tracking-tight flex items-center gap-1">
            NeighborNet <span className="text-[#16866A] text-xs font-bold uppercase tracking-widest bg-emerald-50 px-1.5 py-0.5 rounded-md border border-emerald-200">AI</span>
          </span>
          <p className="text-[10px] text-[#64748B] font-medium">
            {isAdminWorkspace ? 'Admin & Incident Command' : 'Food Rescue & Relief Network'}
          </p>
        </div>
      </div>

      {/* Admin Workspace Switch Banner or Emergency Ribbon */}
      {isAdminWorkspace ? (
        <div className="p-3 border-b border-purple-100 bg-purple-50/70">
          <Link
            to="/dashboard"
            className="flex items-center justify-between gap-2 rounded-xl bg-white border border-purple-200 px-3 py-2 text-xs font-bold text-purple-800 hover:bg-purple-100/50 shadow-2xs transition-all"
          >
            <div className="flex items-center gap-2">
              <ArrowLeft className="h-3.5 w-3.5 text-purple-700" />
              <span>Personal Dashboard</span>
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-purple-400" />
          </Link>
        </div>
      ) : isDisasterMode ? (
        <div className="mx-3 mt-3 rounded-xl bg-red-50 p-2.5 border border-red-200">
          <div className="flex items-center gap-2 text-red-700">
            <Flame className="h-4 w-4 animate-bounce text-red-600" />
            <span className="text-xs font-bold tracking-tight">Disaster Mode Active</span>
          </div>
          <p className="mt-1 text-[11px] text-red-600/80 leading-snug">
            Emergency protocols prioritized for Colombo-Moratuwa flood zone.
          </p>
        </div>
      ) : null}

      {/* Dynamic Navigation List */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {activeSections.map((section, sIdx) => (
          <div key={section.title || `sec-${sIdx}`} className="space-y-1">
            {section.title && (
              <div className="px-3 pb-1 pt-1 text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">
                {section.title}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium transition-all ${
                      isActive
                        ? isAdminWorkspace
                          ? 'bg-purple-700 text-white font-semibold shadow-xs'
                          : 'bg-[#16866A] text-white font-semibold shadow-xs'
                        : 'text-[#64748B] hover:bg-[#F8FAF9] hover:text-[#182B25]'
                    }`
                  }
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.2 rounded-md ${item.badgeColor || 'bg-slate-100 text-slate-700'}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-3.5 border-t border-[#E5EAE7] bg-[#F8FAF9]/50">
        <div className="flex items-center justify-between text-[11px] text-[#64748B]">
          <span className="font-medium">ModelX 2.0 Edition</span>
          <span className="font-semibold text-emerald-700">Moratuwa SL</span>
        </div>
      </div>
    </aside>
  );
};
