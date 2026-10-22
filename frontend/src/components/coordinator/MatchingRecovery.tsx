import { useEffect, useState } from 'react';
import { deliveryService } from '../../services/deliveryService';
import { intelligenceService, DisruptionRecoveryPreview } from '../../services/intelligenceService';
import { DeliveryTask } from '../../types';

export function MatchingRecovery() {
  const [tasks, setTasks] = useState<DeliveryTask[]>([]);
  const [selected, setSelected] = useState('');
  const [reason, setReason] = useState('');
  const [event, setEvent] = useState('VOLUNTEER_UNAVAILABLE');
  const [preview, setPreview] = useState<DisruptionRecoveryPreview | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { deliveryService.getDeliveryTasks().then(rows => setTasks(rows.filter(t => !['DELIVERED','CANCELLED'].includes(t.status)))).catch(e => setMessage(e.message)); }, []);
  return <details className="rounded-2xl border bg-white p-4"><summary className="cursor-pointer font-bold">Delivery disruption and recovery</summary><form className="mt-3 flex flex-wrap items-center gap-3" onSubmit={async e => { e.preventDefault(); setBusy(true); setMessage(''); try { setPreview(await intelligenceService.previewRecovery({ task_id: selected, event_type: event, details: reason })); setMessage('Disruption recorded. Review the proposed recovery before applying.'); } catch (e: any) { setMessage(e.message); } finally { setBusy(false); } }}>
    <label className="text-sm">Active task<select required className="ml-2 rounded border p-2" value={selected} onChange={e => setSelected(e.target.value)}><option value="">Select a task</option>{tasks.map(t => <option key={t.id} value={t.id}>{t.id} — {t.title} ({t.status})</option>)}</select></label>
    <label className="text-sm">Disruption<select className="ml-2 rounded border p-2" value={event} onChange={e => setEvent(e.target.value)}>{['VOLUNTEER_UNAVAILABLE','VOLUNTEER_CANCEL','ROAD_RESTRICTION','PICKUP_DELAY','RESOURCE_WITHDRAWAL','RESOURCE_EXPIRY'].map(v => <option key={v}>{v}</option>)}</select></label>
    <label className="text-sm">Observed details<input required className="ml-2 rounded border p-2" value={reason} onChange={e => setReason(e.target.value)} /></label><button disabled={busy || !selected} className="rounded-lg bg-[#16866A] px-3 py-2 text-sm text-white disabled:opacity-40">Record and preview recovery</button>
  </form>
  {preview && <div className="mt-3 space-y-2 text-sm">{preview.replacement_options.map((o,i) => <p key={i}>{o.description}{o.feasibility_notes && ` ${o.feasibility_notes}`}</p>)}<button disabled={busy || !preview.replacement_options.some(o => ['REASSIGN_VOLUNTEER','SUBSTITUTE_RESOURCE'].includes(o.type))} className="rounded-lg border px-3 py-2 disabled:opacity-40" onClick={async () => { setBusy(true); try { const result = await intelligenceService.applyRecovery(preview.disruption_id); setMessage(result.resolution || 'Recovery applied.'); setPreview(null); } catch (e: any) { setMessage(e.message); } finally { setBusy(false); } }}>Approve recovery</button></div>}
  {message && <p role="status" className="mt-2 text-sm">{message}</p>}
  </details>;
}
