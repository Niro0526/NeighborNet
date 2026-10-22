import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../../services/apiClient';
import { useAuth, useLivePolling } from '../../hooks';
import { PickupLocationMap } from '../../components/common/PickupLocationMap';

interface Location { address: string; latitude: number; longitude: number }
interface Offer { id: string; name: string; providerName: string; availableQuantity: number; unit: string; pickupAddress: string; pickupStart: string; pickupEnd: string; safeUntil: string; storageRequirements: string; safetyNotes: string; dietaryTags: string[]; distanceKm: number | null }
interface Claim { id: string; resource: string; resourceName: string; providerName: string; recipient: string; recipientName: string; quantity: string; unit: string; method: string; status: string; address?: string; volunteerName?: string; volunteerUserId?: string; canHandover: boolean; pickupCode?: string; pickupAddress: string; storageRequirements: string; safetyNotes: string; safeUntil: string; events: { status: string; created_at: string }[] }
const labels: Record<string, string> = { PENDING: 'Awaiting approval', APPROVED: 'Approved', ASSIGNED: 'Volunteer assigned', PICKED_UP: 'Picked up', DELIVERED: 'Delivered', RECEIVED: 'Receipt confirmed', REJECTED: 'Rejected', CANCELLED: 'Cancelled' };
const button = 'rounded-lg bg-[#16866A] px-3 py-2 text-sm font-semibold text-white disabled:opacity-40 hover:bg-[#09664F]';
const input = 'rounded-lg border border-[#E5EAE7] px-3 py-2 text-sm w-full';

