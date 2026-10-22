import React, { useState } from 'react';
import { allocationService } from '../../services/allocationService';

export type MatchedOffer = {resourceId: string; requestId: string; recipientName: string; quantity: number; unit: string};
export const AcceptMatchedOffer: React.FC<{offers: MatchedOffer[]; onAccepted: () => Promise<void>}> = ({offers,onAccepted}) => {
  const [requestId,setRequestId]=useState('');
  const [quantity,setQuantity]=useState('');
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const offer=offers.find(o=>o.requestId===requestId) || offers[0];
  if (!offer) return message ? <p role="status" className="mt-2 text-[11px] text-[#16866A]">{message}</p> : null;
  const accept=async () => {
    setBusy(true);setMessage('');setError('');
    try {
      const amount=quantity==='' ? offer.quantity : Number(quantity);
      if (!Number.isFinite(amount) || amount<=0 || amount>offer.quantity) throw new Error('Enter a quantity within the matched offer.');
      if (Math.abs(amount-Math.round(amount*100)/100)>1e-9) throw new Error('Use at most two decimal places.');
      const allocation=await allocationService.createAllocation({resource_id:offer.resourceId,request_id:offer.requestId,allocated_quantity:amount});
      setMessage(`${allocation.id}: NGO acceptance saved; awaiting Coordinator approval.`);
      setQuantity('');
      await onAccepted();
    } catch (err:any) {setError(err.message || 'Acceptance was not saved.');}
    finally {setBusy(false);}
  };
  return <div className="mt-2 space-y-1 text-[11px]">
    <label>Matched NGO request
      <select aria-label={`Matched request for ${offer.resourceId}`} className="block w-full rounded border p-1" value={offer.requestId} onChange={e=>{setRequestId(e.target.value);setQuantity('');}}>
        {offers.map(o=><option key={o.requestId} value={o.requestId}>{o.requestId} · {o.recipientName}</option>)}
      </select>
    </label>
    <label>Accept quantity ({offer.unit}, maximum {offer.quantity})<input aria-label={`Accept quantity for ${offer.resourceId}`} className="block w-full rounded border p-1" type="number" min="0.01" step="0.01" max={offer.quantity} value={quantity==='' ? offer.quantity : quantity} onChange={e=>setQuantity(e.target.value)}/></label>
    <button disabled={busy} onClick={accept} className="rounded bg-[#16866A] px-2 py-1.5 font-bold text-white disabled:opacity-50">{busy ? 'Saving acceptance…' : 'Accept matched offer'}</button>
    {message && <p role="status">{message}</p>}{error && <p role="alert" className="text-red-700">{error}</p>}
  </div>;
};
