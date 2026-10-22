import React from 'react';
import { useAuth } from '../../hooks';
import { ProviderDashboard } from '../provider/ProviderDashboard';
import { UnifiedDashboard } from './UnifiedDashboard';
import { CommunityFoodPage } from '../recipient/CommunityFoodPage';

export const DashboardEntry: React.FC = () => {
  const { assignedRoles } = useAuth();
  if (assignedRoles.length === 0) return <CommunityFoodPage />;

  if (assignedRoles.length === 1 && assignedRoles[0] === 'FOOD_PROVIDER') {
    return <ProviderDashboard />;
  }

  return <UnifiedDashboard />;
};
