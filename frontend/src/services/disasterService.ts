import { DisasterEvent, OperationalMode } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptDisasterEvent } from './apiAdapters';

export const disasterService = {
  /**
   * Lists all disaster events.
   */
  async getDisasterEvents(): Promise<DisasterEvent[]> {
    if (!isApiMode()) {
      return mockRepository.getDisasterEvents();
    }

    const rawList = await getAllPages('/disasters/');
    return rawList.map(adaptDisasterEvent);
  },

  /**
   * Retrieves the currently active disaster emergency event, if any.
   */
  async getActiveDisasterEvent(): Promise<DisasterEvent | undefined> {
    if (!isApiMode()) {
      const list = mockRepository.getDisasterEvents();
      return list.find((d) => d.status === 'active');
    }

    try {
      const res = await apiClient.get('/disasters/active/');
      if (res.data && res.data.id && res.data.status !== 'RESOLVED' && res.data.status !== 'CLOSED') {
        return adaptDisasterEvent(res.data);
      }
      return undefined;
    } catch (error: any) {
      if (error.statusCode === 401 || error.statusCode === 403) return undefined;
      throw error;
    }
  },

  /**
   * Returns current operational mode (NORMAL vs DISASTER) based on database event state.
   */
  async getOperationalMode(): Promise<OperationalMode> {
    if (!isApiMode()) {
      return mockRepository.getOperationalMode();
    }

    const active = await this.getActiveDisasterEvent();
    return active ? 'DISASTER' : 'NORMAL';
  },

  async setOperationalMode(mode: OperationalMode): Promise<void> {
    if (!isApiMode()) {
      mockRepository.setOperationalMode(mode);
      return;
    }
    const events = await this.getDisasterEvents();
    if (mode === 'NORMAL') {
      for (const event of events.filter((event) => event.status === 'active')) {
        await this.resolveDisaster(event.id);
      }
    } else {
      if (events.some((event) => event.status === 'active')) return;
      const draft = events.find((event) => event.status === 'monitoring');
      if (draft) {
        await this.activateDisaster(draft.id);
      } else {
        const res = await apiClient.post('/disasters/', {
          title: 'Emergency Response — Moratuwa & Colombo South',
          description: 'Emergency response activated by the coordinator.',
          disasterType: 'flood', severity: 'high', status: 'DRAFT',
          affectedLocation: 'Moratuwa & Colombo South', affectedPopulation: 0,
        });
        await this.activateDisaster(res.data.id);
      }
    }
  },

  /**
   * Activates emergency response protocol for a disaster event.
   * Strictly restricted to Coordinators on the backend.
   */
  async activateDisaster(eventId: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateDisasterEvent(eventId, { status: 'active' });
      mockRepository.setOperationalMode('DISASTER');
      return;
    }

    await apiClient.post(`/disasters/${eventId}/activate/`);
  },

  /**
   * Resolves an emergency response event.
   * Strictly restricted to Coordinators on the backend.
   */
  async resolveDisaster(eventId: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateDisasterEvent(eventId, { status: 'resolved' });
      const others = mockRepository.getDisasterEvents().filter((d) => d.id !== eventId && d.status === 'active');
      if (others.length === 0) {
        mockRepository.setOperationalMode('NORMAL');
      }
      return;
    }

    await apiClient.post(`/disasters/${eventId}/resolve/`);
  },
};

export default disasterService;
