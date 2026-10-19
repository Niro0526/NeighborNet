import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { foodService } from '../../services/foodService';
import { FoodCategory } from '../../types';
import { ArrowLeft, PlusCircle, CheckCircle2, AlertCircle } from 'lucide-react';

export const AddFoodPage: React.FC = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const now = new Date();
  const defaultPickupStart = new Date(now.getTime() + 1800000).toISOString().slice(0, 16); // +30m
  const defaultPickupEnd = new Date(now.getTime() + 14400000).toISOString().slice(0, 16); // +4h
  const defaultSafeUntil = new Date(now.getTime() + 86400000).toISOString().slice(0, 16); // +24h

  const [formData, setFormData] = useState({
    name: '',
    category: 'bakery' as FoodCategory,
    quantity: 15,
    unit: 'kg' as const,
    pickupStart: defaultPickupStart,
    pickupEnd: defaultPickupEnd,
    safeUntil: defaultSafeUntil,
    storageRequirements: 'Ambient' as const,
    dietaryTags: ['Vegetarian'] as ('Vegetarian' | 'Halal' | 'Vegan' | 'Gluten-Free')[],
    safetyNotes: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    try {
      await foodService.createListing({
        ...formData,
        quantity: Number(formData.quantity),
        pickupStart: new Date(formData.pickupStart).toISOString(),
        pickupEnd: new Date(formData.pickupEnd).toISOString(),
        safeUntil: new Date(formData.safeUntil).toISOString(),
        providerId: 'ORG-001',
        providerName: 'Colombo City Bakery',
        locationId: 'LOC-001',
      });

      setSuccessMsg('Surplus food successfully registered! It is now available for matching.');
      setTimeout(() => {
        navigate('/dashboard');
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
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Pickup Window Start *</label>
            <input
              type="datetime-local"
              required
              value={formData.pickupStart}
              onChange={(e) => setFormData({ ...formData, pickupStart: e.target.value })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Pickup Window End *</label>
            <input
              type="datetime-local"
              required
              value={formData.pickupEnd}
              onChange={(e) => setFormData({ ...formData, pickupEnd: e.target.value })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Safe Consumption Deadline *</label>
            <input
              type="datetime-local"
              required
              value={formData.safeUntil}
              onChange={(e) => setFormData({ ...formData, safeUntil: e.target.value })}
              className="w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

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
