import { apiClient, isApiMode } from './apiClient';
import { OrganizationProfile } from '../types';

export const organizationService = {
  async getOrganizations(): Promise<OrganizationProfile[]> {
    if (!isApiMode()) {
      return [];
    }
    const res = await apiClient.get<{ count: number; results: any[] } | any[]>('/organizations/');
    const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
    return list;
  },

  async getOrganizationById(id: string): Promise<OrganizationProfile | undefined> {
    if (!isApiMode()) return undefined;
    try {
      const res = await apiClient.get(`/organizations/${id}/`);
      return res.data;
    } catch {
      return undefined;
    }
  },

  async getPendingOrganizations(): Promise<OrganizationProfile[]> {
    if (!isApiMode()) return [];
    try {
      const res = await apiClient.get<OrganizationProfile[]>('/organizations/pending/');
      return res.data || [];
    } catch {
      return [];
    }
  },

  async verifyOrganization(id: string): Promise<boolean> {
    if (!isApiMode()) return true;
    try {
      await apiClient.post(`/organizations/${id}/verify/`);
      return true;
    } catch {
      return false;
    }
  },

  async updateOrganization(id: string, data: Partial<OrganizationProfile>): Promise<OrganizationProfile> {
    const res = await apiClient.patch(`/organizations/${id}/`, data);
    return res.data;
  },
};

export default organizationService;
