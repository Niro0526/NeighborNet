import { apiClient, isApiMode } from './apiClient';

export interface EligibleMatchItem {
  resource_id: string;
  resource_name: string;
  provider_name: string;
  request_id: string;
  request_item_name: string;
  recipient_name: string;
  category: string;
  available_quantity: number;
  remaining_quantity: number;
  compatible_quantity: number;
  unit: string;
  distance_km: number;
  priority: string;
  is_disaster_relief: boolean;
  constraints_satisfied: string[];
}

export interface OptimizationRecommendationItem {
  id: string;
  batch: string;
  resource: string;
  resourceName: string;
  providerName: string;
  request: string;
  requestItemName: string;
  recipientName: string;
  allocated_quantity: number;
  unit: string;
  estimated_distance_km: number;
  distance_type: string;
  deadline_urgency: string;
  match_score: number;
  explanation: string;
  suggested_action: string;
  assigned_volunteer: string | null;
  volunteerName: string | null;
  volunteer_feasibility_notes: string;
  constraints_satisfied: string[];
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'APPLIED';
  createdAllocationId: string | null;
}

export interface RecommendationBatchItem {
  id: string;
  mode: 'NORMAL' | 'DISASTER';
  method: 'ORTOOLS_CPSAT' | 'BASELINE_FCFS' | 'BASELINE_NEAREST';
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'APPLIED';
  createdByName: string | null;
  approvedByName: string | null;
  appliedByName: string | null;
  created_at: string;
  approved_at: string | null;
  applied_at: string | null;
  solver_status: string;
  runtime_ms: number;
  total_allocated_quantity: number;
  fulfilled_demand_pct: number;
  unmet_demand: number;
  solver_metadata: Record<string, any>;
  notes: string;
  recommendationsCount: number;
  recommendations: OptimizationRecommendationItem[];
}

export interface DisruptionRecoveryPreview {
  disruption_id: string;
  task_id: string;
  event_type: string;
  original_plan: Record<string, any>;
  replacement_options: Array<{
    type: string;
    description: string;
    replacement_volunteer_id?: string;
    replacement_volunteer_name?: string;
    vehicle_capacity_kg?: number;
    staging_distance_km?: number;
    feasibility_notes?: string;
  }>;
  recovery_batch_id: string;
  approval_required: boolean;
}

export interface IntelligenceAnalyticsData {
  timestamp: string;
  inventory_metrics: {
    total_registered_supply_kg: number;
    available_surplus_kg: number;
    allocated_supply_kg: number;
    expiring_within_24h_kg: number;
    supply_by_category: Record<string, number>;
  };
  demand_metrics: {
    total_demand_kg: number;
    fulfilled_demand_kg: number;
    unmet_demand_kg: number;
    overall_fulfillment_rate_pct: number;
    total_people_impacted: number;
    demand_by_category: Record<string, number>;
    demand_by_priority: Record<string, number>;
  };
  logistics_and_rescue_metrics: {
    confirmed_rescued_kg: number;
    active_in_transit_kg: number;
    completed_deliveries_count: number;
    reported_disruptions_count: number;
  };
  volunteer_fleet: {
    total_volunteers: number;
    available_couriers: number;
    busy_on_delivery: number;
    offline: number;
  };
  optimizer_pipeline: {
    total_batches: number;
    pending_approval: number;
    applied_batches: number;
  };
  disaster_context: {
    disaster_id: string;
    title: string;
    severity: string;
    affected_location: string;
    affected_population: number;
    open_emergency_requests: number;
    emergency_needed_kg: number;
    emergency_unmet_kg: number;
  } | null;
}

export const intelligenceService = {
  /**
   * Fetches deterministic eligible matching pairs screened by hard constraints.
   */
  async getEligibleMatches(): Promise<EligibleMatchItem[]> {
    if (!isApiMode()) {
      return [];
    }
    const res = await apiClient.get('/intelligence/matches/');
    return res.data?.matches || [];
  },

  /**
   * Executes Google OR-Tools CP-SAT or Baseline matching and stages volunteer feasibility.
   */
  async runOptimization(payload: {
    method: 'ORTOOLS_CPSAT' | 'BASELINE_FCFS' | 'BASELINE_NEAREST';
    mode: 'NORMAL' | 'DISASTER';
    time_limit_seconds?: number;
  }): Promise<RecommendationBatchItem> {
    const res = await apiClient.post('/intelligence/optimize/', payload);
    return res.data?.batch;
  },

  /**
   * Retrieves list of generated recommendation batches.
   */
  async getBatches(): Promise<RecommendationBatchItem[]> {
    if (!isApiMode()) return [];
    const res = await apiClient.get('/intelligence/recommendations/');
    return res.data?.results || [];
  },

  /**
   * Retrieves detailed single recommendation batch.
   */
  async getBatchById(id: string): Promise<RecommendationBatchItem> {
    const res = await apiClient.get(`/intelligence/recommendations/${id}/`);
    return res.data;
  },

  /**
   * Coordinator approves a recommendation batch.
   */
  async approveBatch(id: string): Promise<RecommendationBatchItem> {
    const res = await apiClient.post(`/intelligence/recommendations/${id}/approve/`);
    return res.data?.batch;
  },

  /**
   * Coordinator rejects a recommendation batch.
   */
  async rejectBatch(id: string, reason: string): Promise<RecommendationBatchItem> {
    const res = await apiClient.post(`/intelligence/recommendations/${id}/reject/`, { reason });
    return res.data?.batch;
  },

  /**
   * Coordinator atomically applies approved batch to PostgreSQL (creating Allocations & Tasks).
   */
  async applyBatch(id: string): Promise<{
    success: boolean;
    batch_id: string;
    allocations_count: number;
    delivery_tasks_count: number;
  }> {
    const res = await apiClient.post(`/intelligence/recommendations/${id}/apply/`);
    return res.data;
  },

  /**
   * Reports delivery disruption and previews recomputed replacement plan.
   */
  async previewRecovery(payload: {
    task_id: string;
    event_type: string;
    details: string;
  }): Promise<DisruptionRecoveryPreview> {
    const res = await apiClient.post('/intelligence/recovery/preview/', payload);
    return res.data;
  },

  /**
   * Coordinator applies replacement recovery plan atomically.
   */
  async applyRecovery(disruptionId: string): Promise<{ success: boolean; resolution: string }> {
    const res = await apiClient.post(`/intelligence/recovery/${disruptionId}/apply/`);
    return res.data;
  },

  /**
   * Fetches descriptive intelligence analytics computed via Pandas and NumPy.
   */
  async getAnalytics(): Promise<IntelligenceAnalyticsData | null> {
    if (!isApiMode()) return null;
    const res = await apiClient.get('/intelligence/analytics/');
    return res.data;
  },

  /**
   * Fetches benchmark evaluation runs.
   */
  async getEvaluations(): Promise<any[]> {
    if (!isApiMode()) return [];
    const res = await apiClient.get('/intelligence/evaluations/');
    return res.data?.results || [];
  },
};
