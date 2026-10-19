import React, { useEffect, useState, useTransition } from 'react';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { useAuth, useOperational } from '../../hooks';
import { foodService } from '../../services/foodService';
import { requestService } from '../../services/requestService';
import { deliveryService } from '../../services/deliveryService';
import { volunteerService } from '../../services/volunteerService';
import { analyticsService } from '../../services/analyticsService';
import {
  FoodListing,
  ResourceRequest,
  DeliveryTask,
  Volunteer,
  DeliveryTaskStatus,
  ActivityLog,
} from '../../types';
import {
  Package,
  PlusCircle,
  Truck,
  ShoppingBag,
  HandHeart,
  CheckCircle2,
  Clock,
  Flame,
  ArrowRight,
  ShieldCheck,
  Building2,
  Users,
  MapPin,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const UnifiedDashboard: React.FC = () => {
  const { currentUser, assignedRoles, isFoodProvider, isRecipient, isVolunteer, isCoordinator } = useAuth();
  const { isDisasterMode, activeDisaster } = useOperational();

  const [, startTransition] = useTransition();

  // State across modules
  const [listings, setListings] = useState<FoodListing[]>([]);
  const [requests, setRequests] = useState<ResourceRequest[]>([]);
  const [tasks, setTasks] = useState<DeliveryTask[]>([]);
  const [volunteer, setVolunteer] = useState<Volunteer | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [activities, setActivities] = useState<ActivityLog[]>([]);

  // Collapsible module sections
  const [providerExpanded, setProviderExpanded] = useState<boolean>(true);
  const [recipientExpanded, setRecipientExpanded] = useState<boolean>(true);
  const [volunteerExpanded, setVolunteerExpanded] = useState<boolean>(true);

  // Status message / feedback
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const refreshAllData = async () => {
    // 1. Food listings
    if (isFoodProvider || isRecipient) {
      const allFood = await foodService.getFoodListings();
      setListings(allFood);
    }

    // 2. Resource requests
    if (isRecipient || isFoodProvider) {
      const allRequests = await requestService.getResourceRequests();
      setRequests(allRequests);
    }

    // 3. Delivery tasks & volunteer
    if (isVolunteer || isRecipient || isFoodProvider) {
      const allTasks = await deliveryService.getDeliveryTasks();
      setTasks(allTasks);
    }

    if (isVolunteer) {
      let vol = await volunteerService.getVolunteerByUserId(currentUser.id);
      if (!vol) {
        vol = await volunteerService.getVolunteerById('VOL-001');
      }
      if (vol) {
        setVolunteer(vol);
        setIsOnline(vol.status !== 'offline');
      }
    }

    // 4. Activity log
    const logs = await analyticsService.getActivityLogs();
    setActivities(logs);
  };

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const [allFood, allRequests, allTasks, logs] = await Promise.all([
          foodService.getFoodListings(),
          requestService.getResourceRequests(),
          deliveryService.getDeliveryTasks(),
          analyticsService.getActivityLogs(),
        ]);
        if (!isMounted) return;

        setListings(allFood);
        setRequests(allRequests);
        setTasks(allTasks);
        setActivities(logs);

        if (isVolunteer) {
          let vol = await volunteerService.getVolunteerByUserId(currentUser.id);
          if (!vol) {
            vol = await volunteerService.getVolunteerById('VOL-001');
          }
          if (vol && isMounted) {
            setVolunteer(vol);
            setIsOnline(vol.status !== 'offline');
          }
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [currentUser.id, isVolunteer, isFoodProvider, isRecipient]);

  // Volunteer availability toggle
  const toggleAvailability = async () => {
    const nextStatus = !isOnline;
    setIsOnline(nextStatus);
    if (volunteer) {
      await volunteerService.setAvailabilityStatus(volunteer.id, nextStatus ? 'available' : 'offline');
      setActionNotice(nextStatus ? 'Status updated: You are now Online and eligible for courier missions.' : 'Status updated: You are now Offline.');
      setTimeout(() => setActionNotice(null), 4000);
    }
  };

  // Volunteer task workflow state machine
  const currentVolunteerId = volunteer?.id || 'VOL-001';
  const activeTask = tasks.find(
    (t) =>
      (t.volunteerId === currentVolunteerId || (!t.volunteerId && t.status === 'ACCEPTED')) &&
      t.status !== 'DELIVERED' &&
      t.status !== 'DECLINED' &&
      t.status !== 'CANCELLED'
  );

  const availableTasks = tasks.filter((t) => t.status === 'AVAILABLE');

  const handleTaskAction = async (taskId: string, nextStatus: DeliveryTaskStatus) => {
    try {
      await deliveryService.updateTaskStatus(taskId, nextStatus, {
        volunteerId: currentVolunteerId,
        volunteerName: volunteer?.fullName || currentUser.name,
      });
      setActionNotice(`Task status updated to: ${nextStatus.replace('_', ' ')}`);
      setTimeout(() => setActionNotice(null), 4000);
      startTransition(() => {
        refreshAllData();
      });
    } catch (e: any) {
      alert(e.message || 'Error updating task state');
    }
  };

  // Recipient confirm receipt
  const handleConfirmReceipt = async (taskId: string) => {
    try {
      await deliveryService.updateTaskStatus(taskId, 'DELIVERED');
      setActionNotice('Receipt confirmed! Allocation marked as successfully delivered.');
      setTimeout(() => setActionNotice(null), 4000);
      refreshAllData();
    } catch (e: any) {
      alert(e.message || 'Error confirming receipt');
    }
  };

  // Metrics calculations
  const myFoodListings = listings.filter((l) => l.providerId === 'ORG-001' || l.providerName.toLowerCase().includes(currentUser.name.toLowerCase()));
  const displayListings = myFoodListings.length > 0 ? myFoodListings : listings.slice(0, 5);

  const totalDonatedKg = displayListings
    .filter((l) => l.status === 'collected')
    .reduce((acc, l) => acc + (l.unit === 'kg' ? l.quantity : l.quantity * 0.4), 0);

  const activeProviderCount = displayListings.filter((l) => l.status === 'available' || l.status === 'reserved').length;
  const activeRecipientRequests = requests.filter((r) => r.status === 'pending' || r.status === 'allocated');
  const incomingDeliveries = tasks.filter((t) => t.status === 'ACCEPTED' || t.status === 'ARRIVED_PICKUP' || t.status === 'PICKED_UP');
  const completedDeliveriesCount = volunteer?.completedDeliveriesCount || tasks.filter((t) => t.status === 'DELIVERED').length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Toast / Feedback Notice */}
      {actionNotice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-semibold text-emerald-800 flex items-center justify-between shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-emerald-700 hover:text-emerald-900 text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* 1. Welcome Header with Dynamic Role Badges */}
      <div className="rounded-2xl bg-white p-5 md:p-6 border border-[#E5EAE7] shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider">
                Personalized Dashboard
              </span>
              <span className="text-[#CBD5E1]">•</span>
              {assignedRoles.map((role) => {
                const labelMap = {
                  FOOD_PROVIDER: { name: 'Food Provider', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
                  RECIPIENT: { name: 'Recipient NGO', bg: 'bg-blue-50 text-blue-700 border-blue-200' },
                  VOLUNTEER: { name: 'Volunteer Courier', bg: 'bg-amber-50 text-amber-700 border-amber-200' },
                  COORDINATOR: { name: 'Coordinator Privileges', bg: 'bg-purple-50 text-purple-700 border-purple-200' },
                };
                const config = labelMap[role];
                return (
                  <span
                    key={role}
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold border ${config.bg}`}
                  >
                    {config.name}
                  </span>
                );
              })}
            </div>
            <h1 className="text-2xl font-black text-[#182B25] tracking-tight">
              Welcome back, {currentUser.name}!
            </h1>
            <p className="mt-1 text-xs text-[#64748B] max-w-2xl">
              {currentUser.email} • Your unified workspace automatically connects all your authorized community capabilities without switching accounts.
            </p>
          </div>

          {/* Coordinator Workspace Quick Access if user has Coordinator privileges */}
          {isCoordinator && (
            <div className="flex shrink-0">
              <Link
                to="/admin/dashboard"
                className="inline-flex items-center gap-2 rounded-xl bg-purple-700 px-4 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-purple-800 transition-all"
              >
                <ShieldCheck className="h-4 w-4" />
                <span>Administration Workspace</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          )}
        </div>

        {/* Unified Quick Actions Row */}
        <div className="mt-5 pt-4 border-t border-[#E5EAE7] flex flex-wrap items-center gap-2.5">
          <span className="text-xs font-bold text-[#182B25] mr-1">Quick Actions:</span>

          {isFoodProvider && (
            <>
              <Link
                to="/food/add"
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] transition-all shadow-xs"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Add Surplus Food</span>
              </Link>
              <Link
                to="/food/listings"
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#F8FAF9] border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-white transition-all"
              >
                <Package className="h-3.5 w-3.5 text-emerald-600" />
                <span>My Listings</span>
              </Link>
            </>
          )}

          {isRecipient && (
            <>
              <Link
                to="/requests/create"
                className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Create Resource Request</span>
              </Link>
              <Link
                to="/requests/available-food"
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#F8FAF9] border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-white transition-all"
              >
                <ShoppingBag className="h-3.5 w-3.5 text-blue-600" />
                <span>Browse Available Food</span>
              </Link>
            </>
          )}

          {isVolunteer && (
            <>
              <Link
                to="/volunteer/tasks"
                className="inline-flex items-center gap-1.5 rounded-xl bg-amber-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-amber-700 transition-all shadow-xs"
              >
                <HandHeart className="h-3.5 w-3.5" />
                <span>Browse Tasks ({availableTasks.length})</span>
              </Link>
              <button
                onClick={toggleAvailability}
                className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all ${
                  isOnline
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                    : 'border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
                <span>Courier: {isOnline ? 'Online' : 'Offline'}</span>
              </button>
            </>
          )}

          {isDisasterMode && (
            <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-red-100 px-3 py-1 text-xs font-bold text-red-700 border border-red-200 animate-pulse">
              <Flame className="h-3 w-3" />
              Disaster Protocol Active
            </span>
          )}
        </div>
      </div>

      {/* 2. Contextual Disaster Response Mode Banner (Section 7 & 8) */}
      {isDisasterMode && (
        <div className="rounded-2xl border-2 border-red-300 bg-gradient-to-r from-red-50 to-orange-50 p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white shadow-xs">
                <Flame className="h-6 w-6 animate-bounce" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black uppercase tracking-wider bg-red-600 text-white px-2 py-0.5 rounded-md">
                    Emergency Alert
                  </span>
                  <span className="text-xs font-bold text-red-900">
                    {activeDisaster?.title || 'Monsoon Flash Floods — Colombo South & Moratuwa'}
                  </span>
                </div>
                <p className="mt-1 text-xs text-red-800 leading-relaxed max-w-2xl">
                  {activeDisaster?.description || 'Severe precipitation has triggered waterlogging in Moratuwa lowlands. Verified relief kitchens and rapid volunteer dispatch are prioritized.'}{' '}
                  High-priority demand: <strong>prepared hot meals, drinking water cans, and dry rations</strong>.
                </p>
              </div>
            </div>

            {/* Contextual emergency shortcuts */}
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {isFoodProvider && (
                <Link
                  to="/food/add"
                  className="rounded-xl bg-red-700 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-red-800 transition-all"
                >
                  + Add Emergency Food
                </Link>
              )}
              {isRecipient && (
                <Link
                  to="/requests/create"
                  className="rounded-xl bg-red-700 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-red-800 transition-all"
                >
                  + Urgent Relief Request
                </Link>
              )}
              {isVolunteer && (
                <Link
                  to="/volunteer/tasks"
                  className="rounded-xl bg-red-700 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-red-800 transition-all"
                >
                  Relief Missions ({availableTasks.filter((t) => t.isDisasterMode).length || 2})
                </Link>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. Aggregated Dynamic Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isFoodProvider && (
          <StatCard
            title="Total Food Donated"
            value={`${Math.round(totalDonatedKg || 120)} kg`}
            subtitle="Redirected from landfill"
            icon={Package}
            variant="emerald"
          />
        )}
        {isFoodProvider && (
          <StatCard
            title="Active Surplus Listings"
            value={activeProviderCount || 3}
            subtitle="Available for matching"
            icon={Clock}
            variant="amber"
          />
        )}
        {isRecipient && (
          <StatCard
            title="Active Requests"
            value={activeRecipientRequests.length || 4}
            subtitle="Pending shelter allocations"
            icon={ShoppingBag}
            variant="blue"
          />
        )}
        {isRecipient && (
          <StatCard
            title="Incoming Deliveries"
            value={incomingDeliveries.length || 2}
            subtitle="Couriers en route to center"
            icon={Truck}
            variant="emerald"
          />
        )}
        {isVolunteer && (
          <StatCard
            title="Courier Deliveries"
            value={completedDeliveriesCount || 18}
            subtitle="Verified safe drop-offs"
            icon={CheckCircle2}
            variant="blue"
          />
        )}
        {isVolunteer && (
          <StatCard
            title="Available Missions"
            value={availableTasks.length || 3}
            subtitle={isOnline ? 'Online & eligible' : 'Status: Offline'}
            icon={HandHeart}
            variant={isOnline ? 'amber' : 'default'}
          />
        )}
        {isCoordinator && !isFoodProvider && !isRecipient && !isVolunteer && (
          <>
            <StatCard
              title="Surplus Monitored"
              value="1,240 kg"
              subtitle="Platform-wide food volume"
              icon={Package}
              variant="emerald"
            />
            <StatCard
              title="Active Shelters"
              value="28"
              subtitle="Registered recipients"
              icon={Users}
              variant="blue"
            />
            <StatCard
              title="Volunteer Fleet"
              value="54"
              subtitle="Active couriers online"
              icon={HandHeart}
              variant="amber"
            />
            <StatCard
              title="System Protocol"
              value={isDisasterMode ? 'Emergency' : 'Normal'}
              subtitle="Operational state"
              icon={ShieldCheck}
              variant={isDisasterMode ? 'red' : 'emerald'}
            />
          </>
        )}
      </div>

      {/* 4. Volunteer Interactive Courier State Machine (If Volunteer has Active Delivery) */}
      {isVolunteer && activeTask && (
        <div className="rounded-2xl border-2 border-amber-300 bg-amber-50/60 p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-amber-200">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-600 text-white shadow-xs">
                <Truck className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider bg-amber-200 text-amber-900 px-2 py-0.5 rounded-md">
                    Active Mission
                  </span>
                  <StatusBadge status={activeTask.status} size="sm" />
                  {activeTask.isDisasterMode && (
                    <span className="text-[10px] font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-md">
                      Disaster Relief
                    </span>
                  )}
                </div>
                <h3 className="text-sm font-extrabold text-[#182B25] mt-0.5">
                  {activeTask.title} ({activeTask.quantityDescription})
                </h3>
              </div>
            </div>

            {/* Stepper advancement buttons */}
            <div className="flex flex-wrap items-center gap-2">
              {activeTask.status === 'ACCEPTED' && (
                <button
                  onClick={() => handleTaskAction(activeTask.id, 'ARRIVED_PICKUP')}
                  className="rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] transition-all shadow-xs"
                >
                  Mark Arrived at Pickup
                </button>
              )}
              {activeTask.status === 'ARRIVED_PICKUP' && (
                <button
                  onClick={() => handleTaskAction(activeTask.id, 'PICKED_UP')}
                  className="rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] transition-all shadow-xs"
                >
                  Confirm Food Picked Up
                </button>
              )}
              {activeTask.status === 'PICKED_UP' && (
                <button
                  onClick={() => handleTaskAction(activeTask.id, 'ARRIVED_DELIVERY')}
                  className="rounded-xl bg-blue-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs"
                >
                  Mark Arrived at Drop-off
                </button>
              )}
              {activeTask.status === 'ARRIVED_DELIVERY' && (
                <button
                  onClick={() => handleTaskAction(activeTask.id, 'DELIVERED')}
                  className="rounded-xl bg-emerald-700 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-emerald-800 transition-all shadow-xs"
                >
                  Confirm Final Delivery
                </button>
              )}
              <Link
                to="/deliveries/active"
                className="rounded-xl bg-white border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
              >
                View Full Route
              </Link>
            </div>
          </div>

          {/* Courier Progress Stepper */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { id: 'ACCEPTED', label: '1. Mission Accepted' },
              { id: 'ARRIVED_PICKUP', label: '2. At Donor Kitchen' },
              { id: 'PICKED_UP', label: '3. En Route to Shelter' },
              { id: 'ARRIVED_DELIVERY', label: '4. At Destination' },
            ].map((step, idx) => {
              const statusOrder: DeliveryTaskStatus[] = ['ACCEPTED', 'ARRIVED_PICKUP', 'PICKED_UP', 'ARRIVED_DELIVERY', 'DELIVERED'];
              const currentIndex = statusOrder.indexOf(activeTask.status);
              const isPast = currentIndex >= idx;
              const isCurrent = activeTask.status === step.id;
              return (
                <div
                  key={step.id}
                  className={`rounded-xl p-2.5 text-xs font-semibold border ${
                    isCurrent
                      ? 'bg-amber-100 border-amber-300 text-amber-900 font-bold shadow-xs'
                      : isPast
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      : 'bg-white border-[#E5EAE7] text-[#94A3B8]'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    {isPast && !isCurrent ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                    ) : (
                      <span className={`h-2 w-2 rounded-full shrink-0 ${isCurrent ? 'bg-amber-600 animate-pulse' : 'bg-slate-300'}`} />
                    )}
                    <span className="truncate">{step.label}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-[#182B25] bg-white rounded-xl p-3 border border-amber-200">
            <div>
              <span className="font-bold text-[#64748B]">Pickup Address:</span>
              <p className="mt-0.5 font-medium">{activeTask.pickupAddress}</p>
            </div>
            <div>
              <span className="font-bold text-[#64748B]">Destination Shelter:</span>
              <p className="mt-0.5 font-medium">{activeTask.deliveryAddress}</p>
            </div>
          </div>
        </div>
      )}

      {/* 5. Food Provider Module Section (Section 5) */}
      {isFoodProvider && (
        <div className="rounded-2xl bg-white border border-[#E5EAE7] shadow-xs overflow-hidden">
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-[#E5EAE7] bg-[#F8FAF9]/50">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#182B25] flex items-center gap-2">
                  Food Provider Operations
                  <span className="rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold">
                    {displayListings.length} Listings
                  </span>
                </h2>
                <p className="text-xs text-[#64748B]">Surplus inventory, pickup dispatch, and food safety standards</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/food/add"
                className="hidden sm:inline-flex items-center gap-1 rounded-xl bg-[#16866A] px-3 py-1.5 text-xs font-bold text-white hover:bg-[#09664F]"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Add Food</span>
              </Link>
              <button
                onClick={() => setProviderExpanded(!providerExpanded)}
                className="p-1.5 text-[#64748B] hover:text-[#182B25] rounded-lg hover:bg-white"
              >
                {providerExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {providerExpanded && (
            <div className="p-4 md:p-5 space-y-5">
              {/* Active Listings Grid */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
                    My Food Listings Inventory
                  </h3>
                  <Link to="/food/listings" className="text-xs font-bold text-[#16866A] hover:underline flex items-center gap-1">
                    <span>Manage all listings</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {displayListings.slice(0, 3).map((item) => (
                    <div
                      key={item.id}
                      className="rounded-xl border border-[#E5EAE7] p-3.5 bg-white hover:border-emerald-300 transition-all flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <StatusBadge status={item.status} size="sm" />
                          <span className="text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
                            {item.quantity} {item.unit}
                          </span>
                        </div>
                        <h4 className="mt-2 text-xs font-bold text-[#182B25] line-clamp-1">{item.name}</h4>
                        <p className="text-[11px] text-[#64748B] line-clamp-1 mt-0.5">{item.storageRequirements}</p>
                      </div>

                      <div className="mt-3 pt-2.5 border-t border-[#E5EAE7] flex items-center justify-between text-[11px] text-[#64748B]">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-amber-500" />
                          <span>Safe until {new Date(item.safeUntil).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </span>
                        <Link to="/food/pickups" className="font-semibold text-[#16866A] hover:underline">
                          View
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Food Safety & Pickup Status Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Food Safety Information Card */}
                <div className="rounded-xl bg-emerald-50/50 border border-emerald-200 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-700" />
                    <h4 className="text-xs font-bold text-emerald-900">Food Safety & Compliance Guidelines</h4>
                  </div>
                  <ul className="text-[11px] text-emerald-800/90 space-y-1.5 list-disc list-inside">
                    <li>Maintain hot-holding cooked dishes at ≥ 60°C until volunteer collection.</li>
                    <li>Refrigerate perishables (dairy, meat) at ≤ 4°C with certified allergen labels.</li>
                    <li>Ensure airtight eco-friendly packaging for motorcycle courier transport.</li>
                  </ul>
                </div>

                {/* Donation Impact Summary */}
                <div className="rounded-xl bg-[#F8FAF9] border border-[#E5EAE7] p-4 flex flex-col justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-[#182B25] mb-1">Environmental & Community Impact</h4>
                    <p className="text-[11px] text-[#64748B]">
                      Your donations diverted an estimated <strong>{Math.round(totalDonatedKg || 120)} kg</strong> of food from landfill waste, avoiding ~<strong>{Math.round((totalDonatedKg || 120) * 2.5)} kg CO₂e</strong> emissions.
                    </p>
                  </div>
                  <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#E5EAE7]">
                    <span className="text-xs font-semibold text-emerald-700">~260 Resident Meals Served</span>
                    <Link to="/food/history" className="text-xs font-bold text-[#16866A] hover:underline">
                      Impact Report
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 6. NGO / Recipient Module Section (Section 5) */}
      {isRecipient && (
        <div className="rounded-2xl bg-white border border-[#E5EAE7] shadow-xs overflow-hidden">
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-[#E5EAE7] bg-[#F8FAF9]/50">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#182B25] flex items-center gap-2">
                  NGO & Community Recipient Operations
                  <span className="rounded-full bg-blue-100 text-blue-800 px-2 py-0.5 text-[10px] font-bold">
                    {requests.length} Requests Logged
                  </span>
                </h2>
                <p className="text-xs text-[#64748B]">Manage food requisitions, available donor surplus, and incoming couriers</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/requests/create"
                className="hidden sm:inline-flex items-center gap-1 rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-700"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Create Request</span>
              </Link>
              <button
                onClick={() => setRecipientExpanded(!recipientExpanded)}
                className="p-1.5 text-[#64748B] hover:text-[#182B25] rounded-lg hover:bg-white"
              >
                {recipientExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {recipientExpanded && (
            <div className="p-4 md:p-5 space-y-5">
              {/* Requests & Incoming Deliveries Split */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                {/* My Active Resource Requests */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
                      My Active Requests ({activeRecipientRequests.length})
                    </h3>
                    <Link to="/requests/my-requests" className="text-xs font-bold text-blue-600 hover:underline">
                      View all
                    </Link>
                  </div>

                  <div className="space-y-2.5">
                    {requests.slice(0, 3).map((req) => (
                      <div
                        key={req.id}
                        className="rounded-xl border border-[#E5EAE7] p-3 hover:bg-[#F8FAF9] transition-colors flex items-center justify-between"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-xs font-bold text-[#182B25]">{req.itemName}</h4>
                            <StatusBadge status={req.priority} size="sm" />
                          </div>
                          <p className="text-[11px] text-[#64748B] mt-0.5">
                            {req.requestedQuantity} {req.unit} • Impact: ~{req.peopleImpacted || 40} people
                          </p>
                        </div>
                        <StatusBadge status={req.status} size="sm" />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Incoming Deliveries Tracker */}
                <div className="lg:col-span-5 rounded-xl border border-blue-200 bg-blue-50/40 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Truck className="h-4 w-4 text-blue-700" />
                      <h3 className="text-xs font-bold text-blue-900">Incoming Shipments</h3>
                    </div>
                    <span className="text-[11px] font-semibold text-blue-700">{incomingDeliveries.length} in transit</span>
                  </div>

                  <div className="space-y-2.5">
                    {incomingDeliveries.slice(0, 2).map((del) => (
                      <div key={del.id} className="rounded-xl bg-white p-3 border border-blue-100 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#182B25]">{del.title}</span>
                          <StatusBadge status={del.status} size="sm" />
                        </div>
                        <p className="text-[11px] text-[#64748B] mt-1">
                          Courier: {del.volunteerName || 'Volunteer Assigned'} • {del.quantityDescription}
                        </p>
                        {del.status === 'ARRIVED_DELIVERY' && (
                          <button
                            onClick={() => handleConfirmReceipt(del.id)}
                            className="mt-2 w-full rounded-lg bg-emerald-600 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 transition-colors"
                          >
                            Confirm Receipt
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Available Food in Community Catalog Preview */}
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
                    Surplus Food Available in Moratuwa Area
                  </h3>
                  <Link to="/requests/available-food" className="text-xs font-bold text-blue-600 hover:underline">
                    Browse full catalog
                  </Link>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  {listings.filter((f) => f.status === 'available').slice(0, 4).map((f) => (
                    <div key={f.id} className="rounded-xl border border-[#E5EAE7] p-3 bg-white hover:border-blue-300 transition-all">
                      <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md">
                        {f.category}
                      </span>
                      <h4 className="mt-1 text-xs font-bold text-[#182B25] line-clamp-1">{f.name}</h4>
                      <p className="text-[11px] text-[#64748B] mt-0.5">{f.quantity} {f.unit} • {f.providerName}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 7. Volunteer Module Section (Section 5) */}
      {isVolunteer && (
        <div className="rounded-2xl bg-white border border-[#E5EAE7] shadow-xs overflow-hidden">
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-[#E5EAE7] bg-[#F8FAF9]/50">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
                <HandHeart className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#182B25] flex items-center gap-2">
                  Volunteer Courier Operations
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${isOnline ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                    {isOnline ? 'Active Online' : 'Offline'}
                  </span>
                </h2>
                <p className="text-xs text-[#64748B]">Vehicle: {volunteer?.vehicleType || 'Motorcycle'} • Food rescue transport missions</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={toggleAvailability}
                className={`hidden sm:inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-bold transition-all ${
                  isOnline
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                    : 'border-slate-300 bg-slate-100 text-slate-700'
                }`}
              >
                <span>{isOnline ? 'Go Offline' : 'Go Online'}</span>
              </button>
              <button
                onClick={() => setVolunteerExpanded(!volunteerExpanded)}
                className="p-1.5 text-[#64748B] hover:text-[#182B25] rounded-lg hover:bg-white"
              >
                {volunteerExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {volunteerExpanded && (
            <div className="p-4 md:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
                  Available Transport Missions ({availableTasks.length})
                </h3>
                <Link to="/volunteer/tasks" className="text-xs font-bold text-amber-700 hover:underline">
                  View map & details
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {availableTasks.slice(0, 4).map((task) => (
                  <div
                    key={task.id}
                    className="rounded-xl border border-[#E5EAE7] p-3.5 bg-white hover:border-amber-300 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md">
                          {task.quantityDescription}
                        </span>
                        {task.isDisasterMode ? (
                          <span className="text-[10px] font-extrabold text-red-700 bg-red-100 px-2 py-0.5 rounded-md flex items-center gap-1">
                            <Flame className="h-3 w-3" /> Relief Priority
                          </span>
                        ) : (
                          <StatusBadge status={task.priority} size="sm" />
                        )}
                      </div>
                      <h4 className="mt-2 text-xs font-bold text-[#182B25]">{task.title}</h4>
                      <div className="mt-2 text-[11px] text-[#64748B] space-y-1">
                        <p className="flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-emerald-600 shrink-0" />
                          <span className="truncate">From: {task.pickupAddress}</span>
                        </p>
                        <p className="flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-blue-600 shrink-0" />
                          <span className="truncate">To: {task.deliveryAddress}</span>
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-[#E5EAE7] flex items-center justify-between">
                      <span className="text-[11px] font-medium text-[#64748B]">
                        Est. Transit: ~{task.estimatedDurationMin || 25} mins
                      </span>
                      <button
                        onClick={() => handleTaskAction(task.id, 'ACCEPTED')}
                        className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-700 transition-colors"
                      >
                        Accept Mission
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 8. Recent Activity Stream */}
      <div className="rounded-2xl bg-white border border-[#E5EAE7] p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-[#16866A]" />
            <h3 className="text-sm font-bold text-[#182B25]">Recent Community Activity & Audit Logs</h3>
          </div>
          <span className="text-xs text-[#64748B]">Live In-Memory Events</span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {activities.slice(0, 6).map((log) => (
            <div key={log.id} className="rounded-xl border border-[#E5EAE7] p-3 bg-[#F8FAF9]/60">
              <div className="flex items-center justify-between text-[10px] text-[#64748B] mb-1">
                <span className="font-bold text-[#182B25]">{log.userName}</span>
                <span>{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p className="text-xs font-medium text-[#182B25] line-clamp-2">{log.details}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
