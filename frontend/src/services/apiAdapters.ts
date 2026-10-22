/**
 * NeighborNet AI - API Response Adapters & Data Normalization
 * Bridges Django REST Framework serialization formats and frontend view models.
 */

import {
  User,
  UserRole,
  FoodListing,
  FoodListingStatus,
  ResourceRequest,
  RequestStatus,
  RequestPriority,
  DeliveryTask,
  DeliveryTaskStatus,
  Volunteer,
  DisasterEvent,
  DisasterStatus,
  DisasterSeverity,
  Allocation,
  SystemNotification,
  ActivityLog,
} from '../types';

// Map Backend User -> Frontend User
export function adaptUser(raw: any): User {
  const roles = (raw.assignedRoles || raw.roles || []).map((r: string) => r.toUpperCase()) as UserRole[];
  return {
    id: raw.id,
    name: raw.name || raw.fullName || raw.full_name || raw.email?.split('@')[0] || 'User',
    fullName: raw.fullName || raw.full_name || raw.name || 'User',
    email: raw.email || '',
    phone: raw.phone || '',
    assignedRoles: roles,
    defaultWorkspace: raw.defaultWorkspace || raw.default_workspace || (roles.includes('COORDINATOR') && roles.length === 1 ? 'admin' : 'personal'),
    activeRole: roles[0],
    avatarUrl: raw.avatarUrl || raw.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(raw.name || 'User')}&background=16866A&color=fff`,
    status: raw.status || 'active',
    createdAt: raw.created_at || raw.createdAt || '',
  };
}

// Map Backend Resource -> Frontend FoodListing
export function adaptFoodListing(raw: any): FoodListing {
  const rawStatus = (raw.status || 'AVAILABLE').toUpperCase();
  let status: FoodListingStatus = 'available';
  if (rawStatus === 'RESERVED') status = 'reserved';
  else if (rawStatus === 'COLLECTED' || rawStatus === 'DEPLETED') status = 'collected';
  else if (rawStatus === 'EXPIRED') status = 'expired';
  else if (rawStatus === 'WITHDRAWN') status = 'withdrawn';

  return {
    id: raw.id,
    providerId: raw.providerId || raw.provider?.id || raw.provider || '',
    providerName: raw.providerName || (raw.provider?.name) || 'Organization unavailable',
    name: raw.name || 'Surplus Food Lot',
    category: raw.category || 'cooked_meals',
    quantity: Number(raw.quantity ?? 0),
    availableQuantity: Number(raw.availableQuantity ?? raw.quantity ?? 0),
    isDisasterRelief: Boolean(raw.isDisasterRelief ?? raw.is_disaster_relief),
    disasterEventId: raw.disasterEventId || raw.disaster_event_id || undefined,
    unit: raw.unit || 'kg',
    safeUntil: raw.safeUntil || raw.safe_until || '',
    pickupStart: raw.pickupStart || raw.pickup_start || '',
    pickupEnd: raw.pickupEnd || raw.pickup_end || '',
    pickupAddress: raw.pickupAddress || raw.pickup_address || '',
    pickupLatitude: Number(raw.pickupLatitude ?? raw.pickup_latitude ?? NaN),
    pickupLongitude: Number(raw.pickupLongitude ?? raw.pickup_longitude ?? NaN),
    storageRequirements: raw.storageRequirements || raw.storage_requirements || 'Ambient',
    unitWeightKg: raw.unit_weight_kg ?? null,
    locationId: raw.locationId || raw.providerId || '',
    status,
    dietaryTags: raw.dietaryTags || raw.dietary_tags || [],
    safetyNotes: raw.safetyNotes || raw.safety_notes || '',
    createdAt: raw.created_at || raw.createdAt || '',
  };
}

// Map Backend ResourceRequest -> Frontend ResourceRequest
export function adaptResourceRequest(raw: any): ResourceRequest {
  const rawStatus = (raw.status || 'OPEN').toUpperCase();
  let status: RequestStatus = 'pending';
  if (rawStatus === 'ALLOCATED') status = 'allocated';
  else if (rawStatus === 'PARTIALLY_ALLOCATED') status = 'partially_fulfilled';
  else if (rawStatus === 'FULFILLED') status = 'fulfilled';
  else if (rawStatus === 'CANCELLED') status = 'cancelled';

  return {
    id: raw.id,
    recipientId: raw.recipientId || raw.recipient?.id || raw.recipient || '',
    recipientName: raw.recipientName || (raw.recipient?.name) || 'Recipient Organization',
    category: raw.category || 'cooked_meals',
    itemName: raw.itemName || raw.item_name || 'Emergency Food Supply',
    requestedQuantity: Number(raw.requestedQuantity ?? raw.requested_quantity ?? 0),
    fulfilledQuantity: Number(raw.fulfilledQuantity ?? raw.fulfilled_quantity ?? 0),
    unit: raw.unit || 'meals',
    priority: (raw.priority?.toLowerCase() || 'medium') as RequestPriority,
    status,
    peopleImpacted: Number(raw.peopleImpacted ?? raw.people_impacted ?? 0),
    urgencyDeadline: raw.urgencyDeadline || raw.urgency_deadline || '',
    locationId: raw.recipientId || '',
    specialInstructions: raw.specialInstructions || raw.special_instructions || '',
    isDisasterRelief: Boolean(raw.isDisasterRelief ?? raw.is_disaster_relief),
    disasterEventId: raw.disasterEventId || raw.disaster_event_id || undefined,
    createdAt: raw.created_at || raw.createdAt || '',
  };
}

// Map Backend DeliveryTask -> Frontend DeliveryTask
export function adaptDeliveryTask(raw: any): DeliveryTask {
  const rawStatus = (raw.status || 'AVAILABLE').toUpperCase() as DeliveryTaskStatus;

  return {
    id: raw.id,
    allocationId: raw.allocation || raw.allocation_id || raw.allocationId,
    allocationStatus: raw.allocationStatus,
    foodListingId: raw.resource || raw.resource_id,
    requestId: raw.request || raw.request_id,
    title: raw.title || `Delivery: ${raw.cargoDescription || raw.cargo_description || 'Food Lot'}`,
    cargoDescription: raw.cargoDescription || raw.cargo_description || 'Surplus Food Lot',
    quantityDescription: raw.quantityDescription || `${raw.quantity || 0} ${raw.unit || 'kg'}`,
    status: rawStatus,
    priority: (raw.priority?.toLowerCase() || 'medium') as RequestPriority,
    volunteerId: raw.volunteerId || raw.volunteer?.id || raw.volunteer,
    volunteerName: raw.volunteerName || raw.volunteer?.full_name || raw.volunteer_name,
    pickupLocationId: raw.pickupLocationId || 'LOC-PICKUP',
    pickupLocationName: raw.pickupLocationName || raw.providerName || '',
    pickupAddress: raw.pickupAddress || raw.pickup_address || '',
    pickupContactPhone: raw.pickupContactPhone || raw.pickup_contact_phone || '',
    pickupTimeWindow: raw.pickupTimeWindow || raw.pickup_time_window || '',
    deliveryLocationId: raw.deliveryLocationId || 'LOC-DELIVERY',
    deliveryLocationName: raw.deliveryLocationName || raw.recipientName || '',
    deliveryAddress: raw.deliveryAddress || raw.delivery_address || '',
    deliveryContactPhone: raw.deliveryContactPhone || raw.delivery_contact_phone || '',
    deliveryDeadline: raw.deliveryDeadline || raw.delivery_deadline || '',
    estimatedDistanceKm: Number(raw.estimatedDistanceKm ?? raw.estimated_distance_km ?? 0),
    estimatedDurationMin: Number(raw.estimatedDurationMin ?? raw.estimated_duration_min ?? 0),
    isDisasterMode: Boolean(raw.isDisasterMode ?? raw.is_disaster_mode),
    notes: raw.notes || '',
    disruptionReason: raw.disruptionReason || raw.disruption_reason,
    statusEvents: (raw.statusEvents || raw.status_events || []).map((e: any) => ({
      id: e.id,
      fromStatus: e.fromStatus || e.from_status,
      toStatus: e.toStatus || e.to_status,
      changedByName: e.changedByName || e.changed_by_name || e.changed_by?.name,
      notes: e.notes || '',
      createdAt: e.createdAt || e.created_at,
    })),
    statusTimestamps: {
      created: raw.created_at || raw.createdAt || '',
      accepted: raw.assigned_at || raw.acceptedAt || raw.accepted_at,
      arrivedPickup: raw.arrivedPickupAt || raw.arrived_pickup_at,
      pickedUp: raw.pickedUpAt || raw.picked_up_at,
      arrivedDelivery: raw.arrivedDeliveryAt || raw.arrived_delivery_at,
      delivered: raw.deliveredAt || raw.delivered_at,
      receiptConfirmed: raw.receipt_confirmed_at,
    },
  };
}

// Map Backend Volunteer -> Frontend Volunteer
export function adaptVolunteer(raw: any): Volunteer {
  return {
    id: raw.id,
    userId: raw.userId || raw.user?.id || raw.user,
    fullName: raw.fullName || raw.full_name || 'Volunteer Courier',
    phone: raw.phone || '',
    status: raw.status || 'available',
    vehicleType: raw.vehicleType || raw.vehicle_type || 'motorcycle',
    vehicleCapacityKg: Number(raw.vehicleCapacityKg ?? raw.vehicle_capacity_kg ?? 0),
    completedDeliveriesCount: Number(raw.completedDeliveriesCount ?? raw.completed_deliveries_count ?? 0),
    rating: Number(raw.rating ?? 0),
    badge: raw.badge || '',
    verified: Boolean(raw.verified),
    currentLocation: raw.coordinates ? { latitude: raw.coordinates[1], longitude: raw.coordinates[0] } : undefined,
  };
}

// Map Backend DisasterEvent -> Frontend DisasterEvent
export function adaptDisasterEvent(raw: any): DisasterEvent {
  const rawStatus = (raw.status || 'ACTIVE').toLowerCase();
  let status: DisasterStatus = 'active';
  if (rawStatus === 'draft' || rawStatus === 'monitoring') status = 'monitoring';
  if (rawStatus === 'resolved' || rawStatus === 'closed') status = 'resolved';

  return {
    id: raw.id,
    title: raw.name || raw.title || 'Disaster Emergency',
    description: raw.description || '',
    status,
    severity: (raw.severity?.toLowerCase() || 'critical') as DisasterSeverity,
    declaredAt: raw.declaredAt || raw.started_at || raw.declared_at || raw.created_at || '',
    declaredByCoordinatorId: raw.declared_by?.id || raw.declared_by || 'COORDINATOR',
    affectedPopulation: Number(raw.affected_population ?? raw.affectedPopulation ?? 0),
    activeReliefRequestsCount: Number(raw.activeReliefRequestsCount ?? 0),
    activeResponseTeamsCount: Number(raw.activeResponseTeamsCount ?? 0),
    zones: raw.zones || [],
    requiredResourcesSummary: raw.requiredResourcesSummary || [],
  };
}

// Map Backend Allocation -> Frontend Allocation
export function adaptAllocation(raw: any): Allocation {
  const rawStatus = String(raw.status || 'APPROVED').toUpperCase();
  let status: Allocation['status'] = 'approved';
  if (rawStatus === 'PENDING') status = 'proposed';
  else if (rawStatus === 'FULFILLED') status = 'completed';
  else if (rawStatus === 'REJECTED') status = 'rejected';
  else if (rawStatus === 'CANCELLED') status = 'rejected';
  else if (rawStatus === 'IN_TRANSIT') status = 'in_transit';

  return {
    id: raw.id,
    foodListingId: raw.resource || raw.resource_id || raw.foodListingId,
    requestId: raw.request || raw.request_id || raw.requestId,
    foodListingName: raw.resourceName || raw.resource_name || raw.foodListingName || 'Surplus Food Lot',
    providerName: raw.providerName || raw.provider_name || 'Food Donor',
    recipientName: raw.recipientName || raw.recipient_name || 'Community Recipient',
    quantityAllocated: Number(raw.allocatedQuantity ?? raw.allocated_quantity ?? raw.quantityAllocated ?? 0),
    unit: raw.unit || 'kg',
    matchScore: Number(raw.matchScore ?? 0),
    status,
    volunteerId: raw.volunteer || undefined,
    deliveryTaskId: raw.deliveryTaskId || raw.delivery_task || undefined,
    aiRationale: raw.ai_rationale || raw.aiRationale || '',
    createdAt: raw.created_at || raw.createdAt || '',
    updatedAt: raw.updated_at || raw.updatedAt || '',
  };
}

// Map Backend Notification -> Frontend SystemNotification
export function adaptNotification(raw: any): SystemNotification {
  return {
    id: raw.id,
    title: raw.title || 'Notification',
    message: raw.message || '',
    type: (raw.type?.toLowerCase() || 'system') as any,
    targetRole: raw.target_role || 'ALL',
    targetUserId: raw.user,
    read: Boolean(raw.is_read ?? raw.read),
    createdAt: raw.created_at || raw.timestamp || '',
    actionUrl: raw.action_url || raw.actionUrl,
  };
}

// Map Backend ActivityLog -> Frontend ActivityLog
export function adaptActivityLog(raw: any): ActivityLog {
  return {
    id: raw.id,
    timestamp: raw.timestamp || raw.created_at || '',
    userId: raw.userId || raw.user || undefined,
    userName: raw.userName || raw.user_name || 'Unknown user',
    userRole: raw.userRole || raw.user_role || '',
    action: raw.action || 'ACTIVITY',
    details: raw.details || 'Activity logged',
    category: (raw.category?.toUpperCase() || 'SYSTEM') as any,
  };
}
