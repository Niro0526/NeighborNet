/**
 * NeighborNet AI - Core TypeScript Types & Enums
 * Complete domain models for Food Rescue & Disaster Resource Coordination Platform
 */

// User Roles
export type UserRole = 'FOOD_PROVIDER' | 'RECIPIENT' | 'VOLUNTEER' | 'COORDINATOR';

// System Operational Modes
export type OperationalMode = 'NORMAL' | 'DISASTER';

// Coordinates & Geographic Entities
export interface GeoCoordinate {
  latitude: number;
  longitude: number;
}

export interface LocationRecord {
  id: string;
  name: string;
  address: string;
  city: string;
  postalCode: string;
  coordinates: GeoCoordinate;
  landmark?: string;
  contactPerson?: string;
  contactPhone?: string;
}

// User Model
export interface User {
  id: string;
  name: string;
  fullName: string;
  email: string;
  phone: string;
  assignedRoles: UserRole[];
  defaultWorkspace?: 'personal' | 'admin';
  activeRole?: UserRole;
  role?: UserRole; // for backward compatibility with existing components
  organizationId?: string;
  avatarUrl?: string;
  status: 'active' | 'pending_verification' | 'suspended';
  createdAt: string;
  lastLoginAt?: string;
}

// Organization Model
export type OrganizationType = 
  | 'RESTAURANT'
  | 'BAKERY'
  | 'SUPERMARKET'
  | 'HOTEL'
  | 'FOOD_BANK'
  | 'NGO'
  | 'SHELTER'
  | 'COMMUNITY_KITCHEN'
  | 'RELIEF_CENTER'
  | 'GOVERNMENT_DISASTER_DESK';

export interface Organization {
  id: string;
  name: string;
  type: OrganizationType;
  registrationNumber: string;
  verified: boolean;
  contactEmail: string;
  contactPhone: string;
  locationId: string;
  operatingHours?: string;
  capacity?: number; // max people served per day
  description?: string;
  createdAt: string;
}

// Food Listing
export type FoodCategory = 
  | 'cooked_meals'
  | 'bakery'
  | 'fresh_produce'
  | 'dairy'
  | 'canned_packaged'
  | 'beverages';

export type FoodListingStatus = 'available' | 'reserved' | 'collected' | 'expired' | 'withdrawn';

export interface FoodListing {
  unitWeightKg?: number | null;
  availableQuantity?: number;
  isDisasterRelief?: boolean;
  disasterEventId?: string;
  id: string;
  providerId: string; // Organization ID or User ID
  providerName: string;
  name: string;
  category: FoodCategory;
  quantity: number;
  unit: 'kg' | 'meals' | 'boxes' | 'liters' | 'packages';
  preparedAt?: string; // ISO 8601
  safeUntil: string; // ISO 8601
  pickupStart: string; // ISO 8601
  pickupEnd: string; // ISO 8601
  pickupAddress?: string;
  pickupLatitude?: number;
  pickupLongitude?: number;
  storageRequirements: 'Ambient' | 'Refrigerated' | 'Keep Frozen' | 'Keep Warm (>60°C)';
  locationId: string;
  status: FoodListingStatus;
  dietaryTags?: ('Vegetarian' | 'Halal' | 'Vegan' | 'Gluten-Free')[];
  safetyNotes?: string;
  imageUrl?: string;
  createdAt: string;
}

// Resource Request (NGO / Recipient / Relief Center)
export type RequestPriority = 'low' | 'medium' | 'high' | 'urgent';

export type RequestStatus = 
  | 'pending'
  | 'allocated'
  | 'partially_fulfilled'
  | 'fulfilled'
  | 'cancelled';

export interface ResourceRequest {
  deliveryAddress?: string;
  deliveryLatitude?: number | null;
  deliveryLongitude?: number | null;
  allowPartial?: boolean;
  id: string;
  recipientId: string; // Organization ID
  recipientName: string;
  category: FoodCategory | 'drinking_water' | 'hygiene_kits' | 'blankets_bedding' | 'medical_supplies';
  itemName: string;
  requestedQuantity: number;
  fulfilledQuantity: number;
  unit: string;
  priority: RequestPriority;
  status: RequestStatus;
  peopleImpacted: number;
  urgencyDeadline: string; // ISO 8601
  locationId: string;
  specialInstructions?: string;
  isDisasterRelief: boolean;
  disasterEventId?: string;
  createdAt: string;
}

