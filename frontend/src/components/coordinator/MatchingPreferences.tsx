import { useEffect, useState } from 'react';
import { apiClient, getAllPages } from '../../services/apiClient';

export function MatchingPreferences({ organizationId, coordinator = false }: { organizationId?: string; coordinator?: boolean }) {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [selected, setSelected] = useState(organizationId || '');
  const [org, setOrg] = useState<any>(null);
  const [diet, setDiet] = useState('');
  const [storage, setStorage] = useState('');
  const [dietKnown, setDietKnown] = useState(false);
  const [storageKnown, setStorageKnown] = useState(false);
  const [hours, setHours] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (organizationId) { setSelected(organizationId); return; }
    getAllPages('/organizations/').then(rows => setOrganizations(rows.filter(o => ['NGO','SHELTER','COMMUNITY_KITCHEN','FOOD_BANK','RELIEF_CENTER'].includes(o.type)))).catch(e => setMessage(e.message));
  }, [organizationId]);
  useEffect(() => {
    if (!selected) return;
    apiClient.get(`/organizations/${selected}/`).then(({ data }) => {
      setOrg(data); setDietKnown(data.dietary_requirements != null); setStorageKnown(data.storage_capabilities != null);
      setDiet((data.dietary_requirements || []).join(', ')); setStorage((data.storage_capabilities || []).join(', ')); setHours(data.operatingHours || '');
    }).catch(e => setMessage(e.message));
  }, [selected]);
  return <details className="rounded-2xl border border-[#E5EAE7] bg-white p-4"><summary className="cursor-pointer font-bold">Recorded NGO matching preferences</summary>
    {!organizationId && <label className="mt-3 block text-sm">Organization<select className="ml-2 rounded border p-2" value={selected} onChange={e => setSelected(e.target.value)}><option value="">Select an existing NGO</option>{organizations.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}</select></label>}
    {org && <form className="mt-3 space-y-3 text-sm" onSubmit={async e => {
      e.preventDefault(); setBusy(true); setMessage('');
      const values = (text: string) => text.split(',').map(s => s.trim()).filter(Boolean);
      try { const result = await apiClient.patch(`/organizations/${selected}/`, { dietary_requirements: dietKnown ? values(diet) : null, storage_capabilities: storageKnown ? values(storage) : null, operatingHours: hours }); setOrg(result.data); setMessage('Saved. Changed preferences require coordinator verification before enforcement.'); } catch (e: any) { setMessage(e.message); } finally { setBusy(false); }
    }}>
      <p>{org.name} · {org.matching_preferences_verified ? 'Coordinator verified' : 'Not yet verified'}</p>
      <label className="block"><input type="checkbox" checked={dietKnown} onChange={e => setDietKnown(e.target.checked)} /> Dietary requirements are known (empty list means no dietary restrictions)</label>
      <label className="block">Required dietary tags<input disabled={!dietKnown} className="mt-1 w-full rounded border p-2" value={diet} onChange={e => setDiet(e.target.value)} placeholder="Enter recorded tags, separated by commas" /></label>
      <label className="block"><input type="checkbox" checked={storageKnown} onChange={e => setStorageKnown(e.target.checked)} /> Storage capabilities are known</label>
      <label className="block">Storage capabilities<input disabled={!storageKnown} className="mt-1 w-full rounded border p-2" value={storage} onChange={e => setStorage(e.target.value)} placeholder="Ambient, Refrigerated, Keep Frozen, Keep Warm (>60°C)" /></label>
      <label className="block">Recorded receiving / operating hours (Asia/Colombo)<input className="mt-1 w-full rounded border p-2" value={hours} onChange={e => setHours(e.target.value)} placeholder="HH:MM - HH:MM or 24 Hours; leave unknown if unrecorded" /></label>
      <div className="flex gap-2"><button disabled={busy} className="rounded-lg bg-[#16866A] px-3 py-2 text-white disabled:opacity-40">Save recorded preferences</button>{coordinator && <button type="button" disabled={busy || !org.verified} className="rounded-lg border px-3 py-2 disabled:opacity-40" onClick={async () => { setBusy(true); try { const result = await apiClient.post(`/organizations/${selected}/verify_preferences/`); setOrg(result.data); setMessage('Saved preferences verified. Refresh matching to re-evaluate.'); } catch (e: any) { setMessage(e.message); } finally { setBusy(false); } }}>Verify saved records</button>}</div>
    </form>}
    {message && <p role="status" className="mt-2 text-sm">{message}</p>}
  </details>;
}
