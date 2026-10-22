import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../services/apiClient';
import { intelligenceService, RecommendationBatchItem } from '../../services/intelligenceService';
import { useLivePolling } from '../../hooks';
import { MatchingPreferences } from '../../components/coordinator/MatchingPreferences';
import { MatchingRecovery } from '../../components/coordinator/MatchingRecovery';

interface Pair { resource_id: string; resource_name: string; provider_name: string; request_id: string; request_item_name: string; recipient_name: string; available_quantity: number; remaining_quantity: number; compatible_quantity: number; unit: string; request_unit: string; distance_km: number | null; distance_type: string; constraints_satisfied: string[]; missing_information: string[]; reasons_rejected: string[]; volunteers: { id: string; name: string; capacity: number }[] }
interface Screening { matches: Pair[]; rejected_pairs: Pair[]; empty_reason: string | null; inventory: { id: string; name: string; unit: string; available: number; reserved: number; status: string }[]; demand: { id: string; name: string; recipient: string; unit: string; remaining: number; status: string }[] }
const button = 'rounded-lg bg-[#16866A] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40 hover:bg-[#09664F]';
const card = 'rounded-2xl border border-[#E5EAE7] bg-white p-4';

export function SmartMatchingPage() {
  const [mode, setMode] = useState<'NORMAL' | 'DISASTER'>('NORMAL');
  const [screening, setScreening] = useState<Screening | null>(null);
  const [batches, setBatches] = useState<RecommendationBatchItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [timeLimit, setTimeLimit] = useState(10);
  const refresh = useCallback(async () => {
    const [screen, plans] = await Promise.all([apiClient.get<Screening>('/intelligence/matches/', { params: { mode } }), intelligenceService.getBatches()]);
    setScreening(screen.data); setBatches(plans.filter(p => p.mode === mode)); setError('');
  }, [mode]);
  useEffect(() => { setScreening(null); refresh().catch(e => setError(e.message)); }, [refresh]);
  useLivePolling(refresh, { intervalMs: 15000, onError: e => setError(e.message || 'Unable to refresh matching data.') });
  async function action(work: () => Promise<unknown>, message: string) {
    if (busy) return;
    setBusy(true); setError(''); setNotice('');
    try { await work(); setNotice(message); await refresh(); } catch (e: any) { setError(e.message || 'Matching operation failed.'); } finally { setBusy(false); }
  }
  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold text-[#182B25]">Smart matching</h1><p className="mt-1 text-sm text-slate-600">Recorded NGO demand, live inventory and verified couriers. Recommendations do not reserve stock until approval.</p></div><button className={button} disabled={busy} onClick={() => void action(refresh, 'Database state refreshed.')}>Refresh</button></div>
    <div className="flex flex-wrap items-center gap-3"><label className="text-sm">Operating mode <select className="rounded-lg border p-2" value={mode} onChange={e => setMode(e.target.value as 'NORMAL' | 'DISASTER')}><option value="NORMAL">Normal food rescue</option><option value="DISASTER">Disaster response</option></select></label><Link className="text-sm font-semibold text-[#16866A] underline" to="/community-food">Individual claims: separate approval workflow</Link><Link className="text-sm underline" to="/admin/disasters">Disaster operations</Link></div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-800">{error}</p>}
    {notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-emerald-800">{notice}</p>}
    <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">Distances are straight-line estimates from recorded pickup and delivery coordinates. Missing preferences and route timing are shown explicitly; no diet, unit conversion or road travel time is inferred.</p>
    {!screening ? <p>Loading PostgreSQL records...</p> : <>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className={card}><h2 className="mb-2 font-bold">Inventory ({screening.inventory.length})</h2>{!screening.inventory.length && <p className="text-sm text-slate-500">No supply records in this mode.</p>}<div className="max-h-60 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th>Food</th><th>Available</th><th>Reserved</th><th>Status</th></tr></thead><tbody>{screening.inventory.map(r => <tr key={r.id} className="border-t"><td className="py-2">{r.name}<span className="block text-xs text-slate-500">{r.id}</span></td><td>{r.available} {r.unit}</td><td>{r.reserved} {r.unit}</td><td>{r.status}</td></tr>)}</tbody></table></div></section>
        <section className={card}><h2 className="mb-2 font-bold">Open NGO demand ({screening.demand.length})</h2>{!screening.demand.length && <p className="text-sm text-slate-500">No open NGO requests in this mode.</p>}{screening.demand.map(q => <p className="border-t py-2 text-sm" key={q.id}>{q.recipient}: {q.name} · {q.remaining} {q.unit}<span className="block text-xs text-slate-500">{q.id} · {q.status}</span></p>)}</section>
      </div>
      <section className={card}><h2 className="mb-3 text-lg font-bold">Eligible matches ({screening.matches.length})</h2>{screening.empty_reason && <p className="text-sm text-slate-600">{screening.empty_reason}</p>}
        <div className="grid gap-3 lg:grid-cols-2">{screening.matches.map(p => <article className="rounded-xl border p-3" key={p.resource_id+p.request_id}><h3 className="font-semibold">{p.resource_name} → {p.recipient_name}</h3><p className="text-sm">{p.provider_name} · {p.compatible_quantity} {p.unit} feasible per mission · {p.distance_km ?? 'Unknown'} km ({p.distance_type})</p><p className="text-xs text-slate-500">{p.resource_id} / {p.request_id} · Available {p.available_quantity} {p.unit} · Demand {p.remaining_quantity} {p.request_unit}</p><p className="mt-1 text-xs">Couriers: {p.volunteers.map(v => `${v.name} (up to ${v.capacity} ${p.unit})`).join(', ')}</p><details className="mt-2 text-xs"><summary className="cursor-pointer">Verified checks and missing information</summary><ul className="mt-1 list-inside list-disc">{p.constraints_satisfied.map((s,i) => <li key={i}>{s}</li>)}</ul>{p.missing_information.map((s,i) => <p className="mt-1 text-amber-800" key={i}>Unknown: {s}</p>)}</details></article>)}</div>
      </section>
      <details className={card}><summary className="cursor-pointer font-bold">Rejected pairs ({screening.rejected_pairs.length})</summary><div className="mt-3 space-y-3">{screening.rejected_pairs.map(p => <article className="border-t pt-2 text-sm" key={p.resource_id+p.request_id}><h3 className="font-semibold">{p.resource_name} → {p.recipient_name}</h3><p className="text-xs text-slate-500">{p.resource_id} / {p.request_id} · {p.available_quantity} {p.unit} supply / {p.remaining_quantity} {p.request_unit} demand{p.distance_km != null && ` · ${p.distance_km} km (${p.distance_type})`}</p><ul className="list-inside list-disc text-red-800">{p.reasons_rejected.map((reason,i) => <li key={i}>{reason}</li>)}</ul>{p.missing_information.map((s,i) => <p className="text-xs text-amber-800" key={i}>Missing information: {s}</p>)}</article>)}</div></details>
    </>}
    <section className={card}><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-bold">Google OR-Tools CP-SAT</h2><p className="text-sm text-slate-600">Joint supply, demand and courier capacity constraints. Partial quantities only where permitted.</p></div><div className="flex items-center gap-2"><label className="text-xs">Time limit (seconds)<input className="ml-2 w-16 rounded border p-2" type="number" min={1} max={60} value={timeLimit} onChange={e => setTimeLimit(Number(e.target.value))} /></label><button className={button} disabled={busy || timeLimit < 1 || timeLimit > 60} onClick={() => void action(() => intelligenceService.runOptimization({ method: 'ORTOOLS_CPSAT', mode, time_limit_seconds: timeLimit }), 'Solver completed. Review the plan and missing information before approval.')}>{busy ? 'Working...' : 'Generate plan'}</button></div></div></section>
    <section className="space-y-3"><h2 className="text-lg font-bold">Recommendation plans</h2>{!batches.length && <p className="text-sm text-slate-500">No plans recorded. Generate a plan from current data.</p>}{batches.map(batch => <article className={card} key={batch.id}>
      <div className="flex flex-wrap justify-between gap-2"><h3 className="font-bold">{batch.id} · {batch.status}</h3><p className="text-sm">Solver: {batch.solver_status} · {batch.runtime_ms.toFixed(1)} ms · {new Date(batch.created_at).toLocaleString()}</p></div>
      {batch.status === 'APPLIED' && <p className="mt-2 text-xs text-slate-500">Historical allocation record; this is not a current matching recommendation.</p>}
      {!batch.solver_metadata.units && <p className="mt-2 text-xs text-amber-800">Legacy plan generated before the current checks. Any pending application requires full revalidation.</p>}
      {batch.solver_metadata.empty_reason && <p className="mt-2 text-sm text-amber-800">{batch.solver_metadata.empty_reason}</p>}
      <div className="my-3 flex flex-wrap gap-3">{Object.entries(batch.solver_metadata.units || {}).map(([unit, raw]) => { const u = raw as any; return <p className="rounded-lg bg-slate-50 p-2 text-xs" key={unit}>{unit}: allocated {u.allocated} · remaining stock {u.remaining_inventory} · unmet demand {u.unmet_demand}</p>; })}</div>
      <div className="space-y-2">{batch.recommendations.map(r => <div key={r.id} className="rounded-lg border p-3 text-sm"><p className="font-semibold">{r.resourceName} → {r.recipientName} · {r.allocated_quantity} {r.unit}</p><p>{r.estimated_distance_km} km ({r.distance_type}) · Courier: {r.volunteerName || 'No verified assignment'}</p>{r.volunteer_feasibility_notes && <p className="text-xs text-amber-800">{r.volunteer_feasibility_notes}</p>}{r.createdAllocationId && <p className="text-xs">Persisted allocation: {r.createdAllocationId}</p>}</div>)}</div>
      {(batch.status === 'PENDING_APPROVAL' || batch.status === 'DRAFT') && <div className="mt-3 flex gap-2"><button className={button} disabled={busy || !batch.recommendations.length || !['OPTIMAL','FEASIBLE'].includes(batch.solver_status)} onClick={() => void action(() => intelligenceService.approveBatch(batch.id), 'Approved and committed atomically. Provider, NGO and courier dashboards now reflect the allocations.')}>Approve and allocate</button><button className="rounded-lg border px-4 py-2 text-sm" disabled={busy} onClick={() => void action(() => intelligenceService.rejectBatch(batch.id, 'Rejected by coordinator'), 'Plan rejected. No inventory reserved.')}>Reject</button></div>}
      {batch.status === 'APPROVED' && <button disabled={busy} className={button} onClick={() => void action(() => intelligenceService.applyBatch(batch.id), 'Existing approved plan committed after revalidation.')}>Commit existing approval</button>}
    </article>)}</section>
    <MatchingPreferences coordinator />
    <MatchingRecovery />
  </div>;
}