// Volunteer Model
export type VolunteerAvailabilityStatus = 'available' | 'busy' | 'offline';
export type VehicleType = 'motorcycle' | 'car' | 'van' | 'bicycle' | 'foot';

export interface Volunteer {
  id: string;
  userId: string;
  fullName: string;
  phone: string;
  status: VolunteerAvailabilityStatus;
  vehicleType: VehicleType;
  vehicleCapacityKg: number;
  currentLocation?: GeoCoordinate;
  currentLocationName?: string;
  completedDeliveriesCount: number;
  rating: number; // 1.0 - 5.0
  activeTaskId?: string;
  badge?: 'Top Responder' | 'Rapid Delivery' | 'Community Hero';
  verified: boolean;
}

// Delivery Task State Machine
export type DeliveryTaskStatus = 
  | 'AVAILABLE'
  | 'ACCEPTED'
  | 'ARRIVED_PICKUP'
  | 'PICKED_UP'
  | 'ARRIVED_DELIVERY'
  | 'DELIVERED'
  | 'DECLINED'
  | 'CANCELLED'
  | 'DISRUPTED';

export interface DeliveryTask {
  id: string;
  allocationId?: string;
  foodListingId?: string;
  requestId?: string;
  title: string;
  cargoDescription: string;
  quantityDescription: string;
  status: DeliveryTaskStatus;
  priority: RequestPriority;
  volunteerId?: string;
  volunteerName?: string;
  pickupLocationId: string;
  pickupLocationName: string;
  pickupAddress: string;
  pickupContactPhone: string;
  pickupTimeWindow: string;
  deliveryLocationId: string;
  deliveryLocationName: string;
  deliveryAddress: string;
  deliveryContactPhone: string;
  deliveryDeadline: string;
  estimatedDistanceKm: number;
  estimatedDurationMin: number;
  isDisasterMode: boolean;
  notes?: string;
  disruptionReason?: string;
  statusEvents?: DeliveryStatusEvent[];
  statusTimestamps: {
    created: string;
    accepted?: string;
    arrivedPickup?: string;
    pickedUp?: string;
    arrivedDelivery?: string;
    delivered?: string;
      receiptConfirmed?: string;
  };
  allocationStatus?: string;
}

export interface DeliveryStatusEvent {
  id: string;
  fromStatus: string;
  toStatus: string;
  changedByName?: string;
  notes?: string;
  createdAt: string;
}

// Disaster Event
export type DisasterSeverity = 'low' | 'medium' | 'high' | 'critical';
export type DisasterStatus = 'active' | 'monitoring' | 'resolved';

export interface AffectedZone {
  id: string;
  name: string;
  severity: DisasterSeverity;
  centerCoordinates: GeoCoordinate;
  radiusKm: number;
  affectedPopulation: number;
  urgentNeeds: string[];
  assignedDistributionHubs: string[];
}

export interface DisasterEvent {
  id: string;
  title: string;
  description: string;
  status: DisasterStatus;
  severity: DisasterSeverity;
  declaredAt: string;
  declaredByCoordinatorId: string;
  affectedPopulation: number;
  activeReliefRequestsCount: number;
  activeResponseTeamsCount: number;
  zones: AffectedZone[];
  requiredResourcesSummary: {
    category: string;
    needed: number;
    collected: number;
    unit: string;
  }[];
}

// Resource Allocation (Matching engine outcome)
export type AllocationStatus = 'proposed' | 'approved' | 'in_transit' | 'completed' | 'rejected';

