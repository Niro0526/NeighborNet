import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks';
import { getMobileNav, isNavItemActive } from '../../config/navigation';

export const MobileBottomNavigation: React.FC = () => {
  const { assignedRoles } = useAuth();
  const location = useLocation();
  const isAdminWorkspace = assignedRoles.includes('COORDINATOR') && (location.pathname.startsWith('/admin') || location.pathname.startsWith('/coordinator'));
  const items = getMobileNav(assignedRoles, isAdminWorkspace);

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 lg:hidden border-t border-[#E5EAE7] bg-white/95 backdrop-blur-md px-1 py-1">
      <div className="flex items-center justify-around">
        {items.map((item) => {
          const Icon = item.icon;
          const active = isNavItemActive(location.pathname, item);
          return (
            <NavLink
              key={item.id}
              to={item.path}
              className={`flex min-w-0 flex-1 flex-col items-center justify-center py-1.5 px-1 rounded-lg ${
                active
                  ? isAdminWorkspace
                    ? 'text-purple-700 font-bold'
                    : 'text-[#16866A] font-bold'
                  : 'text-[#64748B]'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] mt-0.5 truncate max-w-full">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
