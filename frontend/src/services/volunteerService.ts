import { Volunteer, VolunteerAvailabilityStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode } from './apiClient';
import { adaptVolunteer } from './apiAdapters';

export const volunteerService = {
  /**
   * Lists registered volunteer couriers.
   */
  async getVolunteers(): Promise<Volunteer[]> {
    if (!isApiMode()) {
      return mockRepository.getVolunteers();
    }

    const res = await apiClient.get<{ count: number; results: any[] } | any[]>('/volunteers/');
    const rawList = Array.isArray(res.data) ? res.data : (res.data?.results || []);
    return rawList.map(adaptVolunteer);
  },

  /**
   * Retrieves volunteer courier profile by ID.
   */
  async getVolunteerById(id: string): Promise<Volunteer | undefined> {
    if (!isApiMode()) {
      const list = mockRepository.getVolunteers();
      return list.find((v) => v.id === id);
    }

    try {
      const res = await apiClient.get(`/volunteers/${id}/`);
      return adaptVolunteer(res.data);
    } catch {
      return undefined;
    }
  },

  /**
   * Retrieves volunteer courier profile associated with an account ID.
   */
  async getVolunteerByUserId(userId: string): Promise<Volunteer | undefined> {
    if (!isApiMode()) {
      const list = mockRepository.getVolunteers();
      return list.find((v) => v.userId === userId);
    }

    const list = await this.getVolunteers();
    return list.find((v) => v.userId === userId);
  },

  /**
   * Toggles courier availability state (available vs offline).
   */
  async setAvailabilityStatus(
    volunteerId: string,
    status: VolunteerAvailabilityStatus
  ): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateVolunteer(volunteerId, { status });
      return;
    }

    await apiClient.post('/volunteers/toggle_availability/', { status });
  },

  /**
   * Coordinator: get unverified volunteers.
   */
  async getPendingVolunteers(): Promise<any[]> {
    if (!isApiMode()) return [];
    try {
      const res = await apiClient.get<any[]>('/volunteers/pending/');
      return res.data || [];
    } catch {
      return [];
    }
  },

  /**
   * Coordinator: approve and verify volunteer.
   */
  async verifyVolunteer(id: string): Promise<boolean> {
    if (!isApiMode()) return true;
    try {
      await apiClient.post(`/volunteers/${id}/verify/`);
      return true;
    } catch {
      return false;
    }
  },
};

export default volunteerService;