export interface Allocation {
  id: string;
  foodListingId: string;
  requestId: string;
  foodListingName: string;
  providerName: string;
  recipientName: string;
  quantityAllocated: number;
  unit: string;
  matchScore: number; // 0-100%
  status: AllocationStatus;
  volunteerId?: string;
  deliveryTaskId?: string;
  aiRationale: string;
  createdAt: string;
  updatedAt: string;
}

// AI Insights & Recommendations
export type AIInsightType = 
  | 'FOOD_MATCH'
  | 'EXPIRY_RISK'
  | 'RESOURCE_SHORTAGE'
  | 'VOLUNTEER_REASSIGNMENT'
  | 'DISASTER_PRIORITY'
  | 'ROUTE_DISRUPTION';

export type AIInsightStatus = 'pending' | 'applied' | 'dismissed';

export interface AIInsight {
  id: string;
  type: AIInsightType;
  title: string;
  description: string;
  relatedEntityIds: {
    foodListingId?: string;
    requestId?: string;
    volunteerId?: string;
    disasterEventId?: string;
    deliveryTaskId?: string;
    organizationId?: string;
  };
  evidence: string[];
  suggestedAction: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdTimestamp: string;
  status: AIInsightStatus;
  dataSourceLabel: string;
  explanation: string;
  simulatedScore?: number;
}

// Notifications
export type NotificationType = 'alert' | 'match' | 'task' | 'delivery' | 'system' | 'disaster';

export interface SystemNotification {
  id: string;
  targetRole: UserRole | 'ALL';
  targetUserId?: string;
  title: string;
  message: string;
  type: NotificationType;
  read: boolean;
  actionUrl?: string;
  createdAt: string;
}

// Activity Log & Audit Trail
export interface ActivityLog {
  id: string;
  timestamp: string;
  userId?: string;
  userName: string;
  userRole: UserRole;
  action: string;
  details: string;
  category: 'FOOD' | 'REQUEST' | 'DELIVERY' | 'DISASTER' | 'AI' | 'SYSTEM';
}

// Map Entities
export interface MapMarkerItem {
  id: string;
  type: 'PROVIDER' | 'NGO' | 'VOLUNTEER' | 'PICKUP' | 'DELIVERY' | 'DISASTER_ZONE' | 'DISTRIBUTION_HUB';
  title: string;
  subtitle: string;
  coordinates: GeoCoordinate;
  statusBadge?: string;
  urgency?: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, string | number>;
}

// Dashboard Analytics Models
export interface DashboardStats {
  totalFoodRescuedKg: number;
  activeRequestsCount: number;
  urgentRequestsCount: number;
  volunteersOnlineCount: number;
  deliveriesTodayCount: number;
  activeDisasterCount: number;
  mealsSavedEstimate: number;
  co2OffsetKgEstimate: number;
}

// Pilot Feedback & Onboarding Models
export type PilotFeedbackCategory = 
  | 'PLATFORM_USABILITY'
  | 'MATCHING_QUALITY'
  | 'DELIVERY_COORDINATION'
  | 'DISASTER_RESPONSE'
  | 'SYSTEM_STABILITY'
  | 'GENERAL_PILOT';

export interface PilotFeedback {
  id: string;
  category: PilotFeedbackCategory;
  categoryDisplay?: string;
  rating: number; // 1-5
  comments: string;
  consentToShareInternally: boolean;
  userName?: string;
  userRole?: string;
  createdAt: string;
}

export interface PilotFeedbackSummary {
  totalSubmissions: number;
  averageRating: number;
  categoryBreakdown: Record<string, { count: number; avgRating: number }>;
  recentFeedbacks: PilotFeedback[];
}

export interface OrganizationProfile {
  id: string;
  name: string;
  type: string;
  registrationNumber?: string;
  verified: boolean;
  contactEmail: string;
  contactPhone: string;
  address: string;
  city: string;
  postalCode?: string;
  latitude: number;
  longitude: number;
  capacity?: number;
  operatingHours?: string;
  serviceArea?: string;
  description?: string;
  profileCompletion: number;
  missingProfileFields: string[];
  createdAt: string;
}

export interface VolunteerProfile extends Volunteer {
  profileCompletion?: number;
  missingProfileFields?: string[];
}
