import {
  User,
  Organization,
  FoodListing,
  ResourceRequest,
  Volunteer,
  DeliveryTask,
  DisasterEvent,
  Allocation,
  AIInsight,
  SystemNotification,
  ActivityLog,
  OperationalMode,
  UserRole,
} from '../types';

import {
  mockUsers,
  mockOrganizations,
  mockFoodListings,
  mockResourceRequests,
  mockVolunteers,
  mockDeliveryTasks,
  mockDisasterEvents,
  mockAllocations,
  mockAIInsights,
  mockNotifications,
  mockActivityLogs,
} from '../mockData';

const STORAGE_PREFIX = 'neighbornet_demo_v3_';
const STORAGE_VERSION = 3;

interface RepositoryState {
  users: User[];
  organizations: Organization[];
  foodListings: FoodListing[];
  resourceRequests: ResourceRequest[];
  volunteers: Volunteer[];
  deliveryTasks: DeliveryTask[];
  disasterEvents: DisasterEvent[];
  allocations: Allocation[];
  aiInsights: AIInsight[];
  notifications: SystemNotification[];
  activityLogs: ActivityLog[];
  operationalMode: OperationalMode;
  currentUser: User;
}

class MockRepository {
  private state: RepositoryState;
  private listeners: Set<() => void> = new Set();

  constructor() {
    this.state = this.loadInitialState();
  }

