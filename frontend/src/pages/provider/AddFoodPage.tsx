import React, { useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { foodService } from '../../services/foodService';
import { FoodCategory } from '../../types';
import { ArrowLeft, PlusCircle, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth, useOperational } from '../../hooks';
import { PickupLocationMap } from '../../components/common/PickupLocationMap';

const COLOMBO_OFFSET_MINUTES = 330;
const DEFAULT_LATITUDE = 6.773;
const DEFAULT_LONGITUDE = 79.8816;

function toColomboParts(value: string) {
  const date = new Date(value);
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Colombo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(date).reduce<Record<string, string>>((result, part) => {
    result[part.type] = part.value;
    return result;
  }, {});
  const hour24 = Number(parts.hour);
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    hour: String(hour24 % 12 || 12),
    minute: String(Math.floor(Number(parts.minute) / 15) * 15).padStart(2, '0'),
    period: hour24 >= 12 ? 'PM' : 'AM',
  };
}

function fromColomboParts(date: string, hour: string, minute: string, period: string): string {
  const hour24 = (Number(hour) % 12) + (period === 'PM' ? 12 : 0);
  const utc = Date.UTC(
    Number(date.slice(0, 4)),
    Number(date.slice(5, 7)) - 1,
    Number(date.slice(8, 10)),
    hour24,
    Number(minute),
  ) - COLOMBO_OFFSET_MINUTES * 60 * 1000;
  return new Date(utc).toISOString();
}

