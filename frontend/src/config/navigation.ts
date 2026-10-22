import {
  LayoutDashboard,
  Package,
  Layers,
  User,
  ShoppingBag,
  Truck,
  HandHeart,
  Clock,
  Sparkles,
  Flame,
  type LucideIcon,
} from 'lucide-react';
import { UserRole } from '../types';

export interface AppNavItem {
  id: string;
  label: string;
  path: string;
  icon: LucideIcon;
}

export const PAGE_TITLES: { prefix: string; title: string }[] = [
  { prefix: '/community-food', title: 'Community Food' },
  { prefix: '/dashboard', title: 'Overview' },
  { prefix: '/food/add', title: 'Add Surplus Food' },
  { prefix: '/food/listings', title: 'My Food' },
  { prefix: '/food/allocations', title: 'Allocations' },
  { prefix: '/food/pickups', title: 'Pickup Tracking' },
  { prefix: '/food/history', title: 'Donation History' },
  { prefix: '/requests/create', title: 'Create Request' },
  { prefix: '/requests/my-requests', title: 'Requests' },
  { prefix: '/requests/available-food', title: 'Available Food' },
  { prefix: '/requests/deliveries', title: 'Deliveries' },
  { prefix: '/volunteer/tasks', title: 'My Tasks' },
  { prefix: '/volunteer/history', title: 'Task History' },
  { prefix: '/deliveries/active', title: 'Active Delivery' },
  { prefix: '/admin/dashboard', title: 'Operations' },
  { prefix: '/admin/matching', title: 'Smart Matching' },
  { prefix: '/admin/allocations', title: 'Smart Matching' },
  { prefix: '/admin/disasters', title: 'Disaster' },
  { prefix: '/admin/recovery', title: 'Recovery' },
  { prefix: '/admin/map', title: 'Live Map' },
  { prefix: '/admin/approvals', title: 'Approvals' },
  { prefix: '/admin/analytics', title: 'Analytics' },
  { prefix: '/admin/organizations', title: 'Organizations' },
  { prefix: '/admin/resources', title: 'Resources' },
  { prefix: '/admin/requests', title: 'Requests' },
  { prefix: '/admin/volunteers', title: 'Volunteers' },
  { prefix: '/admin/audit', title: 'Audit Trail' },
  { prefix: '/notifications', title: 'Notifications' },
  { prefix: '/profile', title: 'Profile' },
  { prefix: '/settings', title: 'Settings' },
];

export function getPageTitle(pathname: string): string {
  const match = PAGE_TITLES.find((entry) => pathname === entry.prefix || pathname.startsWith(`${entry.prefix}/`));
  return match?.title || 'NeighborNet';
}

export function isNavItemActive(pathname: string, item: AppNavItem): boolean {
  if (item.path === '/dashboard') return pathname === '/dashboard';
  if (item.path === '/profile') return pathname === '/profile';
  if (item.path === '/admin/dashboard') {
    return pathname === '/admin/dashboard' || pathname === '/admin';
  }
  if (item.path === '/admin/matching') {
    return pathname.startsWith('/admin/matching') || pathname.startsWith('/admin/allocations');
  }
  if (item.path === '/food/allocations') {
    return pathname.startsWith('/food/allocations') || pathname.startsWith('/food/pickups');
  }
  return pathname === item.path || pathname.startsWith(`${item.path}/`);
}

const OVERVIEW: AppNavItem = { id: 'overview', label: 'Overview', path: '/dashboard', icon: LayoutDashboard };
const PROFILE: AppNavItem = { id: 'profile', label: 'Profile', path: '/profile', icon: User };

const PROVIDER_ITEMS: AppNavItem[] = [
  { id: 'my-food', label: 'My Food', path: '/food/listings', icon: Package },
  { id: 'allocations', label: 'Allocations', path: '/food/allocations', icon: Layers },
];

const RECIPIENT_ITEMS: AppNavItem[] = [
  { id: 'requests', label: 'Requests', path: '/requests/my-requests', icon: ShoppingBag },
  { id: 'deliveries', label: 'Deliveries', path: '/requests/deliveries', icon: Truck },
];

const VOLUNTEER_ITEMS: AppNavItem[] = [
  { id: 'tasks', label: 'My Tasks', path: '/volunteer/tasks', icon: HandHeart },
  { id: 'availability', label: 'Availability', path: '/volunteer/current-task', icon: Clock },
];

const COORDINATOR_PERSONAL: AppNavItem[] = [
  { id: 'operations', label: 'Operations', path: '/admin/dashboard', icon: LayoutDashboard },
];

export const COORDINATOR_ADMIN_NAV: AppNavItem[] = [
  { id: 'admin-overview', label: 'Overview', path: '/admin/dashboard', icon: LayoutDashboard },
  { id: 'operations', label: 'Operations', path: '/admin/map', icon: Truck },
  { id: 'matching', label: 'Smart Matching', path: '/admin/matching', icon: Sparkles },
  { id: 'disaster', label: 'Disaster', path: '/admin/disasters', icon: Flame },
  { id: 'profile', label: 'Profile', path: '/profile', icon: User },
  { id: 'community-food', label: 'Community Food', path: '/community-food', icon: ShoppingBag },
];

function uniqueItems(items: AppNavItem[]): AppNavItem[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.path)) return false;
    seen.add(item.path);
    return true;
  });
}

export function getRoleDestinations(roles: UserRole[]): AppNavItem[] {
  const dest: AppNavItem[] = [];
  if (roles.includes('FOOD_PROVIDER')) dest.push(...PROVIDER_ITEMS);
  if (roles.includes('RECIPIENT')) dest.push(...RECIPIENT_ITEMS);
  if (roles.includes('VOLUNTEER')) dest.push(...VOLUNTEER_ITEMS);
  if (roles.includes('COORDINATOR')) dest.push(...COORDINATOR_PERSONAL);
  return uniqueItems(dest);
}

export function getDesktopNav(roles: UserRole[], isAdminWorkspace: boolean): AppNavItem[] {
  if (isAdminWorkspace) return COORDINATOR_ADMIN_NAV;
  const roleItems = getRoleDestinations(roles).slice(0, 3);
  return uniqueItems([OVERVIEW, { id: 'community-food', label: 'Community Food', path: '/community-food', icon: ShoppingBag }, ...roleItems, PROFILE]);
}

export function getMobileNav(roles: UserRole[], isAdminWorkspace: boolean): AppNavItem[] {
  if (isAdminWorkspace) {
    return [
      COORDINATOR_ADMIN_NAV[0],
      COORDINATOR_ADMIN_NAV[5],
      COORDINATOR_ADMIN_NAV[2],
      COORDINATOR_ADMIN_NAV[3],
      COORDINATOR_ADMIN_NAV[4],
    ];
  }
  const roleItems = getRoleDestinations(roles).slice(0, 2);
  return uniqueItems([OVERVIEW, { id: 'community-food', label: 'Food', path: '/community-food', icon: ShoppingBag }, ...roleItems.slice(0, 1), PROFILE]);
}

export const ROLE_LABELS: Record<UserRole, string> = {
  FOOD_PROVIDER: 'Food Provider',
  RECIPIENT: 'Recipient NGO',
  VOLUNTEER: 'Volunteer',
  COORDINATOR: 'Coordinator',
};
