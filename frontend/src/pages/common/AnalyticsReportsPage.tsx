import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Package,
  Droplets,
  Utensils,
  Box,
  Truck,
  Users,
  Printer,
  RotateCcw,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Flame,
  Info,
} from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { useLivePolling } from '../../hooks';

export const AnalyticsReportsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    try {
      const res = await analyticsService.getVerifiedImpact();
      if (res) {
        setData(res);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const { isPolling, lastPolledAt, forcePoll } = useLivePolling({
    fetcher: loadData,
    intervalMs: 30000,
    enabled: true,
  });

  const normal = data?.normal_community_metrics || {};
  const disaster = data?.disaster_metrics || {};
  const provenance = data?.data_provenance || {};

  const totalFoodListed = normal.total_food_listed_by_unit || {};
  const totalDelivered = normal.total_delivered_by_unit || {};
  const fulfillmentByUnit = normal.fulfillment_percentages_by_unit || {};
  const unmetDemand = normal.unmet_demand_by_unit || {};
  const expiredWithdrawn = normal.expired_or_withdrawn_by_unit || {};

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[#E5EAE7] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-extrabold text-[#182B25] flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-[#16866A]" />
              <span>Verified Impact Analytics</span>
            </h1>
            <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
              Unit Separated • DB Provenance
            </span>
          </div>
          <p className="text-xs text-[#64748B] mt-0.5">
            Empirical data verified against committed PostgreSQL ledger transactions. Strict separation of mass, volume, and discrete portion counts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {lastPolledAt && (
            <span className="text-[11px] text-[#64748B] font-mono mr-1">
              Refreshed {lastPolledAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => forcePoll()}
            disabled={isPolling}
            className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] shadow-xs cursor-pointer disabled:opacity-50"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${isPolling ? 'animate-spin text-[#16866A]' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] cursor-pointer"
          >
            <Printer className="h-3.5 w-3.5" />
            <span>Export / Print</span>
          </button>
        </div>
      </div>

      {/* Data Provenance & Methodology Banner */}
      <div className="rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/70 p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-[#16866A] shrink-0" />
            <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-900">
              {provenance.dataSourceLabel || 'PostgreSQL Operational Database (Verified Records)'}
            </span>
          </div>
          {provenance.is_synthetic_or_demo_data && (
            <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-300">
              Contains Isolated Pilot Demo Data [DEMO]
            </span>
          )}
        </div>
        <p className="text-[11px] text-emerald-950/80 leading-relaxed">
          {provenance.methodology_disclaimer ||
            'Data directly aggregates committed PostgreSQL transactions. Units are strictly isolated to prevent mathematical distortion.'}
        </p>
      </div>

      {/* Verified Delivery Execution By Unit (Strict Separation: kg, liters, meals, packages) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#182B25] flex items-center gap-2">
            <Package className="h-4 w-4 text-[#16866A]" />
            <span>Verified Rescued Deliveries by Physical Unit</span>
          </h2>
          <span className="text-[11px] text-[#64748B] italic">
            Counted exclusively upon verified DELIVERED status
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Kilograms (Food Lots) */}
          <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-[#64748B] mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Solid Food (kg)</span>
              <Package className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#182B25]">
              {(totalDelivered.kg ?? 0).toLocaleString()} <span className="text-sm font-medium text-slate-500">kg</span>
            </div>
            <p className="text-[11px] text-[#64748B] mt-1">
              Cooked meals, produce, staples
            </p>
            <div className="mt-3 pt-2 border-t border-[#E5EAE7] text-[11px] flex justify-between text-[#64748B]">
              <span>Listed Supply:</span>
              <span className="font-semibold text-[#182B25]">{(totalFoodListed.kg ?? 0).toLocaleString()} kg</span>
            </div>
          </div>

          {/* Liters (Liquids / Clean Water) */}
          <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-[#64748B] mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Potable Water / Liquids</span>
              <Droplets className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#182B25]">
              {(totalDelivered.liters ?? 0).toLocaleString()} <span className="text-sm font-medium text-slate-500">L</span>
            </div>
            <p className="text-[11px] text-[#64748B] mt-1">
              Safe drinking water & nutrition milk
            </p>
            <div className="mt-3 pt-2 border-t border-[#E5EAE7] text-[11px] flex justify-between text-[#64748B]">
              <span>Listed Supply:</span>
              <span className="font-semibold text-[#182B25]">{(totalFoodListed.liters ?? 0).toLocaleString()} L</span>
            </div>
          </div>

          {/* Portioned Meals (Discrete counts) */}
          <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-[#64748B] mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Portioned Meals</span>
              <Utensils className="h-4 w-4 text-amber-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#182B25]">
              {(totalDelivered.meals ?? 0).toLocaleString()} <span className="text-sm font-medium text-slate-500">meals</span>
            </div>
            <p className="text-[11px] text-[#64748B] mt-1">
              Discrete prepared lunch / dinner packets
            </p>
            <div className="mt-3 pt-2 border-t border-[#E5EAE7] text-[11px] flex justify-between text-[#64748B]">
              <span>Listed Supply:</span>
              <span className="font-semibold text-[#182B25]">{(totalFoodListed.meals ?? 0).toLocaleString()} meals</span>
            </div>
          </div>

          {/* Emergency Packages / Kits */}
          <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-[#64748B] mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Relief Kits / Boxes</span>
              <Box className="h-4 w-4 text-purple-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#182B25]">
              {((totalDelivered.packages ?? 0) + (totalDelivered.boxes ?? 0)).toLocaleString()}{' '}
              <span className="text-sm font-medium text-slate-500">boxes</span>
            </div>
            <p className="text-[11px] text-[#64748B] mt-1">
              Hygiene sets, dry rations, first-aid kits
            </p>
            <div className="mt-3 pt-2 border-t border-[#E5EAE7] text-[11px] flex justify-between text-[#64748B]">
              <span>Listed Supply:</span>
              <span className="font-semibold text-[#182B25]">
                {((totalFoodListed.packages ?? 0) + (totalFoodListed.boxes ?? 0)).toLocaleString()} kits
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Efficiency: Transit Times & Network Scale */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Transit Speed */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-[#64748B] uppercase tracking-wider mb-2">
            <Clock className="h-4 w-4 text-[#16866A]" />
            <span>Average Courier Transit</span>
          </div>
          <div className="text-2xl font-extrabold text-[#182B25]">
            {normal.average_pickup_to_delivery_minutes !== null && normal.average_pickup_to_delivery_minutes !== undefined ? (
              <>
                {normal.average_pickup_to_delivery_minutes}{' '}
                <span className="text-sm font-medium text-slate-500">minutes</span>
              </>
            ) : (
              <span className="text-base font-bold text-slate-400">N/A (Awaiting Timestamps)</span>
            )}
          </div>
          <p className="text-[11px] text-[#64748B] mt-1">
            Calculated strictly between recorded DB pickup and delivery timestamps.
          </p>
        </div>

        {/* Deliveries Completed Count */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-[#64748B] uppercase tracking-wider mb-2">
            <Truck className="h-4 w-4 text-blue-600" />
            <span>Completed Missions</span>
          </div>
          <div className="text-2xl font-extrabold text-[#182B25]">
            {normal.completed_deliveries_count ?? 0}
          </div>
          <p className="text-[11px] text-[#64748B] mt-1">
            Successful missions signed off by recipient shelters.
          </p>
        </div>

        {/* Participating Organizations */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-[#64748B] uppercase tracking-wider mb-2">
            <Users className="h-4 w-4 text-purple-600" />
            <span>Participating Organizations</span>
          </div>
          <div className="text-2xl font-extrabold text-[#182B25]">
            {normal.participating_verified_organizations_count ?? 0}{' '}
            <span className="text-sm font-medium text-slate-500">
              verified of {normal.participating_total_organizations_count ?? 0} registered
            </span>
          </div>
          <p className="text-[11px] text-[#64748B] mt-1">
            Registered food providers, distribution hubs, and beneficiary NGOs.
          </p>
        </div>
      </div>

      {/* Requisition Demand Fulfillment with Explicit Denominators */}
      <div className="rounded-3xl border border-[#E5EAE7] bg-white p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#182B25] flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-[#16866A]" />
            <span>Community Demand Fulfillment with Explicit Denominators</span>
          </h3>
          <p className="text-xs text-[#64748B] mt-0.5">
            Percentage fulfillment calculated per physical unit type against explicitly stated total requested community demand.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.keys(fulfillmentByUnit).length > 0 ? (
            Object.entries(fulfillmentByUnit).map(([unitKey, item]: [string, any]) => (
              <div key={unitKey} className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#182B25]">
                    {unitKey} Fulfillment Rate
                  </span>
                  <span className="text-base font-extrabold text-[#16866A]">
                    {item.fulfillmentPercentage}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-[#16866A] h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, item.fulfillmentPercentage)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#64748B] pt-1">
                  <span>
                    Fulfilled: <strong className="text-[#182B25]">{item.allocated} {unitKey}</strong>
                  </span>
                  <span>
                    Denominator: <strong className="text-[#182B25]">{item.denominator} {unitKey} requested</strong>
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-[#64748B] italic col-span-2">No demand records logged yet.</p>
          )}
        </div>
      </div>

      {/* Disaster Emergency Operations Performance Section */}
      <div className="rounded-3xl border border-red-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-red-100 pb-3">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-red-600" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-red-900">
              Disaster Response & Emergency Relief Performance
            </h3>
          </div>
          <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-[10px] font-bold text-red-700">
            Rapid Response Sector
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-red-100 bg-red-50/50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-700">
              Relief Demands Received
            </span>
            <div className="text-2xl font-extrabold text-red-900 mt-1">
              {disaster.requests_received ?? 0}
            </div>
            <p className="text-[11px] text-red-700/80 mt-1">
              {disaster.requests_fulfilled ?? 0} fulfilled / {disaster.requests_partially_fulfilled ?? 0} partial
            </p>
          </div>

          <div className="rounded-2xl border border-red-100 bg-red-50/50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-700">
              Pending Urgent Requests
            </span>
            <div className="text-2xl font-extrabold text-red-900 mt-1">
              {disaster.pending_urgent_requests ?? 0}
            </div>
            <p className="text-[11px] text-red-700/80 mt-1">High-priority life safety needs</p>
          </div>

          <div className="rounded-2xl border border-red-100 bg-red-50/50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-700">
              Disaster Missions Completed
            </span>
            <div className="text-2xl font-extrabold text-red-900 mt-1">
              {disaster.deliveries_completed ?? 0}
            </div>
            <p className="text-[11px] text-red-700/80 mt-1">Through flood-affected routes</p>
          </div>

          <div className="rounded-2xl border border-red-100 bg-red-50/50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-700">
              Recovery Plans Executed
            </span>
            <div className="text-2xl font-extrabold text-red-900 mt-1">
              {disaster.recovery_plans_applied ?? 0}
            </div>
            <p className="text-[11px] text-red-700/80 mt-1">
              {disaster.disruptions_recorded ?? 0} route hazards resolved
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsReportsPage;