export const AddFoodPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const { currentUser } = useAuth();
  const { isDisasterMode, activeDisaster } = useOperational();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [unitWeight, setUnitWeight] = useState('');
  const now = new Date();
  const defaultPickupStart = new Date(now.getTime() + 1800000).toISOString(); // +30m
  const defaultPickupEnd = new Date(now.getTime() + 14400000).toISOString(); // +4h
  const defaultSafeUntil = new Date(now.getTime() + 86400000).toISOString(); // +24h

  const [formData, setFormData] = useState({
    name: '',
    category: 'bakery' as FoodCategory,
    quantity: 15,
    unit: 'kg' as const,
    pickupStart: defaultPickupStart,
    pickupEnd: defaultPickupEnd,
    safeUntil: defaultSafeUntil,
    storageRequirements: 'Ambient' as const,
    dietaryTags: [] as ('Vegetarian' | 'Halal' | 'Vegan' | 'Gluten-Free')[],
    safetyNotes: '',
    pickupAddress: '',
    pickupLatitude: DEFAULT_LATITUDE,
    pickupLongitude: DEFAULT_LONGITUDE,
  });

  useEffect(() => {
    if (!editId) return;
    foodService.getListingById(editId).then((listing) => {
      if (!listing) {
        setErrorMsg('This listing could not be found.');
        return;
      }
      setUnitWeight(listing.unitWeightKg == null ? '' : String(listing.unitWeightKg));
      setFormData({
        name: listing.name,
        category: listing.category,
        quantity: listing.quantity,
        unit: listing.unit as 'kg',
        pickupStart: listing.pickupStart,
        pickupEnd: listing.pickupEnd,
        safeUntil: listing.safeUntil,
        storageRequirements: listing.storageRequirements as 'Ambient',
        dietaryTags: listing.dietaryTags || [],
        safetyNotes: listing.safetyNotes || '',
        pickupAddress: listing.pickupAddress || '',
        pickupLatitude: listing.pickupLatitude ?? DEFAULT_LATITUDE,
        pickupLongitude: listing.pickupLongitude ?? DEFAULT_LONGITUDE,
      });
    }).catch((err: Error) => setErrorMsg(err.message || 'Could not load this listing.'));
  }, [editId]);

  const updateTime = (field: 'pickupStart' | 'pickupEnd' | 'safeUntil', part: 'date' | 'hour' | 'minute' | 'period', value: string) => {
    const current = toColomboParts(formData[field]);
    setFormData((previous) => ({
      ...previous,
      [field]: fromColomboParts(
        part === 'date' ? value : current.date,
        part === 'hour' ? value : current.hour,
        part === 'minute' ? value : current.minute,
        part === 'period' ? value : current.period,
      ),
    }));
  };

  const renderTimeSelector = (field: 'pickupStart' | 'pickupEnd' | 'safeUntil', label: string) => {
    const value = toColomboParts(formData[field]);
    return (
      <div>
        <label className="block text-xs font-bold text-[#182B25] mb-1">{label} *</label>
        <div className="grid grid-cols-[1fr_4.5rem_4.5rem_4.5rem] gap-1">
          <input type="date" required value={value.date} onChange={(e) => updateTime(field, 'date', e.target.value)} className="min-w-0 rounded-xl border border-[#E5EAE7] px-2 py-2 text-xs" />
          <select value={value.hour} onChange={(e) => updateTime(field, 'hour', e.target.value)} className="rounded-xl border border-[#E5EAE7] px-1 py-2 text-xs">
            {Array.from({ length: 12 }, (_, index) => String(index + 1)).map((hour) => <option key={hour}>{hour}</option>)}
          </select>
          <select value={value.minute} onChange={(e) => updateTime(field, 'minute', e.target.value)} className="rounded-xl border border-[#E5EAE7] px-1 py-2 text-xs">
            {['00', '15', '30', '45'].map((minute) => <option key={minute}>{minute}</option>)}
          </select>
          <select value={value.period} onChange={(e) => updateTime(field, 'period', e.target.value)} className="rounded-xl border border-[#E5EAE7] px-1 py-2 text-xs">
            <option>AM</option><option>PM</option>
          </select>
        </div>
        <p className="mt-1 text-[10px] text-[#64748B]">Sri Lanka time (Asia/Colombo)</p>
      </div>
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    try {
      const listingData = {
        ...formData,
        quantity: Number(formData.quantity),
        unitWeightKg: unitWeight === '' ? null : Number(unitWeight),
        pickupStart: formData.pickupStart,
        pickupEnd: formData.pickupEnd,
        safeUntil: formData.safeUntil,
        providerId: currentUser.organizationId || '',
        providerName: currentUser.name,
        locationId: '',
        isDisasterRelief: isDisasterMode,
        disasterEventId: activeDisaster?.id,
      };
      const start = new Date(formData.pickupStart);
      const end = new Date(formData.pickupEnd);
      const safeUntil = new Date(formData.safeUntil);
      if (!formData.pickupAddress.trim()) throw new Error('Enter a pickup address.');
      if (end <= start) throw new Error('Pickup end must be after pickup start.');
      if (safeUntil < end) throw new Error('Safe-consumption deadline must cover the pickup window.');
      if (formData.pickupLatitude < -90 || formData.pickupLatitude > 90 || formData.pickupLongitude < -180 || formData.pickupLongitude > 180) {
        throw new Error('Select a valid pickup location on the map.');
      }
      if (editId) {
        await foodService.updateListing(editId, listingData);
      } else {
        await foodService.createListing(listingData);
      }

      setSuccessMsg(editId ? 'Listing updated successfully.' : 'Surplus food successfully registered! It is now available for matching.');
      setTimeout(() => {
        navigate('/food/listings');
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to list food. Please verify input fields.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleTag = (tag: 'Vegetarian' | 'Halal' | 'Vegan' | 'Gluten-Free') => {
    setFormData((prev) => ({
      ...prev,
      dietaryTags: prev.dietaryTags.includes(tag)
        ? prev.dietaryTags.filter((t) => t !== tag)
        : [...prev.dietaryTags, tag],
    }));
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
          <h1 className="text-xl font-extrabold text-[#182B25]">Register Surplus Food</h1>
          <p className="text-xs text-[#64748B]">List excess prepared or packaged food for community redistribution</p>
        </div>
      </div>

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
        <label className="block text-xs font-bold">Recorded weight per unit (kg, optional for non-kg offers)<input className="mt-1 w-full rounded-xl border p-2" type="number" min="0.0001" step="any" value={unitWeight} onChange={e => setUnitWeight(e.target.value)} placeholder="Leave unknown if not measured" /></label>
        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Item Title / Description *</label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g. Fresh Sourdough Loaves & Pastry Boxes"
            className="w-full rounded-xl border border-[#E5EAE7] px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Category *</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value as FoodCategory })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="bakery">Bakery & Pastries</option>
              <option value="cooked_meals">Cooked Warm Meals</option>
              <option value="fresh_produce">Fresh Produce & Fruits</option>
              <option value="dairy">Dairy & Eggs</option>
              <option value="canned_packaged">Canned / Packaged Pantry</option>
              <option value="beverages">Beverages & Juice</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Quantity *</label>
            <input
              type="number"
              min="0.1"
              step="0.1"
              required
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Unit *</label>
            <select
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value as any })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="kg">Kilograms (kg)</option>
              <option value="meals">Portions / Meals</option>
              <option value="boxes">Boxes / Cartons</option>
              <option value="liters">Liters</option>
              <option value="packages">Packages</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {renderTimeSelector('pickupStart', 'Pickup Window Start')}
          {renderTimeSelector('pickupEnd', 'Pickup Window End')}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {renderTimeSelector('safeUntil', 'Safe Consumption Deadline')}

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Storage Condition *</label>
            <select
              value={formData.storageRequirements}
              onChange={(e) => setFormData({ ...formData, storageRequirements: e.target.value as any })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            >
              <option value="Ambient">Ambient Room Temperature</option>
              <option value="Refrigerated">Refrigerated (2°C - 5°C)</option>
              <option value="Keep Frozen">Frozen (&lt; -18°C)</option>
              <option value="Keep Warm (>60°C)">Hot Holding (&gt; 60°C)</option>
            </select>
          </div>

          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-bold text-[#182B25]">Pickup location</h2>
              <p className="text-[11px] text-[#64748B]">Choose the exact handover point. GPS is optional; address entry always works.</p>
            </div>
            <PickupLocationMap
              latitude={formData.pickupLatitude}
              longitude={formData.pickupLongitude}
              onChange={(pickupLatitude, pickupLongitude) => setFormData((previous) => ({ ...previous, pickupLatitude, pickupLongitude }))}
            />
            <input
              required
              type="text"
              value={formData.pickupAddress}
              onChange={(e) => setFormData({ ...formData, pickupAddress: e.target.value })}
              placeholder="Street address, city, landmark"
              className="w-full rounded-xl border border-[#E5EAE7] px-3.5 py-2 text-xs text-[#182B25]"
            />
            <p className="text-[10px] text-[#64748B]">Pin: {formData.pickupLatitude.toFixed(6)}, {formData.pickupLongitude.toFixed(6)}</p>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1.5">Dietary Certifications</label>
          <div className="flex flex-wrap gap-2">
            {(['Vegetarian', 'Halal', 'Vegan', 'Gluten-Free'] as const).map((tag) => (
              <button
                type="button"
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold border transition-all ${
                  formData.dietaryTags.includes(tag)
                    ? 'border-[#16866A] bg-emerald-50 text-[#16866A]'
                    : 'border-[#E5EAE7] text-[#64748B] hover:border-slate-300'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Preparation & Safety Notes</label>
          <textarea
            rows={2}
            value={formData.safetyNotes}
            onChange={(e) => setFormData({ ...formData, safetyNotes: e.target.value })}
            placeholder="e.g. Baked at 4 PM. Keep in dry containers. No allergens."
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
            className="inline-flex items-center gap-1.5 rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all disabled:opacity-50 cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" />
            <span>{isSubmitting ? 'Registering...' : 'Publish Surplus Listing'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddFoodPage;
