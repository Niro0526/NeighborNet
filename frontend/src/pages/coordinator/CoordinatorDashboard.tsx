import React, { useEffect, useState } from 'react';
import { PageHeader } from '../../components/common/PageHeader';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { useOperational } from '../../hooks';
import { analyticsService } from '../../services/analyticsService';
import { foodService } from '../../services/foodService';
import { allocationService } from '../../services/allocationService';
import { DashboardStats, FoodListing, AIInsight, ActivityLog } from '../../types';
import {
  Package,
  ShoppingBag,
  Users,
  Truck,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  Flame,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { isApiMode } from '../../services/apiClient';

import { LiveOperationsCenter } from '../../components/coordinator/LiveOperationsCenter';

export const CoordinatorDashboard: React.FC = () => {
  const { isDisasterMode, activeDisaster } = useOperational();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [foodListings, setFoodListings] = useState<FoodListing[]>([]);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [activities, setActivities] = useState<ActivityLog[]>([]);

  useEffect(() => {
    analyticsService.getDashboardStats().then(setStats);
    foodService.getFoodListings().then(setFoodListings);
    allocationService.getAIInsights().then(setInsights);
    analyticsService.getActivityLogs().then(setActivities);
  }, [isDisasterMode]);

  const expiringSoon = foodListings.filter(
    (f) => f.status === 'available' || f.status === 'reserved'
  ).slice(0, 3);

  const topInsight = insights.find((i) => i.status === 'pending') || insights[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDisasterMode ? 'Disaster Response Command Dashboard' : 'Coordinator Overview'}
        subtitle={
          isDisasterMode
            ? `Emergency relief protocol active: ${activeDisaster?.title || 'Monsoon Flash Floods'}`
            : 'Real-time summary of surplus food inventory, community requests, and courier dispatches'
        }
        badge={
          isDisasterMode ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-extrabold text-red-700 animate-pulse border border-red-200">
              <Flame className="h-3.5 w-3.5" />
              DISASTER MODE ACTIVE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 border border-emerald-200">
              Normal Community Mode
            </span>
          )
        }
        action={
          <div className="flex items-center gap-2">
            <Link
              to="/admin/matching"
              className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Review AI Matches</span>
            </Link>
          </div>
        }
      />

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Available Food Surplus"
          value={`${stats?.totalFoodRescuedKg ?? 0} kg`}
          subtitle="Saved from landfill this cycle"
          icon={Package}
          trend={{ value: 'Real-time verified', isPositive: true }}
          variant="emerald"
        />
        <StatCard
          title="Active Requests"
          value={stats?.activeRequestsCount ?? 0}
          subtitle={`${stats?.urgentRequestsCount ?? 0} urgent priorities`}
          icon={ShoppingBag}
          trend={stats?.urgentRequestsCount ? { value: `${stats.urgentRequestsCount} urgent`, isPositive: false } : undefined}
          variant="red"
        />
        <StatCard
          title="Volunteers Online"
          value={stats?.volunteersOnlineCount ?? 0}
          subtitle="Moratuwa & Colombo area"
          icon={Users}
          trend={{ value: 'Active couriers', isPositive: true }}
          variant="amber"
        />
        <StatCard
          title="Deliveries Completed"
          value={stats?.deliveriesTodayCount ?? 0}
          subtitle="Safe transit confirmed"
          icon={Truck}
          trend={{ value: 'Verified delivery', isPositive: true }}
          variant="blue"
        />
      </div>

      {/* Coordinator Live Operations Center */}
      <LiveOperationsCenter />


      {/* AI Recommendation Highlight Banner */}
      {topInsight && (
        <div className="rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50/80 to-teal-50/60 p-5 shadow-xs">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#16866A] text-white shadow-xs">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md">
                    {isApiMode() ? 'OR-Tools Recommendation — Optimization Engine' : 'Demo Recommendation — Simulated'}
                  </span>
                  <StatusBadge status={topInsight.priority} size="sm" />
                </div>
                <h4 className="mt-1 text-sm font-extrabold text-[#182B25]">{topInsight.title}</h4>
                <p className="text-xs text-[#64748B] max-w-2xl mt-0.5">{topInsight.description}</p>
              </div>
            </div>
            <Link
              to="/admin/matching"
              className="flex shrink-0 items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] transition-colors"
            >
              <span>View Rationale & Dispatch</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Main Split: Expiry Risks & Live Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Food at Risk of Expiry */}
        <div className="lg:col-span-7 rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-600" />
              <h3 className="text-sm font-bold text-[#182B25]">Food at Risk of Expiry</h3>
            </div>
            <Link to="/admin/resources" className="text-xs font-semibold text-[#16866A] hover:underline">
              View All
            </Link>
          </div>

          <div className="mt-4 space-y-3">
            {expiringSoon.map((food) => (
              <div
                key={food.id}
                className="flex items-center justify-between rounded-xl border border-[#E5EAE7] p-3.5 hover:bg-[#F8FAF9] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700 font-bold text-xs">
                    {food.quantity} {food.unit}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-[#182B25] line-clamp-1">{food.name}</h4>
                    <p className="text-[11px] text-[#64748B]">{food.providerName} • {food.storageRequirements}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={food.status} size="sm" />
                  <Link
                    to="/admin/matching"
                    className="rounded-lg bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-[#16866A] hover:bg-emerald-100"
                  >
                    Match
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Audit & Activity Stream */}
        <div className="lg:col-span-5 rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
            <h3 className="text-sm font-bold text-[#182B25]">Recent System Activity</h3>
            <Link to="/admin/audit" className="text-xs font-semibold text-[#16866A] hover:underline">
              Audit Trail
            </Link>
          </div>

          <div className="mt-4 space-y-3.5">
            {activities.slice(0, 4).map((act) => (
              <div key={act.id} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[#16866A]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-[#182B25]">{act.details}</p>
                  <p className="text-[10px] text-[#64748B] mt-0.5">
                    {act.userName} • {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
