import { DashboardStats } from '../types';
import { mockFoodListings } from './foodListings';
import { mockResourceRequests } from './resourceRequests';
import { mockVolunteers } from './volunteers';
import { mockDeliveryTasks } from './deliveryTasks';
import { mockDisasterEvents } from './disasterEvents';

/**
 * Dynamically computes dashboard stats from centralized mock datasets
 */
export function calculateDashboardStats(): DashboardStats {
  const totalFoodRescuedKg = mockFoodListings
    .filter((f) => f.status === 'collected' || f.status === 'reserved' || f.status === 'available')
    .reduce((acc, f) => {
      if (f.unit === 'kg') return acc + f.quantity;
      if (f.unit === 'meals') return acc + f.quantity * 0.4; // 0.4 kg per meal average
      return acc + f.quantity;
    }, 0);

  const activeRequests = mockResourceRequests.filter(
    (r) => r.status === 'pending' || r.status === 'allocated' || r.status === 'partially_fulfilled'
  );

  const urgentRequests = activeRequests.filter((r) => r.priority === 'urgent' || r.priority === 'high');

  const volunteersOnline = mockVolunteers.filter((v) => v.status === 'available' || v.status === 'busy');

  const deliveriesToday = mockDeliveryTasks.filter((t) => t.status === 'DELIVERED');

  const activeDisasters = mockDisasterEvents.filter((d) => d.status === 'active');

  return {
    totalFoodRescuedKg: Math.round(totalFoodRescuedKg),
    activeRequestsCount: activeRequests.length,
    urgentRequestsCount: urgentRequests.length,
    volunteersOnlineCount: volunteersOnline.length,
    deliveriesTodayCount: deliveriesToday.length,
    activeDisasterCount: activeDisasters.length,
    mealsSavedEstimate: Math.round(totalFoodRescuedKg * 2.2), // ~2.2 meals per kg
    co2OffsetKgEstimate: Math.round(totalFoodRescuedKg * 2.5), // 2.5 kg CO2e per kg saved
  };
}

// Chart trend data: weekly food rescued (kg)
export const mockWeeklyFoodTrends = {
  days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  surplusCollected: [140, 185, 210, 195, 320, 410, 290],
  requestsFulfilled: [120, 160, 190, 175, 280, 390, 260],
};

// Food category breakdown data
export const mockFoodCategoryDistribution = [
  { name: 'Cooked Meals', value: 42 },
  { name: 'Fresh Produce', value: 28 },
  { name: 'Bakery & Grains', value: 18 },
  { name: 'Dairy & Beverages', value: 8 },
  { name: 'Packaged Food', value: 4 },
];

// Demand vs Supply balance by region
export const mockRegionalSupplyDemand = {
  regions: ['Moratuwa North', 'Mount Lavinia', 'Dehiwala', 'Colombo 03', 'Lunawa Flood Zone'],
  supplyKg: [310, 240, 180, 420, 110],
  demandKg: [360, 190, 220, 180, 520],
};

// Delivery performance metrics
export const mockDeliveryPerformance = {
  onTimeRatePercent: 94.8,
  averageDeliveryDurationMinutes: 19.5,
  foodSafetyIntegrityRatePercent: 99.2,
  totalDistanceCoveredKm: 342,
};
