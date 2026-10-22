import React, { useState, useEffect } from 'react';
import {
  User as UserIcon,
  Building2,
  ShieldCheck,
  MapPin,
  Edit3,
  AlertTriangle,
  Save,
} from 'lucide-react';
import { useAuth } from '../../hooks';
import { apiClient, isApiMode } from '../../services/apiClient';
import { OrganizationProfile } from '../../types';
import { MatchingPreferences } from '../../components/coordinator/MatchingPreferences';

export const ProfilePage: React.FC = () => {
  const { currentUser, assignedRoles } = useAuth();
  const [organization, setOrganization] = useState<OrganizationProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<OrganizationProfile>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isApiMode()) {
      apiClient.get('/organizations/my_organizations/').then((res) => {
        const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        if (list.length > 0) {
          const preferred = assignedRoles.includes('RECIPIENT') ? list.find((org: any) => ['NGO', 'SHELTER', 'FOOD_BANK', 'COMMUNITY_KITCHEN', 'RELIEF_CENTER'].includes(org.type)) || list[0] : list[0];
          setOrganization(preferred);
          setEditForm(preferred);
        }
      }).catch(() => {});
    }
  }, []);

  const handleSave = async () => {
    if (!organization?.id || !isApiMode()) return;
    setIsSaving(true);
    try {
      const res = await apiClient.patch(`/organizations/${organization.id}/`, editForm);
      setOrganization(res.data);
      setIsEditing(false);
    } catch {
      // Handle error silently
    } finally {
      setIsSaving(false);
    }
  };

  const profileCompletion = organization?.profileCompletion ?? 0;
  const missingFields = organization?.missingProfileFields ?? [];
  const isVerified = organization?.verified ?? false;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {organization?.id && assignedRoles.includes('RECIPIENT') && <MatchingPreferences organizationId={organization.id} />}
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5EAE7] pb-4">
        <div>
          <h1 className="text-xl font-extrabold text-[#182B25] flex items-center gap-2">
            <UserIcon className="h-5 w-5 text-[#16866A]" />
            <span>User Profile & Organization</span>
          </h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Account identity, organization verification status, and profile completeness for pilot readiness
          </p>
        </div>
      </div>

      {/* User Identity Card */}
      <div className="rounded-3xl border border-[#E5EAE7] bg-white p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-4">
          {currentUser.avatarUrl ? (
            <img
              src={currentUser.avatarUrl}
              alt={currentUser.name}
              className="h-16 w-16 rounded-2xl object-cover ring-2 ring-[#16866A]/20"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#16866A] text-white text-xl font-bold">
              {currentUser.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-extrabold text-[#182B25]">{currentUser.name}</h2>
              {isVerified && (
                <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
                  <ShieldCheck className="h-3 w-3" />
                  Verified
                </span>
              )}
              {!isVerified && organization && (
                <span className="flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-200">
                  <AlertTriangle className="h-3 w-3" />
                  Pending Verification
                </span>
              )}
            </div>
            <p className="text-xs text-[#64748B] mt-0.5">{currentUser.email}</p>
            <div className="flex items-center gap-2 mt-1.5">
              {assignedRoles.map((role) => (
                <span
                  key={role}
                  className="rounded-md bg-[#F8FAF9] border border-[#E5EAE7] px-2 py-0.5 text-[10px] font-semibold text-[#182B25] capitalize"
                >
                  {role.replace('_', ' ').toLowerCase()}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Organization Profile & Completeness */}
      {organization && (
        <div className="rounded-3xl border border-[#E5EAE7] bg-white p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-[#E5EAE7] pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-[#16866A]" />
              <h3 className="text-base font-bold text-[#182B25]">Organization Profile</h3>
            </div>
            <div className="flex items-center gap-2">
              {/* Profile Completion Gauge */}
              <div className="flex items-center gap-2 mr-3">
                <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full ${
                      profileCompletion >= 80 ? 'bg-emerald-500' : profileCompletion >= 50 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${profileCompletion}%` }}
                  />
                </div>
                <span className="text-xs font-extrabold text-[#182B25]">{profileCompletion}%</span>
              </div>

              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] cursor-pointer"
                >
                  <Edit3 className="h-3.5 w-3.5" />
                  <span>Edit Profile</span>
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsEditing(false)}
                    className="rounded-xl border border-[#E5EAE7] px-3 py-1.5 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAF9] cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer disabled:opacity-50"
                  >
                    <Save className="h-3.5 w-3.5" />
                    <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Missing Fields Warning */}
          {missingFields.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-amber-800">
                  Complete these fields for pilot readiness ({missingFields.length} remaining):
                </span>
                <ul className="mt-1 text-[11px] text-amber-700 list-disc pl-4 space-y-0.5">
                  {missingFields.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Profile Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl bg-[#F8FAF9] p-4 border border-[#E5EAE7] space-y-3">
              <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1">
                <Building2 className="h-3 w-3" /> Organization Details
              </span>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Name:</span>
                  <span className="font-semibold text-[#182B25]">{organization.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Type:</span>
                  <span className="font-semibold text-[#182B25] capitalize">{organization.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Registration #:</span>
                  {isEditing ? (
                    <input
                      value={editForm.registrationNumber || ''}
                      onChange={(e) => setEditForm({ ...editForm, registrationNumber: e.target.value })}
                      className="w-32 rounded-lg border border-[#E5EAE7] px-2 py-0.5 text-xs text-right"
                    />
                  ) : (
                    <span className="font-semibold text-[#182B25]">{organization.registrationNumber || '—'}</span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Capacity:</span>
                  <span className="font-semibold text-[#182B25]">{organization.capacity || '—'}</span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl bg-[#F8FAF9] p-4 border border-[#E5EAE7] space-y-3">
              <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1">
                <MapPin className="h-3 w-3" /> Contact & Location
              </span>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Email:</span>
                  <span className="font-semibold text-[#182B25]">{organization.contactEmail}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Phone:</span>
                  <span className="font-semibold text-[#182B25]">{organization.contactPhone || '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Address:</span>
                  <span className="font-semibold text-[#182B25] text-right max-w-[150px] truncate">
                    {organization.address || '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Service Area:</span>
                  {isEditing ? (
                    <input
                      value={editForm.serviceArea || ''}
                      onChange={(e) => setEditForm({ ...editForm, serviceArea: e.target.value })}
                      className="w-32 rounded-lg border border-[#E5EAE7] px-2 py-0.5 text-xs text-right"
                    />
                  ) : (
                    <span className="font-semibold text-[#182B25]">{organization.serviceArea || '—'}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No organization fallback */}
      {!organization && !isApiMode() && (
        <div className="rounded-2xl border border-dashed border-[#E5EAE7] bg-white p-8 text-center">
          <Building2 className="mx-auto h-8 w-8 text-[#94A3B8] mb-2" />
          <h3 className="text-sm font-bold text-[#182B25]">No Organization Linked</h3>
          <p className="text-xs text-[#64748B]">
            Your account is not yet associated with a registered organization. Contact a Coordinator for assistance.
          </p>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
