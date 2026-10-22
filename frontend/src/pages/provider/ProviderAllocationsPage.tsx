import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Layers, Truck, AlertCircle, CheckCircle2, Phone, RefreshCw } from 'lucide-react';
import { allocationService } from '../../services/allocationService';
import { deliveryService } from '../../services/deliveryService';
import { foodService } from '../../services/foodService';
import { Allocation, DeliveryTask, FoodListing } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { useProviderScope } from '../../hooks/useProviderScope';
import { useLivePolling } from '../../hooks';

export const ProviderAllocationsPage: React.FC = () => {
  const { providerIds, userName, ready } = useProviderScope();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get('tab') === 'pickup' ? 'pickup' : 'allocations';
  const resourceFilter = searchParams.get('resource') || '';

  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [tasks, setTasks] = useState<DeliveryTask[]>([]);
  const [listings, setListings] = useState<FoodListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<DeliveryTask | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const listingIds = useMemo(() => new Set(listings.map((item) => item.id)), [listings]);
  const listingNames = useMemo(() => new Set(listings.map((item) => item.providerName)), [listings]);

  const mineAllocations = allocations.filter((allocation) => {
    if (resourceFilter && allocation.foodListingId !== resourceFilter) return false;
    if (listingIds.size === 0) return listingNames.size === 0 ? false : listingNames.has(allocation.providerName);
    return listingIds.has(allocation.foodListingId) || listingNames.has(allocation.providerName);
  });

  const mineTasks = tasks.filter((task) => {
    if (listingIds.size === 0) return false;
    return Boolean(task.foodListingId && listingIds.has(task.foodListingId));
  });

  const load = async () => {
    setError(null);
    try {
      const [allocs, deliveryTasks, myListings] = await Promise.all([
        allocationService.getAllocations(),
        deliveryService.getDeliveryTasks(),
        foodService.getMyListings({ providerIds, providerName: userName }),
      ]);
      setAllocations(allocs);
      setTasks(deliveryTasks);
      setListings(myListings);
      const ownedIds = new Set(myListings.map((listing) => listing.id));
      const ownedTasks = deliveryTasks.filter((task) => task.foodListingId && ownedIds.has(task.foodListingId));
      setSelectedTask((previous) => ownedTasks.find((task) => task.id === previous?.id) || (tab === 'pickup' ? ownedTasks[0] : null) || null);
    } catch (err: any) {
      setError(err.message || 'Could not load allocations.');
      setAllocations([]);
      setTasks([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!ready) return;
    load();
  }, [ready, providerIds.join(','), userName]);
  useLivePolling({ fetcher: load, enabled: ready, intervalMs: 10000 });

  useEffect(() => {
    if (tab === 'pickup' && mineTasks.length > 0 && !selectedTask) {
      setSelectedTask(mineTasks[0]);
    }
  }, [tab, mineTasks, selectedTask]);

  const handleHandover = async (taskId: string) => {
    try {
      await deliveryService.updateTaskStatus(taskId, 'PICKED_UP');
      setNotice('Handover recorded. Courier is now in transit.');
      await load();
    } catch (err: any) {
      setError(err.message || 'Could not confirm handover.');
    }
  };

  const setTab = (next: 'allocations' | 'pickup') => {
    const nextParams = new URLSearchParams(searchParams);
    if (next === 'pickup') nextParams.set('tab', 'pickup');
    else nextParams.delete('tab');
    setSearchParams(nextParams);
  };

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#182B25]">Allocations</h2>
          <p className="text-xs text-[#64748B]">Matches against your surplus and live pickup status.</p>
        </div>
        <button
          type="button"
          onClick={load}
          className="inline-flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      <div className="flex gap-1 rounded-xl bg-[#E5EAE7]/50 p-1 w-fit">
        <button
          type="button"
          onClick={() => setTab('allocations')}
          className={`rounded-lg px-3 py-1.5 text-xs font-bold ${tab === 'allocations' ? 'bg-white text-[#182B25] shadow-xs' : 'text-[#64748B]'}`}
        >
          Matches
        </button>
        <button
          type="button"
          onClick={() => setTab('pickup')}
          className={`rounded-lg px-3 py-1.5 text-xs font-bold ${tab === 'pickup' ? 'bg-white text-[#182B25] shadow-xs' : 'text-[#64748B]'}`}
        >
          Track pickup
        </button>
      </div>

      {notice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="py-16 text-center">
          <div className="h-7 w-7 animate-spin rounded-full border-2 border-[#16866A] border-t-transparent mx-auto" />
          <p className="text-xs text-[#64748B] mt-2">Loading from the database...</p>
        </div>
      ) : tab === 'allocations' ? (
        <div className="rounded-2xl border border-[#E5EAE7] bg-white overflow-hidden">
          {mineAllocations.length === 0 ? (
            <div className="py-16 text-center px-4">
              <Layers className="h-10 w-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-[#182B25]">No allocations yet</h3>
              <p className="text-xs text-[#64748B] mt-1 max-w-sm mx-auto">
                When matching assigns your food to a recipient, it will appear here.
              </p>
              <Link to="/food/listings" className="mt-4 inline-block text-xs font-bold text-[#16866A]">
                View my food
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-[#E5EAE7]">
              {mineAllocations.map((allocation) => {
                const relatedTask = tasks.find(
                  (task) => task.allocationId === allocation.id || task.id === allocation.deliveryTaskId
                );
                return (
                  <div key={allocation.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-bold text-[#182B25]">{allocation.foodListingName}</h3>
                        <StatusBadge status={allocation.status} size="sm" />
                      </div>
                      <p className="text-xs text-[#64748B] mt-1">
                        {allocation.quantityAllocated} {allocation.unit} to {allocation.recipientName}
                      </p>
                    </div>
                    {relatedTask ? (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedTask(relatedTask);
                          setTab('pickup');
                        }}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-[#16866A] px-3 py-1.5 text-xs font-bold text-white"
                      >
                        <Truck className="h-3.5 w-3.5" />
                        Track pickup
                      </button>
                    ) : (
                      <span className="text-xs text-[#94A3B8]">No courier assigned yet</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            {mineTasks.length === 0 ? (
              <div className="rounded-2xl border border-[#E5EAE7] bg-white p-6 text-center">
                <Truck className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-bold text-[#182B25]">No pickups scheduled</p>
              </div>
            ) : (
              mineTasks.map((task) => (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => setSelectedTask(task)}
                  className={`w-full text-left rounded-xl border p-3 ${
                    selectedTask?.id === task.id ? 'border-[#16866A] bg-emerald-50/40' : 'border-[#E5EAE7] bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-[#182B25] truncate">{task.title}</span>
                    <StatusBadge status={task.status} size="sm" />
                  </div>
                  <p className="text-[11px] text-[#64748B] mt-1 truncate">{task.volunteerName || 'Courier pending'}</p>
                </button>
              ))
            )}
          </div>

          <div className="lg:col-span-2 rounded-2xl border border-[#E5EAE7] bg-white p-5">
            {!selectedTask ? (
              <p className="text-xs text-[#64748B]">Select a pickup to see courier status.</p>
            ) : (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-[#182B25]">{selectedTask.title}</h3>
                  <p className="text-xs text-[#64748B] mt-1">{selectedTask.quantityDescription}</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="font-bold text-[#64748B]">Pickup</p>
                    <p className="mt-0.5 text-[#182B25]">{selectedTask.pickupAddress}</p>
                  </div>
                  <div>
                    <p className="font-bold text-[#64748B]">Destination</p>
                    <p className="mt-0.5 text-[#182B25]">{selectedTask.deliveryAddress}</p>
                  </div>
                  <div>
                    <p className="font-bold text-[#64748B]">Courier</p>
                    <p className="mt-0.5 text-[#182B25]">{selectedTask.volunteerName || 'Not assigned'}</p>
                  </div>
                  <div>
                    <p className="font-bold text-[#64748B]">Status</p>
                    <div className="mt-1">
                      <StatusBadge status={selectedTask.status} size="sm" />
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedTask.pickupContactPhone && (
                    <a
                      href={`tel:${selectedTask.pickupContactPhone}`}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold"
                    >
                      <Phone className="h-3.5 w-3.5" />
                      Call
                    </a>
                  )}
                  {selectedTask.status === 'ARRIVED_PICKUP' && (
                    <button
                      type="button"
                      onClick={() => handleHandover(selectedTask.id)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-[#16866A] px-3 py-1.5 text-xs font-bold text-white"
                    >
                      Confirm handover
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
