import React, { useEffect, useState } from 'react';
import { PageHeader } from '../../components/common/PageHeader';
import { StatCard } from '../../components/common/StatCard';
import { requestService } from '../../services/requestService';
import { foodService } from '../../services/foodService';
import { deliveryService } from '../../services/deliveryService';
import { ResourceRequest, FoodListing, DeliveryTask } from '../../types';
import { PlusCircle, ShoppingBag, Truck, CheckCircle2, Clock, MapPin, Flame } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth, useOperational } from '../../hooks';

export const RecipientDashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { isDisasterMode, activeDisaster } = useOperational();
  const [requests, setRequests] = useState<ResourceRequest[]>([]);
  const [availableFood, setAvailableFood] = useState<FoodListing[]>([]);
  const [incomingDeliveries, setIncomingDeliveries] = useState<DeliveryTask[]>([]);

  useEffect(() => {
    requestService.getResourceRequests().then(setRequests);
    foodService.getFoodListings().then((all) => {
      setAvailableFood(all.filter((f) => f.status === 'available'));
    });
    deliveryService.getDeliveryTasks().then((all) => {
      setIncomingDeliveries(all.filter((t) => t.status === 'ACCEPTED' || t.status === 'ARRIVED_PICKUP' || t.status === 'PICKED_UP'));
    });
  }, []);

  const activeRequestsCount = requests.filter((r) => r.status === 'pending' || r.status === 'allocated' || r.status === 'partially_fulfilled').length;

  const totalReceivedKg = requests
    .filter((r) => r.status === 'fulfilled' || r.status === 'allocated' || r.status === 'partially_fulfilled')
    .reduce((acc, r) => acc + (r.unit === 'kg' ? (r.fulfilledQuantity ?? 0) : (r.fulfilledQuantity ?? 0) * 0.4), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${currentUser.name}!`}
        subtitle="Request essential food rations, track incoming volunteer couriers, and review distribution."
        badge={
          isDisasterMode ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-extrabold text-red-700 animate-pulse border border-red-200">
              <Flame className="h-3.5 w-3.5" />
              Disaster Relief Active
            </span>
          ) : undefined
        }
        action={
          <Link
            to="/recipient/create-request"
            className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create Resource Request</span>
          </Link>
        }
      />

      {/* Disaster Mode Contextual Notice */}
      {isDisasterMode && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
          <Flame className="h-5 w-5 text-red-600 shrink-0 mt-0.5 animate-bounce" />
          <div className="text-xs">
            <span className="font-bold text-red-800">
              Disaster Emergency Response Active — {activeDisaster?.title || 'Monsoon Flash Floods'}
            </span>
            <p className="text-red-700/80 mt-0.5">
              Urgent relief allocations (drinking water cans, ready rations, baby milk) are currently fast-tracked for distribution to verified shelters.
            </p>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Requests"
          value={activeRequestsCount}
          subtitle="Awaiting match / in progress"
          icon={ShoppingBag}
          variant="emerald"
        />
        <StatCard
          title="Incoming Deliveries"
          value={incomingDeliveries.length}
          subtitle="En route to your facility"
          icon={Truck}
          variant="blue"
        />
        <StatCard
          title="Received Supply"
          value={`${Math.round(totalReceivedKg)} kg`}
          subtitle="Fed resident meals"
          icon={CheckCircle2}
          variant="amber"
        />
        <StatCard
          title="Total Community Requests"
          value={requests.length}
          subtitle="Cumulative logged"
          icon={Clock}
          variant="default"
        />
      </div>

      {/* Incoming Delivery Alert if any */}
      {incomingDeliveries.length > 0 && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/60 p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-xs">
                <Truck className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-800 bg-blue-100 px-2 py-0.5 rounded-md">
                  Active Courier En Route
                </span>
                <h4 className="mt-1 text-sm font-bold text-[#182B25]">{incomingDeliveries[0].title}</h4>
                <p className="text-xs text-[#64748B]">
                  Volunteer: <span className="font-semibold text-[#182B25]">{incomingDeliveries[0].volunteerName || 'Assigned Courier'}</span> • Est. distance: {incomingDeliveries[0].estimatedDistanceKm} km
                </p>
              </div>
            </div>
            <Link
              to="/recipient/deliveries"
              className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 transition-colors"
            >
              Track Courier Status
            </Link>
          </div>
        </div>
      )}

      {/* Available Food Offers from Local Donors */}
      <div className="rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
          <div>
            <h3 className="text-sm font-bold text-[#182B25]">Available Surplus Food Offers</h3>
            <p className="text-xs text-[#64748B]">Nearby restaurants and bakeries with surplus food ready for claim</p>
          </div>
          <Link to="/recipient/available-food" className="text-xs font-semibold text-[#16866A] hover:underline">
            Browse All ({availableFood.length})
          </Link>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableFood.map((food) => (
            <div key={food.id} className="rounded-2xl border border-[#E5EAE7] p-4 bg-[#F8FAF9] card-hover flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-md">
                    {food.quantity} {food.unit}
                  </span>
                  <span className="text-[10px] text-amber-700 font-semibold flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Expires {new Date(food.safeUntil).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <h4 className="mt-2 text-xs font-bold text-[#182B25] line-clamp-1">{food.name}</h4>
                <p className="text-[11px] text-[#64748B] mt-0.5 flex items-center gap-1">
                  <MapPin className="h-3 w-3 text-[#64748B]" />
                  {food.providerName}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#E5EAE7] flex items-center justify-between">
                <span className="text-[10px] text-[#64748B]">{food.storageRequirements}</span>
                <Link
                  to="/recipient/create-request"
                  className="rounded-lg bg-[#16866A] px-3 py-1 text-xs font-bold text-white hover:bg-[#09664F] transition-colors"
                >
                  Request Allocation
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
