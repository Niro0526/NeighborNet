import { Allocation, AllocationStatus, AIInsight, AIInsightStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptAllocation } from './apiAdapters';

export const allocationService = {
  async getMatchedOffers() {
    if (!isApiMode()) return [];
    const response = await apiClient.get('/allocations/offers/');
    return response.data;
  },
  /**
   * Fetches resource allocations.
   */
  async getAllocations(): Promise<Allocation[]> {
    if (!isApiMode()) {
      return mockRepository.getAllocations();
    }

    const rawList = await getAllPages('/allocations/');
    return rawList.map(adaptAllocation);
  },

  /**
   * Creates an atomic allocation with database row locks.
   */
  async createAllocation(payload: {
    resource_id: string;
    request_id: string;
    allocated_quantity: number;
  }): Promise<Allocation> {
    if (!isApiMode()) {
      const newAlloc: Allocation = {
        id: `ALC-${Date.now().toString().slice(-4)}`,
        foodListingId: payload.resource_id,
        requestId: payload.request_id,
        foodListingName: 'Surplus Food Lot',
        providerName: 'Perera Food Outlets',
        recipientName: 'Community Kitchen',
        quantityAllocated: payload.allocated_quantity,
        unit: 'kg',
        matchScore: 95,
        status: 'approved',
        aiRationale: 'Matched based on immediate proximity and dietary preference.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      mockRepository.addAllocation(newAlloc);
      return newAlloc;
    }

    const res = await apiClient.post('/allocations/', payload);
    return adaptAllocation(res.data);
  },

  /**
   * Approves or updates an allocation.
   */
  async updateAllocationStatus(id: string, status: AllocationStatus): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateAllocation(id, { status, updatedAt: new Date().toISOString() });
      return;
    }

    if (status === 'approved') {
      await apiClient.post(`/allocations/${id}/approve/`);
    } else {
      throw new Error(`Unsupported allocation action: ${status}`);
    }
  },

  async getAIInsights(): Promise<AIInsight[]> {
    if (!isApiMode()) {
      return mockRepository.getAIInsights();
    }
    try {
      const res = await apiClient.get<{ count: number; results: any[] }>('/intelligence/recommendations/');
      const batches = res.data?.results || [];
      if (batches.length > 0) {
        return batches.slice(0, 3).map((b: any): AIInsight => ({
          id: b.id,
          type: b.mode === 'DISASTER' ? 'DISASTER_PRIORITY' : 'FOOD_MATCH',
          title: `OR-Tools CP-SAT Batch #${b.id.slice(0, 6)}`,
          description: `Solver fulfilled ${b.fulfilled_demand_pct}% demand (${b.total_allocated_quantity} allocated across the batch's recorded units).`,
          relatedEntityIds: {},
          evidence: [
            `Allocations: ${b.total_allocated_quantity || 0} kg`,
            `Demand fulfilled: ${b.fulfilled_demand_pct || 0}%`,
            `Status: ${b.status || 'PENDING'}`
          ],
          suggestedAction: b.status === 'APPROVED' ? 'Monitor active delivery dispatches' : 'Review and approve recommendation allocations',
          priority: b.mode === 'DISASTER' ? 'high' : 'medium',
          createdTimestamp: b.created_at,
          status: b.status === 'APPROVED' ? 'applied' : b.status === 'REJECTED' ? 'dismissed' : 'pending',
          dataSourceLabel: 'Live PostgreSQL / OR-Tools Solver',
          explanation: `Mathematical optimization solved across active community requests using post-harvest / perishable shelf-life windows.`,
          simulatedScore: Number(b.fulfilled_demand_pct ?? 0),
        }));
      }
      return [];
    } catch {
      return [];
    }
  },

  async updateInsightStatus(id: string, status: AIInsightStatus): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateAIInsight(id, { status });
    }
  },
};

export default allocationService;
