import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Package, PlusCircle, Pencil, Ban, AlertCircle } from 'lucide-react';
import { foodService } from '../../services/foodService';
import { FoodListing } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { useProviderScope } from '../../hooks/useProviderScope';
import { DonationTracking } from '../../components/delivery/DonationTracking';

function canMutate(listing: FoodListing): boolean {
  return listing.status === 'available';
}

export const FoodListingsPage: React.FC<{ allProviders?: boolean }> = ({ allProviders = false }) => {
  const navigate = useNavigate();
  const { providerIds, userName, ready } = useProviderScope();
  const [listings, setListings] = useState<FoodListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [withdrawId, setWithdrawId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = allProviders ? await foodService.getFoodListings() : await foodService.getMyListings({ providerIds, providerName: userName });
      setListings(data);
    } catch (err: any) {
      setError(err.message || 'Could not load food listings.');
      setListings([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!ready) return;
    load();
  }, [ready, providerIds.join(','), userName]);

  const handleWithdraw = async (id: string) => {
    setBusyId(id);
    try {
      await foodService.withdrawListing(id);
      setNotice('Listing withdrawn from distribution.');
      setWithdrawId(null);
      await load();
    } catch (err: any) {
      setError(err.message || 'Withdraw failed. You may not be authorized to change this listing.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#182B25]">{allProviders ? 'Food Resources & Inventory' : 'My Food'}</h2>
          <p className="text-xs text-[#64748B]">{allProviders ? 'Persisted surplus inventory across provider organizations.' : 'Active surplus lots you can edit or withdraw while still available.'}</p>
        </div>
        {!allProviders && <Link
          to="/food/add"
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F]"
        >
          <PlusCircle className="h-4 w-4" />
          Add Surplus Food
        </Link>}
      </div>

      {notice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-[#E5EAE7] bg-white overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center">
            <div className="h-7 w-7 animate-spin rounded-full border-2 border-[#16866A] border-t-transparent mx-auto" />
            <p className="text-xs text-[#64748B] mt-2">Loading listings...</p>
          </div>
        ) : listings.length === 0 ? (
          <div className="py-16 text-center px-4">
            <Package className="h-10 w-10 text-slate-300 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-[#182B25]">No surplus listed yet</h3>
            <p className="text-xs text-[#64748B] mt-1 max-w-sm mx-auto">
              Publish a cooked meal, bakery lot, or produce listing so matching can allocate it.
            </p>
            <Link
              to="/food/add"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white"
            >
              <PlusCircle className="h-4 w-4" />
              Add Surplus Food
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-[#E5EAE7]">
            {listings.map((item) => (
              <div key={item.id} className="p-4 flex flex-col md:flex-row md:flex-wrap md:items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-[#182B25] truncate">{item.name}</h3>
                    <StatusBadge status={item.status} size="sm" />
                  </div>
                  <p className="text-[11px] text-[#64748B] mt-1">{item.id} · Created {new Date(item.createdAt).toLocaleString()}</p>
                  <p className="text-xs text-[#64748B] mt-1">
                    {item.quantity} {item.unit} · {item.storageRequirements} · Safe until{' '}
                    {new Date(item.safeUntil).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => navigate(allProviders ? '/admin/matching' : `/food/allocations?resource=${encodeURIComponent(item.id)}`)}
                    className="rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                  >
                    Allocations
                  </button>
                  {!allProviders && canMutate(item) && (
                    <>
                      <Link
                        to={`/food/add?edit=${encodeURIComponent(item.id)}`}
                        className="inline-flex items-center gap-1 rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9]"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        Edit
                      </Link>
                      <button
                        type="button"
                        disabled={busyId === item.id}
                        onClick={() => setWithdrawId(item.id)}
                        className="inline-flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                      >
                        <Ban className="h-3.5 w-3.5" />
                        Withdraw
                      </button>
                    </>
                  )}
                </div>
                {!item.isDisasterRelief && <DonationTracking listingId={item.id}/>}
              </div>
            ))}
          </div>
        )}
      </div>

      {withdrawId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xl">
            <h3 className="text-sm font-bold text-[#182B25]">Withdraw this listing?</h3>
            <p className="text-xs text-[#64748B] mt-2">
              It will leave the matching pool and cannot be allocated until listed again.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setWithdrawId(null)}
                className="rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleWithdraw(withdrawId)}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white"
              >
                Confirm withdraw
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
