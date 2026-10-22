import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { requestService } from '../../services/requestService';
import { isApiMode } from '../../services/apiClient';
import { useOperational } from '../../hooks';
import { RequestPriority } from '../../types';
import { ArrowLeft, PlusCircle, CheckCircle2, AlertCircle, Flame } from 'lucide-react';

export const CreateRequestPage: React.FC = () => {
  const navigate = useNavigate();
  const { isDisasterMode, activeDisaster } = useOperational();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryLatitude, setDeliveryLatitude] = useState('');
  const [deliveryLongitude, setDeliveryLongitude] = useState('');
  const [allowPartial, setAllowPartial] = useState(true);
  const now = new Date();
  const defaultDeadline = new Date(now.getTime() + 14400000 - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16); // local +4h

  const [formData, setFormData] = useState({
    itemName: '',
    category: (isDisasterMode ? 'drinking_water' : 'cooked_meals') as any,
    requestedQuantity: 50,
    unit: isDisasterMode ? 'liters' : 'meals',
    priority: (isDisasterMode ? 'urgent' : 'high') as RequestPriority,
    urgencyDeadline: defaultDeadline,
    peopleImpacted: 45,
    specialInstructions: '',
    isDisasterRelief: isDisasterMode,
    disasterEventId: activeDisaster?.id || '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    try {
      const created = await requestService.createRequest({
        ...formData,
        deliveryAddress,
        deliveryLatitude: deliveryLatitude === '' ? null : Number(deliveryLatitude),
        deliveryLongitude: deliveryLongitude === '' ? null : Number(deliveryLongitude),
        allowPartial,
        requestedQuantity: Number(formData.requestedQuantity),
        peopleImpacted: Number(formData.peopleImpacted),
        urgencyDeadline: new Date(formData.urgencyDeadline).toISOString(),
        recipientId: isApiMode() ? '' : 'ORG-003',
        recipientName: isApiMode() ? '' : 'Community Recipient NGO',
        locationId: isApiMode() ? '' : 'LOC-003',
        disasterEventId: formData.isDisasterRelief ? (formData.disasterEventId || activeDisaster?.id) : undefined,
      });

      setSuccessMsg(`Resource request ${created.id} published successfully.`);
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit request. Please verify inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/dashboard"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[#E5EAE7] bg-white text-[#64748B] hover:text-[#182B25] shadow-xs"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-extrabold text-[#182B25]">Create Resource Request</h1>
          <p className="text-xs text-[#64748B]">Request meals, dry rations, or emergency supplies for community redistribution</p>
        </div>
      </div>

      {isDisasterMode && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-800 flex items-center gap-2">
          <Flame className="h-4 w-4 text-red-600 shrink-0" />
          <span>Disaster Mode Active: Requests can be flagged for priority emergency response under {activeDisaster?.title || 'Active Disaster'}.</span>
        </div>
      )}

      {errorMsg && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="rounded-2xl border border-[#E5EAE7] bg-white p-6 shadow-xs space-y-5">
        <details><summary className="cursor-pointer text-sm font-semibold">Delivery location and partial fulfillment</summary><p className="my-2 text-xs text-slate-500">Leave delivery location blank to use your registered NGO address and coordinates. A different address needs its own coordinates.</p><label className="block text-xs">Delivery address<input className="my-1 w-full rounded border p-2" value={deliveryAddress} onChange={e => setDeliveryAddress(e.target.value)} /></label><div className="grid grid-cols-2 gap-2"><label className="text-xs">Latitude<input className="my-1 w-full rounded border p-2" type="number" step="any" min={-90} max={90} value={deliveryLatitude} onChange={e => setDeliveryLatitude(e.target.value)} /></label><label className="text-xs">Longitude<input className="my-1 w-full rounded border p-2" type="number" step="any" min={-180} max={180} value={deliveryLongitude} onChange={e => setDeliveryLongitude(e.target.value)} /></label></div><label className="text-xs"><input type="checkbox" checked={allowPartial} onChange={e => setAllowPartial(e.target.checked)} /> Accept partial quantities</label></details>
        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Required Item / Description *</label>
          <input
            type="text"
            required
            value={formData.itemName}
            onChange={(e) => setFormData({ ...formData, itemName: e.target.value })}
            placeholder="e.g. Prepared Hot Lunches or 500L Potable Water"
            className="w-full rounded-xl border border-[#E5EAE7] px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Category *</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="cooked_meals">Cooked Warm Meals</option>
              <option value="bakery">Bakery Items & Bread</option>
              <option value="fresh_produce">Fresh Produce / Vegetables</option>
              <option value="canned_packaged">Pantry / Dry Rations</option>
              <option value="drinking_water">Clean Drinking Water</option>
              <option value="hygiene_kits">Hygiene / Sanitation Kits</option>
              <option value="medical_supplies">First Aid / Medical</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Quantity Needed *</label>
            <input
              type="number"
              min="1"
              required
              value={formData.requestedQuantity}
              onChange={(e) => setFormData({ ...formData, requestedQuantity: parseFloat(e.target.value) || 0 })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Unit *</label>
            <select
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="meals">Meals / Portions</option>
              <option value="kg">Kilograms (kg)</option>
              <option value="liters">Liters</option>
              <option value="boxes">Boxes / Packs</option>
              <option value="packages">Packages</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Urgency Priority *</label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as RequestPriority })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="low">Low (Next 48 Hours)</option>
              <option value="medium">Medium (Next 24 Hours)</option>
              <option value="high">High (Next 6 Hours)</option>
              <option value="urgent">Urgent Emergency (&lt; 2 Hours)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Needed-By Deadline *</label>
            <input
              type="datetime-local"
              required
              value={formData.urgencyDeadline}
              onChange={(e) => setFormData({ ...formData, urgencyDeadline: e.target.value })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">People Impacted</label>
            <input
              type="number"
              min="1"
              value={formData.peopleImpacted}
              onChange={(e) => setFormData({ ...formData, peopleImpacted: parseInt(e.target.value, 10) || 0 })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>
        </div>

        {/* Disaster Relief Linking */}
        <div className="rounded-xl border border-[#E5EAE7] bg-slate-50/70 p-3.5">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.isDisasterRelief}
              onChange={(e) => setFormData({ ...formData, isDisasterRelief: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-[#16866A] focus:ring-[#16866A]"
            />
            <span className="text-xs font-bold text-[#182B25]">Link to Active Disaster Relief Effort</span>
          </label>
          {formData.isDisasterRelief && activeDisaster && (
            <p className="mt-1 text-[11px] text-[#64748B] pl-6">
              Linked event: <strong>{activeDisaster.title}</strong> (ID: {activeDisaster.id})
            </p>
          )}
        </div>

        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Delivery / Handling Instructions</label>
          <textarea
            rows={2}
            value={formData.specialInstructions}
            onChange={(e) => setFormData({ ...formData, specialInstructions: e.target.value })}
            placeholder="e.g. Ring front reception on arrival. Storage area has refrigeration available."
            className="w-full rounded-xl border border-[#E5EAE7] px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
          />
        </div>

        <div className="pt-2 flex justify-end gap-3">
          <Link
            to="/dashboard"
            className="rounded-xl border border-[#E5EAE7] px-4 py-2 text-xs font-bold text-[#64748B] hover:text-[#182B25] hover:bg-slate-50 transition-all"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition-all disabled:opacity-50 cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" />
            <span>{isSubmitting ? 'Publishing...' : 'Submit Requisition'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateRequestPage;
