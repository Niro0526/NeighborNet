import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AuthLayout } from '../layouts/AuthLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { AdminProtectedRoute } from '../components/common/AdminProtectedRoute';
import { RoleProtectedRoute } from '../components/common/RoleProtectedRoute';

import { LandingPage } from '../pages/public/LandingPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { ForgotPasswordPage } from '../pages/auth/ForgotPasswordPage';

import { UnifiedDashboard } from '../pages/dashboard/UnifiedDashboard';
import { CoordinatorDashboard } from '../pages/coordinator/CoordinatorDashboard';
import { VolunteerDashboard } from '../pages/volunteer/VolunteerDashboard';
import { AddFoodPage } from '../pages/provider/AddFoodPage';
import { ProviderPickupsPage } from '../pages/provider/ProviderPickupsPage';
import { CreateRequestPage } from '../pages/recipient/CreateRequestPage';
import { SmartMatchingPage } from '../pages/coordinator/SmartMatchingPage';
import { LiveMapPage } from '../pages/common/LiveMapPage';
import { AnalyticsReportsPage } from '../pages/common/AnalyticsReportsPage';
import { NotificationsPage } from '../pages/common/NotificationsPage';
import { ProfilePage } from '../pages/common/ProfilePage';
import { ApprovalsPage } from '../pages/coordinator/ApprovalsPage';
import { PlaceholderView } from '../pages/common/PlaceholderView';

