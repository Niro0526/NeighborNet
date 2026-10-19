import React, { useEffect, useState } from 'react';
import { PageHeader } from '../../components/common/PageHeader';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { foodService } from '../../services/foodService';
import { FoodListing } from '../../types';
import { PlusCircle, Package, Truck, CheckCircle2, Clock, AlertCircle, Flame } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth, useOperational } from '../../hooks';

export const ProviderDashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { isDisasterMode, activeDisaster } = useOperational();
  const [listings, setListings] = useState<FoodListing[]>([]);

  useEffect(() => {
    foodService.getFoodListings().then(setListings);
  }, []);

  const totalDonatedKg = listings
    .filter((l) => l.status === 'collected')
    .reduce((acc, l) => acc + (l.unit === 'kg' ? l.quantity : l.quantity * 0.4), 0);

  const activeCount = listings.filter((l) => l.status === 'available' || l.status === 'reserved').length;
  const collectedCount = listings.filter((l) => l.status === 'collected').length;
  const pendingPickupCount = listings.filter((l) => l.status === 'reserved').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${currentUser.name}!`}
        subtitle="Track your surplus food donations, schedule volunteer pickups, and verify safe deliveries."
        badge={
          isDisasterMode ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-extrabold text-red-700 animate-pulse border border-red-200">
              <Flame className="h-3.5 w-3.5" />
              Disaster Protocol
            </span>
          ) : undefined
        }
        action={
          <Link
            to="/provider/add-food"
            className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Add Surplus Food</span>
          </Link>
        }
      />

      {/* Contextual Disaster Relief Emergency Banner */}
      {isDisasterMode && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
          <Flame className="h-5 w-5 text-red-600 shrink-0 mt-0.5 animate-bounce" />
          <div className="text-xs">
            <span className="font-bold text-red-800">
              Emergency Disaster Protocol Active — {activeDisaster?.title || 'Monsoon Flash Floods'}
            </span>
            <p className="text-red-700/80 mt-0.5">
              High-priority demand for prepared warm meals, bread, and clean drinking water in affected Moratuwa lowlands. Emergency lots receive rapid volunteer dispatch.
            </p>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Food Donated"
          value={`${Math.round(totalDonatedKg)} kg`}
          subtitle="Redirected from waste"
          icon={Package}
          variant="emerald"
        />
        <StatCard
          title="Pickups Completed"
          value={collectedCount}
          subtitle="Verified by recipient shelters"
          icon={CheckCircle2}
          variant="blue"
        />
        <StatCard
          title="Active Listings"
          value={activeCount}
          subtitle="Currently listed for matching"
          icon={Clock}
          variant="amber"
        />
        <StatCard
          title="Pending Pickups"
          value={pendingPickupCount}
          subtitle="Courier en route / reserved"
          icon={Truck}
          variant="red"
        />
      </div>

      {/* Listings Section */}
      <div className="rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
          <div>
            <h3 className="text-sm font-bold text-[#182B25]">Registered Surplus Food Listings</h3>
            <p className="text-xs text-[#64748B]">All active, reserved, and completed lots from your kitchen</p>
          </div>
          <Link to="/provider/listings" className="text-xs font-semibold text-[#16866A] hover:underline">
            View All Listings
          </Link>
        </div>

        {listings.length === 0 ? (
          <div className="py-12 text-center">
            <Package className="h-10 w-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-[#182B25]">No Surplus Food Listings Yet</h4>
            <p className="text-xs text-[#64748B] mt-1 max-w-sm mx-auto">
              Register edible cooked meals, bakery lots, or fresh produce to match with verified community shelters.
            </p>
            <Link
              to="/provider/add-food"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#09664F]"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Add Surplus Food</span>
            </Link>
          </div>
        ) : (
          <div className="mt-4 divide-y divide-[#E5EAE7]">
            {listings.map((item) => (
            <div key={item.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="h-12 w-12 rounded-xl bg-slate-100 overflow-hidden shrink-0">
                  {item.imageUrl ? (
                    <img src={item.imageUrl} alt={item.name} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs font-bold text-[#16866A]">
                      {item.quantity} {item.unit}
                    </div>
                  )}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#182B25]">{item.name}</h4>
                  <p className="text-[11px] text-[#64748B]">
                    Quantity: <span className="font-semibold text-[#182B25]">{item.quantity} {item.unit}</span> • Storage: {item.storageRequirements}
                  </p>
                  <p className="text-[10px] text-amber-700 mt-0.5">
                    Safe until: {new Date(item.safeUntil).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({new Date(item.safeUntil).toLocaleDateString()})
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <StatusBadge status={item.status} size="sm" />
                <Link
                  to="/provider/pickups"
                  className="rounded-lg border border-[#E5EAE7] px-3 py-1 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                >
                  Pickup Info
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>

      {/* Food Safety Compliance Banner */}
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-[#16866A] shrink-0 mt-0.5" />
        <div className="text-xs">
          <span className="font-bold text-[#182B25]">NeighborNet Safe Food Rescue Guidelines:</span>
          <p className="text-[#64748B] mt-0.5">
            Prepared cooked meals must be kept held at &gt;60°C or blast chilled to &lt;5°C prior to courier collection. Insulated thermal boxes are provided by our registered volunteers.
          </p>
        </div>
      </div>
    </div>
  );
};