export function CommunityFoodPage() {
  const { currentUser, isCoordinator, isVolunteer } = useAuth();
  const [location, setLocation] = useState<Location>({ address: '', latitude: 6.773, longitude: 79.8816 });
  const [saved, setSaved] = useState(false);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [methods, setMethods] = useState<Record<string, string>>({});
  const [ack, setAck] = useState<Record<string, boolean>>({});
  const [codes, setCodes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loaded, setLoaded] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const [o, c] = await Promise.all([apiClient.get<Offer[]>('/community-food/offers/'), apiClient.get<Claim[]>('/community-food/')]);
      setOffers(o.data); setClaims(c.data); setLoaded(true); setError('');
    } catch (e: any) { setError(e.message || 'Unable to load food requests.'); }
  }, []);
  useEffect(() => {
    apiClient.get<Location | null>('/community-food/location/').then(r => { if (r.data) { setLocation(r.data); setSaved(true); } }).catch(e => setError(e.message));
    void refresh();
  }, [refresh]);
  useLivePolling(refresh);
  async function perform(work: () => Promise<unknown>, message: string) {
    if (busy) return;
    setBusy(true); setError(''); setNotice('');
    try { await work(); setNotice(message); await refresh(); } catch (e: any) { setError(e.message || 'Request failed.'); } finally { setBusy(false); }
  }
  function transition(claim: Claim, status: string) {
    void perform(() => apiClient.post(`/community-food/${claim.id}/transition/`, { status, safetyAcknowledged: ack[claim.id] === true, pickupCode: codes[claim.id] || '' }), 'Status updated.');
  }
  return <div className="mx-auto max-w-6xl space-y-5">
    <div><h1 className="text-2xl font-bold text-[#182B25]">Community food</h1><p className="mt-1 text-sm text-slate-600">Receive surplus food as an individual. No NGO registration needed. All requests require coordinator approval.</p></div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-800">{error}</p>}
    {notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-emerald-800">{notice}</p>}
    <details className="rounded-2xl border border-[#E5EAE7] bg-white p-4" open={!saved}>
      <summary className="cursor-pointer font-semibold">{saved ? `Your location: ${location.address}` : 'Set your location to request food'}</summary>
      <form className="mt-3 space-y-3" onSubmit={e => { e.preventDefault(); void perform(async () => { await apiClient.put('/community-food/location/', location); setSaved(true); }, 'Location saved. Existing requests keep their original delivery location.'); }}>
        <label className="block text-sm">Delivery address<input className={input} required maxLength={300} value={location.address} onChange={e => { setLocation({ ...location, address: e.target.value }); setSaved(false); }} /></label>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">Latitude<input className={input} type="number" step="any" min={-90} max={90} required value={location.latitude} onChange={e => { setLocation({ ...location, latitude: Number(e.target.value) }); setSaved(false); }} /></label>
          <label className="text-sm">Longitude<input className={input} type="number" step="any" min={-180} max={180} required value={location.longitude} onChange={e => { setLocation({ ...location, longitude: Number(e.target.value) }); setSaved(false); }} /></label>
        </div>
        <PickupLocationMap latitude={location.latitude} longitude={location.longitude} onChange={(latitude, longitude) => { setLocation(v => ({ ...v, latitude, longitude })); setSaved(false); }} />
        <button disabled={busy} className={button}>Save location</button>
      </form>
    </details>
    <section className="rounded-2xl border border-[#E5EAE7] bg-white p-4">
      <h2 className="mb-3 text-lg font-bold">{isCoordinator ? 'Community requests' : 'Food requests and tracking'}</h2>
      {!loaded ? <p>Loading requests…</p> : !claims.length && <p className="text-sm text-slate-500">No requests yet.</p>}
      <div className="space-y-3">{claims.map(c => {
        const mine = c.recipient === currentUser.id;
        const courier = isVolunteer && c.volunteerUserId === currentUser.id;
        return <article key={c.id} className="rounded-xl border border-[#E5EAE7] p-3">
          <div className="flex flex-wrap justify-between gap-2"><h3 className="font-semibold">{c.resourceName} · {c.quantity} {c.unit}</h3><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold">{labels[c.status]}</span></div>
          <p className="text-sm text-slate-600">{c.providerName} → {c.recipientName} · {c.method === 'pickup' ? 'Authorized pickup' : 'Volunteer delivery'}{c.volunteerName && ` · ${c.volunteerName}`}</p>
          <p className="mt-1 text-sm">Pickup: {c.pickupAddress}{c.address && ` · Destination: ${c.address}`}</p>
          <p className="text-xs text-slate-500">{c.storageRequirements} · Safe until {new Date(c.safeUntil).toLocaleString()}{c.safetyNotes && ` · ${c.safetyNotes}`}</p>
          <ol className="my-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">{c.events.map((event, i) => <li key={i}>{labels[event.status]} · {new Date(event.created_at).toLocaleString()}</li>)}</ol>
          <div className="flex flex-wrap items-center gap-2">
            {c.pickupCode && <p className="text-sm font-semibold">Your pickup code: {c.pickupCode}. Show it to the provider at handover.</p>}
            {c.canHandover && c.method === 'pickup' && c.status === 'APPROVED' && <label className="text-xs">Recipient pickup code<input className={input} maxLength={12} value={codes[c.id] || ''} onChange={e => setCodes(v => ({ ...v, [c.id]: e.target.value }))} /></label>}
            {isCoordinator && c.status === 'PENDING' && <><button disabled={busy} className={button} onClick={() => transition(c, 'APPROVED')}>Approve</button><button disabled={busy} className={button} onClick={() => transition(c, 'REJECTED')}>Reject</button></>}
            {(mine || isCoordinator) && ['PENDING', 'APPROVED', 'ASSIGNED'].includes(c.status) && <button disabled={busy} className={button} onClick={() => transition(c, 'CANCELLED')}>Cancel request</button>}
            {isVolunteer && !mine && c.status === 'APPROVED' && c.method === 'delivery' && <button disabled={busy} className={button} onClick={() => transition(c, 'ASSIGNED')}>Accept delivery</button>}
            {c.canHandover && (c.status === 'ASSIGNED' || (c.status === 'APPROVED' && c.method === 'pickup' && !courier)) && <><label className="text-xs"><input type="checkbox" checked={!!ack[c.id]} onChange={e => setAck(v => ({ ...v, [c.id]: e.target.checked }))} /> I verified safe handling and handover</label><button disabled={busy || !ack[c.id]} className={button} onClick={() => transition(c, 'PICKED_UP')}>Confirm pickup</button></>}
            {c.status === 'PICKED_UP' && c.method === 'delivery' && (courier || isCoordinator) && <button disabled={busy} className={button} onClick={() => transition(c, 'DELIVERED')}>Confirm delivery</button>}
            {mine && (c.status === 'DELIVERED' || (c.status === 'PICKED_UP' && c.method === 'pickup')) && <button disabled={busy} className={button} onClick={() => transition(c, 'RECEIVED')}>Confirm receipt</button>}
          </div>
        </article>;
      })}</div>
    </section>
    <section><h2 className="mb-3 text-lg font-bold">Available food {saved && 'near you'}</h2>
      {!loaded ? <p>Loading offers…</p> : !offers.length && <p className="text-sm text-slate-500">No eligible food is available right now. Check back later.</p>}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{offers.map(o => {
        const claimed = claims.some(c => c.resource === o.id && c.recipient === currentUser.id && !['REJECTED', 'CANCELLED'].includes(c.status));
        return <article key={o.id} className="space-y-2 rounded-2xl border border-[#E5EAE7] bg-white p-4">
          <h3 className="font-bold">{o.name}</h3><p className="text-sm">{o.availableQuantity} {o.unit} · {o.providerName}</p>
          <p className="text-xs text-slate-600">{o.pickupAddress}{o.distanceKm != null && ` · ${o.distanceKm.toFixed(1)} km`}</p>
          <p className="text-xs text-slate-600">Pickup {new Date(o.pickupStart).toLocaleString()} – {new Date(o.pickupEnd).toLocaleString()}</p>
          <p className="text-xs">Safe until {new Date(o.safeUntil).toLocaleString()} · {o.storageRequirements}</p>
          <p className="text-xs">{o.safetyNotes} {o.dietaryTags.join(', ')}</p>
          <label className="block text-xs">Quantity ({o.unit})<input className={input} type="number" min="0.01" step="0.01" max={o.availableQuantity} value={quantities[o.id] ?? Math.min(1, o.availableQuantity)} onChange={e => setQuantities(v => ({ ...v, [o.id]: e.target.value }))} /></label>
          <label className="block text-xs">Receive by<select className={input} value={methods[o.id] || (o.unit === 'kg' ? 'delivery' : 'pickup')} onChange={e => setMethods(v => ({ ...v, [o.id]: e.target.value }))}>{o.unit === 'kg' && <option value="delivery">Volunteer delivery</option>}<option value="pickup">Authorized pickup</option></select></label>
          <label className="flex gap-2 text-xs"><input type="checkbox" checked={!!ack[o.id]} onChange={e => setAck(v => ({ ...v, [o.id]: e.target.checked }))} />I can follow the storage and food safety instructions</label>
          <button className={button} disabled={busy || !saved || !ack[o.id] || claimed} onClick={() => void perform(() => apiClient.post('/community-food/', { resource: o.id, quantity: quantities[o.id] ?? Math.min(1, o.availableQuantity), method: methods[o.id] || (o.unit === 'kg' ? 'delivery' : 'pickup'), safetyAcknowledged: ack[o.id] }), 'Food requested. The provider and coordinator have been notified.')}>
            {claimed ? 'Already requested' : !saved ? 'Save location first' : 'Request food'}
          </button>
        </article>;
      })}</div>
    </section>
  </div>;
}