  private loadInitialState(): RepositoryState {
    try {
      const stored = localStorage.getItem(`${STORAGE_PREFIX}state`);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.version === STORAGE_VERSION && parsed.data) {
          return parsed.data;
        }
      }
    } catch (e) {
      console.warn('Failed to parse demo state from localStorage, falling back to seed data', e);
    }

    return {
      users: structuredClone(mockUsers),
      organizations: structuredClone(mockOrganizations),
      foodListings: structuredClone(mockFoodListings),
      resourceRequests: structuredClone(mockResourceRequests),
      volunteers: structuredClone(mockVolunteers),
      deliveryTasks: structuredClone(mockDeliveryTasks),
      disasterEvents: structuredClone(mockDisasterEvents),
      allocations: structuredClone(mockAllocations),
      aiInsights: structuredClone(mockAIInsights),
      notifications: structuredClone(mockNotifications),
      activityLogs: structuredClone(mockActivityLogs),
      operationalMode: 'NORMAL',
      currentUser: structuredClone(mockUsers[0]), // Default to Ravi Mendis (Food Provider & Volunteer)
    };
  }

  private persist() {
    try {
      localStorage.setItem(
        `${STORAGE_PREFIX}state`,
        JSON.stringify({ version: STORAGE_VERSION, data: this.state })
      );
    } catch (e) {
      console.warn('Failed to persist demo state to localStorage', e);
    }
    this.notify();
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((fn) => fn());
  }

  public resetToSeedData() {
    localStorage.removeItem(`${STORAGE_PREFIX}state`);
    this.state = {
      users: structuredClone(mockUsers),
      organizations: structuredClone(mockOrganizations),
      foodListings: structuredClone(mockFoodListings),
      resourceRequests: structuredClone(mockResourceRequests),
      volunteers: structuredClone(mockVolunteers),
      deliveryTasks: structuredClone(mockDeliveryTasks),
      disasterEvents: structuredClone(mockDisasterEvents),
      allocations: structuredClone(mockAllocations),
      aiInsights: structuredClone(mockAIInsights),
      notifications: structuredClone(mockNotifications),
      activityLogs: structuredClone(mockActivityLogs),
      operationalMode: 'NORMAL',
      currentUser: structuredClone(mockUsers[0]),
    };
    this.persist();
  }

  // State Getters
  public getUsers(): User[] {
    return structuredClone(this.state.users);
  }

  public getCurrentUser(): User {
    return structuredClone(this.state.currentUser);
  }

  public setCurrentUser(userOrIdentifier: User | string) {
    if (typeof userOrIdentifier === 'string') {
      let found = this.state.users.find(
        (u) => u.id === userOrIdentifier || u.email.toLowerCase() === userOrIdentifier.toLowerCase()
      );
      if (!found) {
        found = this.state.users.find((u) => u.assignedRoles.includes(userOrIdentifier as UserRole));
      }
      if (found) {
        this.state.currentUser = structuredClone(found);
      }
    } else {
      this.state.currentUser = structuredClone(userOrIdentifier);
    }
    this.persist();
  }

  public switchActiveRole(targetRole: UserRole): User {
    const user = this.state.currentUser;
    if (!user.assignedRoles.includes(targetRole)) {
      throw new Error(`Unauthorized role switch: User ${user.name} does not possess approved role ${targetRole}`);
    }
    user.activeRole = targetRole;
    user.role = targetRole;

    const idx = this.state.users.findIndex((u) => u.id === user.id);
    if (idx !== -1) {
      this.state.users[idx].activeRole = targetRole;
      this.state.users[idx].role = targetRole;
    }

    this.addActivityLog({
      id: `LOG-${Date.now()}`,
      timestamp: new Date().toISOString(),
      userId: user.id,
      userName: user.fullName,
      userRole: targetRole,
      action: 'WORKSPACE_SWITCHED',
      details: `User switched active workspace to ${targetRole}.`,
      category: 'SYSTEM',
    });

    this.persist();
    return structuredClone(user);
  }

  public getOperationalMode(): OperationalMode {
    return this.state.operationalMode;
  }

  public setOperationalMode(mode: OperationalMode) {
    // Only coordinators can trigger disaster mode transitions
    if (!this.state.currentUser.assignedRoles.includes('COORDINATOR')) {
      throw new Error('Unauthorized action: Only approved Coordinator accounts can activate or deactivate disaster modes.');
    }
    this.state.operationalMode = mode;
    this.addActivityLog({
      id: `LOG-${Date.now()}`,
      timestamp: new Date().toISOString(),
      userId: this.state.currentUser.id,
      userName: this.state.currentUser.fullName,
      userRole: this.state.currentUser.activeRole || this.state.currentUser.assignedRoles[0] || 'FOOD_PROVIDER',
      action: mode === 'DISASTER' ? 'DISASTER_MODE_ACTIVATED' : 'NORMAL_MODE_RESUMED',
      details: `Coordinator switched system operational mode to ${mode} mode.`,
      category: 'DISASTER',
    });
    this.persist();
  }

  public getOrganizations(): Organization[] {
    return structuredClone(this.state.organizations);
  }

  public getFoodListings(): FoodListing[] {
    return structuredClone(this.state.foodListings);
  }

  public addFoodListing(listing: FoodListing) {
    this.state.foodListings.unshift(listing);
    this.addActivityLog({
      id: `LOG-${Date.now()}`,
      timestamp: new Date().toISOString(),
      userId: this.state.currentUser.id,
      userName: this.state.currentUser.fullName,
      userRole: this.state.currentUser.activeRole || this.state.currentUser.assignedRoles[0] || 'FOOD_PROVIDER',
      action: 'FOOD_LISTED',
      details: `Registered surplus food: ${listing.name} (${listing.quantity} ${listing.unit}).`,
      category: 'FOOD',
    });
    this.persist();
  }

  public updateFoodListing(id: string, updates: Partial<FoodListing>) {
    const idx = this.state.foodListings.findIndex((f) => f.id === id);
    if (idx !== -1) {
      this.state.foodListings[idx] = { ...this.state.foodListings[idx], ...updates };
      this.persist();
    }
  }

  public getResourceRequests(): ResourceRequest[] {
    return structuredClone(this.state.resourceRequests);
  }

  public addResourceRequest(req: ResourceRequest) {
    this.state.resourceRequests.unshift(req);
    this.addActivityLog({
      id: `LOG-${Date.now()}`,
      timestamp: new Date().toISOString(),
      userId: this.state.currentUser.id,
      userName: this.state.currentUser.fullName,
      userRole: this.state.currentUser.activeRole || this.state.currentUser.assignedRoles[0] || 'FOOD_PROVIDER',
      action: 'REQUEST_SUBMITTED',
      details: `Created resource request: ${req.itemName} (${req.requestedQuantity} ${req.unit}).`,
      category: 'REQUEST',
    });
    this.persist();
  }

  public updateResourceRequest(id: string, updates: Partial<ResourceRequest>) {
    const idx = this.state.resourceRequests.findIndex((r) => r.id === id);
    if (idx !== -1) {
      this.state.resourceRequests[idx] = { ...this.state.resourceRequests[idx], ...updates };
      this.persist();
    }
  }

  public getVolunteers(): Volunteer[] {
    return structuredClone(this.state.volunteers);
  }

  public updateVolunteer(id: string, updates: Partial<Volunteer>) {
    const idx = this.state.volunteers.findIndex((v) => v.id === id);
    if (idx !== -1) {
      this.state.volunteers[idx] = { ...this.state.volunteers[idx], ...updates };
      this.persist();
    }
  }

  public getDeliveryTasks(): DeliveryTask[] {
    return structuredClone(this.state.deliveryTasks);
  }

  public updateDeliveryTask(id: string, updates: Partial<DeliveryTask>) {
    const idx = this.state.deliveryTasks.findIndex((t) => t.id === id);
    if (idx !== -1) {
      this.state.deliveryTasks[idx] = { ...this.state.deliveryTasks[idx], ...updates };
      
      // If task transitioned to DELIVERED, synchronize across food listing and request
      if (updates.status === 'DELIVERED') {
        const task = this.state.deliveryTasks[idx];
        if (task.foodListingId) {
          this.updateFoodListing(task.foodListingId, { status: 'collected' });
        }
        if (task.requestId) {
          this.updateResourceRequest(task.requestId, { status: 'fulfilled' });
        }
      }

      this.persist();
    }
  }

  public getDisasterEvents(): DisasterEvent[] {
    return structuredClone(this.state.disasterEvents);
  }

  public updateDisasterEvent(id: string, updates: Partial<DisasterEvent>) {
    const idx = this.state.disasterEvents.findIndex((d) => d.id === id);
    if (idx !== -1) {
      this.state.disasterEvents[idx] = { ...this.state.disasterEvents[idx], ...updates };
      this.persist();
    }
  }

  public getAllocations(): Allocation[] {
    return structuredClone(this.state.allocations);
  }

  public addAllocation(alloc: Allocation) {
    this.state.allocations.unshift(alloc);
    this.persist();
  }

  public updateAllocation(id: string, updates: Partial<Allocation>) {
    const idx = this.state.allocations.findIndex((a) => a.id === id);
    if (idx !== -1) {
      this.state.allocations[idx] = { ...this.state.allocations[idx], ...updates };
      this.persist();
    }
  }

  public getAIInsights(): AIInsight[] {
    return structuredClone(this.state.aiInsights);
  }

  public updateAIInsight(id: string, updates: Partial<AIInsight>) {
    const idx = this.state.aiInsights.findIndex((ai) => ai.id === id);
    if (idx !== -1) {
      this.state.aiInsights[idx] = { ...this.state.aiInsights[idx], ...updates };
      this.persist();
    }
  }

  public getNotifications(): SystemNotification[] {
    return structuredClone(this.state.notifications);
  }

  public markNotificationAsRead(id: string) {
    const notif = this.state.notifications.find((n) => n.id === id);
    if (notif) {
      notif.read = true;
      this.persist();
    }
  }

  public markAllNotificationsAsRead() {
    this.state.notifications.forEach((n) => (n.read = true));
    this.persist();
  }

  public getActivityLogs(): ActivityLog[] {
    return structuredClone(this.state.activityLogs);
  }

  public addActivityLog(log: ActivityLog) {
    this.state.activityLogs.unshift(log);
    this.persist();
  }
}

export const mockRepository = new MockRepository();
