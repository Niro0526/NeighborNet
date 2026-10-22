import React, { useEffect, useState } from 'react';
import { apiClient, isApiMode } from '../../services/apiClient';
import { useLivePolling } from '../../hooks';

type Tracking = {
  id: string; publishedAt: string; quantity: number; allocatedQuantity: number; availableQuantity: number; unit: string;
  allocations: { id: string; recipientName: string; acceptedQuantity: number | null; allocatedQuantity: number; unit: string; status: string; approvalStatus: string;
    taskId: string | null; deliveryStatus: string | null; volunteerName: string | null; pickupAddress: string | null; pickupStart: string | null; pickupEnd: string | null;
    timeline: {label: string; at: string | null}[] }[];
};

export const DonationTracking: React.FC<{listingId: string}> = ({listingId}) => {
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [error, setError] = useState('');
  const load = async () => {
    if (!isApiMode()) return;
    try {
      const response = await apiClient.get<Tracking>(`/resources/${listingId}/tracking/`);
      setTracking(response.data);
      setError('');
    } catch (err: any) { setError(err.message || 'Could not refresh donation tracking.'); }
  };
  useEffect(() => { setTracking(null); load(); }, [listingId]);
  useLivePolling({fetcher: load, enabled: isApiMode(), intervalMs: 10000});
  if (!isApiMode()) return null;
  return <div className="w-full basis-full rounded-xl border border-[#E5EAE7] bg-[#F8FAF9] p-3 space-y-2 text-xs" aria-label={`Donation tracking ${listingId}`}>
    <h4 className="font-bold text-[#182B25]">Donation tracking · {listingId}</h4>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {!tracking ? <p>Loading persisted tracking…</p> : <>
      <p>Total {tracking.quantity} {tracking.unit} · Allocated {tracking.allocatedQuantity} {tracking.unit} · <strong>Available to allocate: {tracking.availableQuantity} {tracking.unit}</strong></p>
      <p className="text-[#64748B]">Published: {new Date(tracking.publishedAt).toLocaleString()}</p>
      {tracking.allocations.length === 0 && <p>No NGO acceptance recorded yet.</p>}
      {tracking.allocations.map(allocation => <div key={allocation.id} className="rounded-lg border border-[#E5EAE7] bg-white p-3 space-y-2">
        <p className="font-bold">{allocation.recipientName} · {allocation.id}</p>
        <p>{allocation.acceptedQuantity == null ? `Allocated ${allocation.allocatedQuantity} ${allocation.unit}; NGO acceptance not recorded` : `NGO accepted ${allocation.acceptedQuantity} ${allocation.unit}`} · Allocation: {allocation.status}</p>
        <p>Coordinator approval: {allocation.approvalStatus === 'PENDING' ? 'Awaiting approval' : allocation.approvalStatus === 'APPROVED' ? 'Approved' : 'Timestamp not recorded'}</p>
        <p>Delivery: {allocation.deliveryStatus || 'No delivery task'}{allocation.taskId ? ` · ${allocation.taskId}` : ''} · Courier: {allocation.volunteerName || 'Not assigned'}</p>
        {allocation.pickupAddress && <p>Pickup: {allocation.pickupAddress} · {allocation.pickupStart && new Date(allocation.pickupStart).toLocaleString()} – {allocation.pickupEnd && new Date(allocation.pickupEnd).toLocaleString()}</p>}
        <details>
          <summary className="cursor-pointer font-semibold text-[#16866A]">Tracking timeline · {allocation.id}</summary>
          <ol className="mt-2 space-y-1 border-l-2 border-[#E5EAE7] pl-3">
            {allocation.timeline.map(step => <li key={step.label} className={step.at ? 'text-[#182B25]' : 'text-[#64748B]'}>{step.label}: {step.at ? <time dateTime={step.at}>{new Date(step.at).toLocaleString()}</time> : 'Not recorded'}</li>)}
          </ol>
        </details>
      </div>)}
    </>}
  </div>;
};
