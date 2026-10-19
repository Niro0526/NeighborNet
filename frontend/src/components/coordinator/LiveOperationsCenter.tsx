import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLivePolling } from '../../hooks';
import { analyticsService } from '../../services/analyticsService';
import {
  Activity,
  AlertTriangle,
  Clock,
  ShieldAlert,
  CheckCircle,
  Truck,
  Users,
  Layers,
  ArrowRight,
  RefreshCw,
  Flame,
} from 'lucide-react';

export const LiveOperationsCenter: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOps = async () => {
    try {
      const ops = await analyticsService.getLiveOperations();
      if (ops) {
        setData(ops);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const { isPolling, lastPolledAt, forcePoll } = useLivePolling({
    fetcher: fetchOps,
    intervalMs: 15000,
    enabled: true,
  });

  const ops = data || {};
  const pendingVerifs = ops.pendingVerifications?.count ?? 0;
  const pendingAllocations = ops.pendingAllocationApprovals?.count ?? 0;
  const activeDeliveries = ops.activeDeliveries?.count ?? 0;
  const delayedDeliveries = ops.delayedDeliveries?.count ?? 0;
  const unmetRequests = ops.unmetRequests?.count ?? 0;
  const urgentDisaster = ops.urgentDisasterRequests?.count ?? 0;
  const disruptions = ops.volunteerDisruptions?.count ?? 0;

  const hasUrgentAlerts = disruptions > 0 || delayedDeliveries > 0 || urgentDisaster > 0;

  return (
    <div className="rounded-3xl border border-[#E5EAE7] bg-white p-6 shadow-sm space-y-6">
      {/* Header and Live Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E5EAE7]">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#16866A]/10 text-[#16866A]">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-extrabold text-[#182B25]">
                Coordinator Live Operations Center
              </h3>
              <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Live 15s Polling
              </span>
            </div>
            <p className="text-xs text-[#64748B] mt-0.5">
              Real-time situational monitoring, human-in-the-loop approvals, and mission intervention
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {lastPolledAt && (
            <span className="text-[11px] text-[#64748B] font-mono">
              Updated {lastPolledAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => forcePoll()}
            disabled={isPolling}
            title="Refresh Live Operations"
            className="rounded-xl border border-[#E5EAE7] p-2 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isPolling ? 'animate-spin text-[#16866A]' : 'text-[#64748B]'}`} />
          </button>
        </div>
      </div>

      {/* Critical Operational Banner if any disruption or delay */}
      {hasUrgentAlerts && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 space-y-2">
          <div className="flex items-center gap-2 text-red-800 font-bold text-xs uppercase tracking-wider">
            <ShieldAlert className="h-4 w-4 text-red-600 shrink-0" />
            <span>Active Operational Action Items</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-red-700">
            {disruptions > 0 && (
              <div className="flex items-center justify-between bg-white/70 p-2.5 rounded-xl border border-red-200/60">
                <span>Route Disruptions / Hazards:</span>
                <span className="font-extrabold text-red-800 bg-red-100 px-2 py-0.5 rounded-md">
                  {disruptions}
                </span>
              </div>
            )}
            {delayedDeliveries > 0 && (
              <div className="flex items-center justify-between bg-white/70 p-2.5 rounded-xl border border-red-200/60">
                <span>Overdue Deliveries:</span>
                <span className="font-extrabold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-md">
                  {delayedDeliveries}
                </span>
              </div>
            )}
            {urgentDisaster > 0 && (
              <div className="flex items-center justify-between bg-white/70 p-2.5 rounded-xl border border-red-200/60">
                <span>Urgent Disaster Requests:</span>
                <span className="font-extrabold text-red-800 bg-red-100 px-2 py-0.5 rounded-md">
                  {urgentDisaster}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Operational Matrix Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. Pending Verifications */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5 text-[#16866A]" /> Pending Onboarding
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-extrabold ${
                  pendingVerifs > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {pendingVerifs}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              Unverified Partners & Couriers
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              Requires coordinator review of registration, contact numbers, and operating capacity.
            </p>
          </div>
          <Link
            to="/admin/approvals"
            className="flex items-center justify-between text-xs font-bold text-[#16866A] hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Review Approvals Queue</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 2. Pending Allocations */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-blue-600" /> Allocations
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-extrabold ${
                  pendingAllocations > 0 ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {pendingAllocations}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              Awaiting Coordinator Authorization
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              CP-SAT and heuristic matches held for human oversight prior to courier dispatch.
            </p>
          </div>
          <Link
            to="/admin/matching"
            className="flex items-center justify-between text-xs font-bold text-blue-700 hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Open Smart Matching</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 3. Active Deliveries & Transit */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <Truck className="h-3.5 w-3.5 text-purple-600" /> Active Fleet Missions
              </span>
              <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-extrabold text-purple-800">
                {activeDeliveries}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              In-Transit & Accepted Missions
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              Track courier progress between donor facilities and recipient shelters.
            </p>
          </div>
          <Link
            to="/admin/map"
            className="flex items-center justify-between text-xs font-bold text-purple-700 hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Track on Live Map</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 4. Unmet Community Demands */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-amber-600" /> Unmet Demands
              </span>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-extrabold text-amber-800">
                {unmetRequests}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              Open & Partially Allocated Requests
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              Shelters and community centers waiting for surplus supply matching.
            </p>
          </div>
          <Link
            to="/admin/requests"
            className="flex items-center justify-between text-xs font-bold text-amber-700 hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Inspect Open Demands</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 5. Route Disruptions & Recovery */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-red-600" /> Route Disruptions
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-extrabold ${
                  disruptions > 0 ? 'bg-red-100 text-red-800' : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {disruptions}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              Reported Floods & Impasses
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              Delivery missions paused due to hazards requiring route reassignment or relief escort.
            </p>
          </div>
          <Link
            to="/admin/recovery"
            className="flex items-center justify-between text-xs font-bold text-red-700 hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Run Dynamic Recovery Engine</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 6. Emergency & Disaster Protocol */}
        <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
                <Flame className="h-3.5 w-3.5 text-orange-600" /> Disaster Readiness
              </span>
              <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-extrabold text-orange-800">
                {urgentDisaster > 0 ? `${urgentDisaster} Critical` : 'Ready'}
              </span>
            </div>
            <p className="text-xs text-[#182B25] font-semibold mt-2">
              Relief Protocols & Zones
            </p>
            <p className="text-[11px] text-[#64748B] mt-0.5">
              Emergency mode overrides and distribution hub mobilizations for flash floods and cyclones.
            </p>
          </div>
          <Link
            to="/admin/disasters"
            className="flex items-center justify-between text-xs font-bold text-orange-700 hover:underline pt-2 border-t border-[#E5EAE7]/70"
          >
            <span>Disaster Command Console</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LiveOperationsCenter;