export const router = createBrowserRouter([
  // Public Landing Page
  {
    path: '/',
    element: <LandingPage />,
  },

  // Auth Routes
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
    ],
  },

  // Authenticated Application Wrapped in DashboardLayout
  {
    element: <DashboardLayout />,
    children: [
      // 1. Smart Unified Dashboard (Personal Workspace for all regular users)
      {
        path: '/dashboard',
        element: <UnifiedDashboard />,
      },

      // 2. Food Provider Feature Routes (/food/*)
      {
        path: '/food',
        element: <RoleProtectedRoute requiredRole="FOOD_PROVIDER" title="Food Provider Permission Required" />,
        children: [
          {
            path: 'add',
            element: <AddFoodPage />,
          },
          {
            path: 'add-food',
            element: <Navigate to="/food/add" replace />,
          },
          {
            path: 'listings',
            element: (
              <PlaceholderView
                title="Food Listings Inventory"
                subtitle="Manage active, reserved, and expired surplus lots with live status indicators"
                backPath="/dashboard"
              />
            ),
          },
          {
            path: 'pickups',
            element: <ProviderPickupsPage />,
          },
          {
            path: 'history',
            element: (
              <PlaceholderView
                title="Donation History & Impact"
                subtitle="Review total kilograms donated, carbon offset metrics, and recipient commendations"
                backPath="/dashboard"
              />
            ),
          },
          { index: true, element: <Navigate to="/food/listings" replace /> },
        ],
      },

      // 3. Recipient / NGO Feature Routes (/requests/*)
      {
        path: '/requests',
        element: <RoleProtectedRoute requiredRole="RECIPIENT" title="NGO / Recipient Permission Required" />,
        children: [
          {
            path: 'create',
            element: <CreateRequestPage />,
          },
          {
            path: 'my-requests',
            element: (
              <PlaceholderView
                title="My Resource Requests"
                subtitle="Track pending, matched, and fulfilled community requests"
                backPath="/dashboard"
              />
            ),
          },
          {
            path: 'available-food',
            element: (
              <PlaceholderView
                title="Available Food Catalog"
                subtitle="Explore available surplus lots from verified food donors in your vicinity"
                backPath="/dashboard"
              />
            ),
          },
          {
            path: 'deliveries',
            element: (
              <PlaceholderView
                title="Incoming Deliveries"
                subtitle="Live tracking of volunteer couriers transporting resources to your center"
                backPath="/dashboard"
              />
            ),
          },
          {
            path: 'history',
            element: (
              <PlaceholderView
                title="Receipt History"
                subtitle="Complete audit log of received nutrition and emergency supplies"
                backPath="/dashboard"
              />
            ),
          },
          { index: true, element: <Navigate to="/requests/my-requests" replace /> },
        ],
      },

      // 4. Volunteer Feature Routes (/volunteer/*)
      {
        path: '/volunteer',
        element: <RoleProtectedRoute requiredRole="VOLUNTEER" title="Volunteer Courier Permission Required" />,
        children: [
          {
            path: 'tasks',
            element: (
              <PlaceholderView
                title="Available Volunteer Tasks"
                subtitle="Browse nearby missions matching your vehicle type and carrying capacity"
                backPath="/dashboard"
              />
            ),
          },
          {
            path: 'current-task',
            element: <VolunteerDashboard />,
          },
          {
            path: 'active',
            element: <VolunteerDashboard />,
          },
          {
            path: 'map',
            element: <LiveMapPage />,
          },
          {
            path: 'history',
            element: (
              <PlaceholderView
                title="Courier Run History"
                subtitle="Review your completed deliveries, community badges, and responder rating"
                backPath="/dashboard"
              />
            ),
          },
          { index: true, element: <Navigate to="/volunteer/tasks" replace /> },
        ],
      },

      // 5. Deliveries Feature Routes (/deliveries/*)
      {
        path: '/deliveries',
        children: [
          {
            path: 'active',
            element: <VolunteerDashboard />,
          },
          {
            path: 'history',
            element: (
              <PlaceholderView
                title="Delivery Audit History"
                subtitle="Review past completed food transports and recipient signatures"
                backPath="/dashboard"
              />
            ),
          },
          { index: true, element: <Navigate to="/deliveries/active" replace /> },
        ],
      },

      // 6. Coordinator / Administration Workspace Routes (/admin/*)
      {
        path: '/admin',
        element: <AdminProtectedRoute />,
        children: [
          { path: 'dashboard', element: <CoordinatorDashboard /> },
          {
            path: 'organizations',
            element: (
              <PlaceholderView
                title="Partner Organizations"
                subtitle="Directory of verified restaurants, supermarkets, bakeries, and shelters"
                backPath="/admin/dashboard"
              />
            ),
          },
          {
            path: 'resources',
            element: (
              <PlaceholderView
                title="Centralized Food Resources & Inventory"
                subtitle="Comprehensive catalog of surplus lots across all registered food providers"
                backPath="/admin/dashboard"
              />
            ),
          },
          {
            path: 'inventory',
            element: <Navigate to="/admin/resources" replace />,
          },
          {
            path: 'requests',
            element: (
              <PlaceholderView
                title="Community Resource Requests"
                subtitle="Prioritize high-need shelter demands and disaster relief requisitions"
                backPath="/admin/dashboard"
              />
            ),
          },
          {
            path: 'volunteers',
            element: (
              <PlaceholderView
                title="Volunteer Fleet Management"
                subtitle="Monitor real-time courier availability, vehicle capacities, and active dispatches"
                backPath="/admin/dashboard"
              />
            ),
          },
          {
            path: 'matching',
            element: <SmartMatchingPage />,
          },
          {
            path: 'allocations',
            element: <SmartMatchingPage />,
          },
          {
            path: 'map',
            element: <LiveMapPage />,
          },
          {
            path: 'disasters',
            element: (
              <PlaceholderView
                title="Disaster Emergency Management"
                subtitle="Activate disaster protocols, delineate affected hazard zones, and mobilize emergency rations"
                backPath="/admin/dashboard"
              />
            ),
          },
          {
            path: 'recovery',
            element: <SmartMatchingPage />,
          },
          {
            path: 'approvals',
            element: <ApprovalsPage />,
          },
          {
            path: 'analytics',
            element: <AnalyticsReportsPage />,
          },
          {
            path: 'reports',
            element: <AnalyticsReportsPage />,
          },
          {
            path: 'audit',
            element: (
              <PlaceholderView
                title="System Audit Trail"
                subtitle="Immutable event logs recording all state transitions, allocations, and user actions"
                backPath="/admin/dashboard"
              />
            ),
          },
          { index: true, element: <Navigate to="/admin/dashboard" replace /> },
        ],
      },

      // 7. Shared Account & System Utility Routes
      {
        path: '/notifications',
        element: <NotificationsPage />,
      },
      {
        path: '/profile',
        element: <ProfilePage />,
      },
      {
        path: '/settings',
        element: (
          <PlaceholderView
            title="Platform Settings & Preferences"
            subtitle="Configure notification alerts, operational radius, and theme preferences"
            backPath="/dashboard"
          />
        ),
      },

      // 8. Legacy Route Redirects (Ensuring 100% backward compatibility)
      { path: '/provider/dashboard', element: <Navigate to="/dashboard" replace /> },
      { path: '/provider/add-food', element: <Navigate to="/food/add" replace /> },
      { path: '/map', element: <Navigate to="/admin/map" replace /> },
      { path: '/reports', element: <Navigate to="/admin/reports" replace /> },
      { path: '/analytics', element: <Navigate to="/admin/analytics" replace /> },
      { path: '/provider/listings', element: <Navigate to="/food/listings" replace /> },
      { path: '/provider/pickups', element: <Navigate to="/food/pickups" replace /> },
      { path: '/provider/history', element: <Navigate to="/food/history" replace /> },
      { path: '/provider/notifications', element: <Navigate to="/notifications" replace /> },
      { path: '/provider/profile', element: <Navigate to="/profile" replace /> },
      { path: '/provider/*', element: <Navigate to="/dashboard" replace /> },

      { path: '/recipient/dashboard', element: <Navigate to="/dashboard" replace /> },
      { path: '/recipient/create-request', element: <Navigate to="/requests/create" replace /> },
      { path: '/recipient/available-food', element: <Navigate to="/requests/available-food" replace /> },
      { path: '/recipient/requests', element: <Navigate to="/requests/my-requests" replace /> },
      { path: '/recipient/deliveries', element: <Navigate to="/requests/deliveries" replace /> },
      { path: '/recipient/history', element: <Navigate to="/requests/history" replace /> },
      { path: '/recipient/notifications', element: <Navigate to="/notifications" replace /> },
      { path: '/recipient/profile', element: <Navigate to="/profile" replace /> },
      { path: '/recipient/*', element: <Navigate to="/dashboard" replace /> },

      { path: '/volunteer/dashboard', element: <Navigate to="/dashboard" replace /> },
      { path: '/volunteer/notifications', element: <Navigate to="/notifications" replace /> },
      { path: '/volunteer/profile', element: <Navigate to="/profile" replace /> },

      { path: '/coordinator/dashboard', element: <Navigate to="/admin/dashboard" replace /> },
      { path: '/coordinator/inventory', element: <Navigate to="/admin/resources" replace /> },
      { path: '/coordinator/requests', element: <Navigate to="/admin/requests" replace /> },
      { path: '/coordinator/volunteers', element: <Navigate to="/admin/volunteers" replace /> },
      { path: '/coordinator/matching', element: <Navigate to="/admin/matching" replace /> },
      { path: '/coordinator/allocations', element: <Navigate to="/admin/allocations" replace /> },
      { path: '/coordinator/map', element: <Navigate to="/admin/map" replace /> },
      { path: '/coordinator/disasters', element: <Navigate to="/admin/disasters" replace /> },
      { path: '/coordinator/recovery', element: <Navigate to="/admin/recovery" replace /> },
      { path: '/coordinator/approvals', element: <Navigate to="/admin/approvals" replace /> },
      { path: '/coordinator/organizations', element: <Navigate to="/admin/organizations" replace /> },
      { path: '/coordinator/analytics', element: <Navigate to="/admin/analytics" replace /> },
      { path: '/coordinator/audit', element: <Navigate to="/admin/audit" replace /> },
      { path: '/coordinator/notifications', element: <Navigate to="/notifications" replace /> },
      { path: '/coordinator/profile', element: <Navigate to="/profile" replace /> },
      { path: '/coordinator/*', element: <Navigate to="/admin/dashboard" replace /> },
    ],
  },

  // Fallback Catch-All
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
