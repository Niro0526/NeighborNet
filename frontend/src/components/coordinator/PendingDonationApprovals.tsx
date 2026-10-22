import React, { useEffect, useState } from 'react';
import { Allocation } from '../../types';
import { allocationService } from '../../services/allocationService';
import { isApiMode } from '../../services/apiClient';
import { useLivePolling } from '../../hooks';

export const PendingDonationApprovals: React.FC = () => {
  const [pending,setPending]=useState<Allocation[]>([]);
  const [busy,setBusy]=useState('');
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const load=async()=>{if (!isApiMode()) return;try {setPending((await allocationService.getAllocations()).filter(a=>a.status==='proposed'));setError('');}catch(err:any){setError(err.message || 'Could not load NGO acceptances.');}};
  useEffect(()=>{load();},[]);
  useLivePolling({fetcher:load,enabled:isApiMode(),intervalMs:10000});
  if (!isApiMode()) return null;
  const approve=async(id:string)=>{setBusy(id);setError('');setMessage('');try{await allocationService.updateAllocationStatus(id,'approved');setMessage(`Allocation ${id} approved and saved.`);await load();}catch(err:any){setError(err.message || 'Approval was not saved.');}finally{setBusy('');}};
  return <section className="rounded-2xl border border-[#E5EAE7] bg-white p-4 space-y-2">
    <h3 className="text-sm font-bold">NGO acceptances awaiting approval ({pending.length})</h3>
    {error && <p role="alert" className="text-xs text-red-700">{error}</p>}{message && <p role="status" className="text-xs text-[#16866A]">{message}</p>}
    {pending.length===0 && <p className="text-xs text-[#64748B]">No pending NGO acceptances.</p>}
    {pending.map(a=><div key={a.id} className="rounded-lg border p-3 text-xs space-y-1"><p className="font-bold">{a.id} · {a.recipientName}</p><p>{a.foodListingName} · {a.quantityAllocated} {a.unit} · {a.foodListingId}</p><button disabled={!!busy} onClick={()=>approve(a.id)} className="rounded bg-[#16866A] px-3 py-1.5 font-bold text-white disabled:opacity-50">{busy===a.id ? 'Saving approval…' : `Approve ${a.id}`}</button></div>)}
  </section>;
};
