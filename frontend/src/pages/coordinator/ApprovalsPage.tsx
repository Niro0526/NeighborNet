import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Building2,
  Users,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  UserCheck,
} from 'lucide-react';
import { organizationService } from '../../services/organizationService';
import { volunteerService } from '../../services/volunteerService';
import { OrganizationProfile } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';

export const ApprovalsPage: React.FC = () => {
  const [pendingOrgs, setPendingOrgs] = useState<OrganizationProfile[]>([]);
  const [pendingVols, setPendingVols] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [tab, setTab] = useState<'organizations' | 'volunteers'>('organizations');

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [orgs, vols] = await Promise.all([
        organizationService.getPendingOrganizations(),
        volunteerService.getPendingVolunteers(),
      ]);
      setPendingOrgs(orgs);
      setPendingVols(vols);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerifyOrg = async (id: string) => {
    setVerifyingId(id);
    try {
      const success = await organizationService.verifyOrganization(id);
      if (success) {
        setPendingOrgs((prev) => prev.filter((o) => o.id !== id));
      }
    } finally {
      setVerifyingId(null);
    }
  };

  const handleVerifyVol = async (id: string) => {
    setVerifyingId(id);
    try {
      const success = await volunteerService.verifyVolunteer(id);
      if (success) {
        setPendingVols((prev) => prev.filter((v) => v.id !== id));
      }
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5EAE7] pb-4">
        <div>
          <h1 className="text-xl font-extrabold text-[#182B25] flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-[#16866A]" />
            <span>Pilot Onboarding Approvals</span>
          </h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Coordinator human-in-the-loop verification for new organizations and volunteer couriers. No automatic approvals.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] cursor-pointer disabled:opacity-50"
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Pending Summary Bar */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-2xl border border-[#E5EAE7] bg-white p-4 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-[#64748B] uppercase tracking-wider mb-1">
            <Building2 className="h-4 w-4 text-[#16866A]" />
            <span>Pending Organizations</span>
          </div>
          <div className="text-2xl font-extrabold text-[#182B25]">
            {pendingOrgs.length}
          </div>
          <p className="text-[11px] text-[#64748B] mt-1">Restaurants, bakeries, NGOs awaiting verification</p>
        </div>

        <div className="rounded-2xl border border-[#E5EAE7] bg-white p-4 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-bold text-[#64748B] uppercase tracking-wider mb-1">
            <Users className="h-4 w-4 text-blue-600" />
            <span>Pending Volunteers</span>
          </div>
          <div className="text-2xl font-extrabold text-[#182B25]">
            {pendingVols.length}
          </div>
          <p className="text-[11px] text-[#64748B] mt-1">Courier applicants awaiting background checks</p>
        </div>
      </div>

      {/* Tab Toggle */}
      <div className="flex items-center bg-[#F8FAF9] p-1 rounded-xl border border-[#E5EAE7] w-fit">
        <button
          onClick={() => setTab('organizations')}
          className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
            tab === 'organizations'
              ? 'bg-white text-[#182B25] shadow-xs border border-[#E5EAE7]'
              : 'text-[#64748B] hover:text-[#182B25]'
          }`}
        >
          <Building2 className="h-3 w-3" />
          <span>Organizations ({pendingOrgs.length})</span>
        </button>
        <button
          onClick={() => setTab('volunteers')}
          className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
            tab === 'volunteers'
              ? 'bg-white text-[#182B25] shadow-xs border border-[#E5EAE7]'
              : 'text-[#64748B] hover:text-[#182B25]'
          }`}
        >
          <Users className="h-3 w-3" />
          <span>Volunteers ({pendingVols.length})</span>
        </button>
      </div>

      {/* Organizations Tab */}
      {tab === 'organizations' && (
        <div className="space-y-3">
          {pendingOrgs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#E5EAE7] bg-white p-8 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
              <h3 className="text-sm font-bold text-[#182B25]">All Organizations Verified</h3>
              <p className="text-xs text-[#64748B]">No pending organization registrations at this time.</p>
            </div>
          ) : (
            pendingOrgs.map((org) => (
              <div
                key={org.id}
                className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-[#182B25]">{org.name}</h4>
                      <StatusBadge status="pending" size="sm" />
                      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 capitalize">
                        {org.type}
                      </span>
                    </div>
                    <p className="text-xs text-[#64748B] mt-0.5">
                      {org.contactEmail} • {org.contactPhone} • {org.city || 'N/A'}
                    </p>
                  </div>

                  {/* Profile Completion Gauge */}
                  <div className="shrink-0 text-right">
                    <div className="text-[10px] font-bold text-[#64748B] uppercase mb-1">
                      Profile Completeness
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            org.profileCompletion >= 80 ? 'bg-emerald-500' : org.profileCompletion >= 50 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${org.profileCompletion}%` }}
                        />
                      </div>
                      <span className="text-xs font-extrabold text-[#182B25]">
                        {org.profileCompletion}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Missing Fields Warning */}
                {org.missingProfileFields && org.missingProfileFields.length > 0 && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-amber-800">Incomplete Profile Fields:</span>
                      <ul className="mt-0.5 text-[11px] text-amber-700 list-disc pl-4">
                        {org.missingProfileFields.map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Action */}
                <div className="flex items-center justify-between pt-2 border-t border-[#E5EAE7]">
                  <span className="text-[11px] text-[#64748B]">
                    Registration: {org.registrationNumber || 'Not provided'}
                  </span>
                  <button
                    onClick={() => handleVerifyOrg(org.id)}
                    disabled={verifyingId === org.id}
                    className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer disabled:opacity-50"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    <span>{verifyingId === org.id ? 'Verifying...' : 'Approve & Verify'}</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Volunteers Tab */}
      {tab === 'volunteers' && (
        <div className="space-y-3">
          {pendingVols.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#E5EAE7] bg-white p-8 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
              <h3 className="text-sm font-bold text-[#182B25]">All Volunteers Verified</h3>
              <p className="text-xs text-[#64748B]">No pending volunteer registrations at this time.</p>
            </div>
          ) : (
            pendingVols.map((vol) => (
              <div
                key={vol.id}
                className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-bold text-xs capitalize">
                      {(vol.vehicleType || vol.vehicle_type || 'Motorcycle').slice(0, 3)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-[#182B25]">
                          {vol.fullName || vol.full_name || 'Volunteer Courier'}
                        </h4>
                        <StatusBadge status="pending" size="sm" />
                      </div>
                      <p className="text-xs text-[#64748B]">
                        Vehicle: <span className="font-semibold capitalize">{vol.vehicleType || vol.vehicle_type || 'motorcycle'}</span> •
                        Capacity: <span className="font-semibold">{vol.vehicleCapacityKg || vol.vehicle_capacity_kg || 15} kg</span> •
                        Phone: <span className="font-semibold">{vol.phone || 'N/A'}</span>
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleVerifyVol(vol.id)}
                    disabled={verifyingId === vol.id}
                    className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer disabled:opacity-50 shrink-0"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    <span>{verifyingId === vol.id ? 'Verifying...' : 'Approve & Verify'}</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ApprovalsPage;
