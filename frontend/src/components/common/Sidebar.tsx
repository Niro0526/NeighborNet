import React from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Flame } from 'lucide-react';
import { useAuth, useOperational } from '../../hooks';
import { getDesktopNav, isNavItemActive } from '../../config/navigation';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  isAdminWorkspace: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle, isAdminWorkspace }) => {
  const { assignedRoles } = useAuth();
  const { isDisasterMode } = useOperational();
  const location = useLocation();
  const items = getDesktopNav(assignedRoles, isAdminWorkspace && assignedRoles.includes('COORDINATOR'));

  return (
    <aside
      className={`hidden lg:flex flex-col border-r border-[#E5EAE7] bg-white h-screen sticky top-0 shrink-0 transition-[width] duration-200 ${
        collapsed ? 'w-16' : 'w-[212px]'
      }`}
    >
      <div className={`flex h-14 items-center border-b border-[#E5EAE7] ${collapsed ? 'justify-center px-2' : 'justify-between px-3'}`}>
        {!collapsed && (
          <Link to={isAdminWorkspace ? '/admin/dashboard' : '/dashboard'} className="min-w-0">
            <p className="text-sm font-extrabold text-[#182B25] tracking-tight truncate">NeighborNet</p>
            <p className="text-[10px] font-semibold text-[#16866A] uppercase tracking-wider">
              {isAdminWorkspace ? 'Command' : 'Food Rescue'}
            </p>
          </Link>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[#64748B] hover:bg-[#F8FAF9] hover:text-[#182B25]"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {isDisasterMode && !collapsed && (
        <div className="mx-2 mt-2 flex items-center gap-1.5 rounded-lg bg-red-50 px-2 py-1.5 border border-red-200">
          <Flame className="h-3.5 w-3.5 text-red-600 shrink-0" />
          <span className="text-[10px] font-bold text-red-700">Disaster mode</span>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.id}
              to={item.path}
              title={item.label}
              className={() => {
                const active = isNavItemActive(location.pathname, item);
                return `flex items-center rounded-lg text-[13px] font-medium transition-colors ${
                  collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-2.5 py-2'
                } ${
                  active
                    ? isAdminWorkspace
                      ? 'bg-purple-700 text-white'
                      : 'bg-[#16866A] text-white'
                    : 'text-[#64748B] hover:bg-[#F8FAF9] hover:text-[#182B25]'
                }`;
              }}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};
