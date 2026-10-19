import { DashboardStats, ActivityLog, MapMarkerItem, LocationRecord } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode } from './apiClient';
import { adaptActivityLog } from './apiAdapters';
import {
  calculateDashboardStats,
  mockWeeklyFoodTrends,
  mockFoodCategoryDistribution,
  mockRegionalSupplyDemand,
  mockDeliveryPerformance,
} from '../mockData/analytics';
import { mockLocations, mockMapMarkers } from '../mockData/mapLocations';

export const analyticsService = {
  /**
   * Fetches operational KPI statistics.
   * In API mode, queries GET /api/v1/dashboard/admin/ directly from PostgreSQL.
   */
  async getDashboardStats(): Promise<DashboardStats> {
    if (!isApiMode()) {
      return calculateDashboardStats();
    }

    const res = await apiClient.get('/dashboard/admin/');
    const k = res.data?.kpis || res.data?.metrics || {};
    return {
      totalFoodRescuedKg: Math.round(Number(k.availableSurplusKg ?? k.availableResourcesKg ?? 0)),
      activeRequestsCount: Number(k.activeRequestsCount ?? k.openRequestsCount ?? 0),
      urgentRequestsCount: Number(k.urgentRequestsCount ?? 0),
      volunteersOnlineCount: Number(k.volunteersOnlineCount ?? k.activeVolunteersCount ?? 0),
      deliveriesTodayCount: Number(k.deliveriesCompletedToday ?? k.activeDeliveriesCount ?? 0),
      activeDisasterCount: Number(res.data?.activeDisaster ? 1 : 0),
      mealsSavedEstimate: Math.round(Number(k.availableSurplusKg ?? 0) * 2.2),
      co2OffsetKgEstimate: Math.round(Number(k.availableSurplusKg ?? 0) * 1.9),
    };
  },

  /**
   * Part 5: Fetches live operational monitoring indicators for Coordinator Command Center.
   */
  async getLiveOperations() {
    if (!isApiMode()) {
      return null;
    }
    const res = await apiClient.get('/dashboard/admin/');
    return res.data?.liveOperations || null;
  },

  /**
   * Part 6: Fetches verified impact analytics with strict unit isolation and explicit denominators.
   */
  async getVerifiedImpact() {
    if (!isApiMode()) {
      return null;
    }
    const res = await apiClient.get('/intelligence/impact/');
    return res.data;
  },

  /**
   * Part 8: Submits pilot usability feedback from authenticated participants.
   */
  async submitPilotFeedback(payload: {
    category: string;
    rating: number;
    comments?: string;
    consent_to_share_internally?: boolean;
  }) {
    if (!isApiMode()) {
      return { success: true };
    }
    const res = await apiClient.post('/audit/feedback/', payload);
    return res.data;
  },

  /**
   * Part 8: Fetches aggregate feedback summary for Coordinators.
   */
  async getPilotFeedbackSummary() {
    if (!isApiMode()) {
      return null;
    }
    const res = await apiClient.get('/audit/feedback/summary/');
    return res.data;
  },

  async getWeeklyFoodTrends() {
    return mockWeeklyFoodTrends;
  },

  async getFoodCategoryDistribution() {
    return mockFoodCategoryDistribution;
  },

  async getRegionalSupplyDemand() {
    return mockRegionalSupplyDemand;
  },

  async getDeliveryPerformance() {
    return mockDeliveryPerformance;
  },


  /**
   * Fetches immutable audit logs.
   * In API mode, restricted to Coordinators via GET /api/v1/audit/.
   */
  async getActivityLogs(): Promise<ActivityLog[]> {
    if (!isApiMode()) {
      return mockRepository.getActivityLogs();
    }

    try {
      const res = await apiClient.get<{ count: number; results: any[] } | any[]>('/audit/');
      const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      return rawList.map(adaptActivityLog);
    } catch {
      return [];
    }
  },

  /**
   * Loads physical location records.
   * In API mode, maps registered organizations from PostgreSQL/PostGIS.
   */
  async getMapLocations(): Promise<LocationRecord[]> {
    if (!isApiMode()) {
      return mockLocations;
    }

    try {
      const res = await apiClient.get<{ count: number; results: any[] } | any[]>('/organizations/');
      const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      return rawList.map((org: any) => ({
        id: org.id,
        name: org.name,
        address: org.address,
        city: org.city || 'Colombo',
        postalCode: org.postal_code || '10400',
        coordinates: {
          latitude: Number(org.latitude || 6.9271),
          longitude: Number(org.longitude || 79.8612),
        },
        contactPerson: org.contact_email,
        contactPhone: org.contact_phone,
      }));
    } catch {
      return mockLocations;
    }
  },

  async getMapMarkers(): Promise<MapMarkerItem[]> {
    if (!isApiMode()) {
      return mockMapMarkers;
    }

    const locs = await this.getMapLocations();
    return locs.map((loc) => ({
      id: loc.id,
      title: loc.name,
      subtitle: loc.address || 'Operational Facility',
      type: 'PROVIDER',
      coordinates: loc.coordinates,
      statusBadge: 'Active Hub',
      urgency: 'medium',
      details: {
        capacity: 'Surplus Food & Logistics Hub',
        phone: loc.contactPhone || 'N/A',
      },
    }));
  },
};

export default analyticsService;
