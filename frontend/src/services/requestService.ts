import { ResourceRequest, RequestStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptResourceRequest } from './apiAdapters';

export const requestService = {
  /**
   * Fetches community & emergency resource requests.
   */
  async getResourceRequests(): Promise<ResourceRequest[]> {
    if (!isApiMode()) {
      return mockRepository.getResourceRequests();
    }

    const rawList = await getAllPages('/resource-requests/');
    return rawList.map(adaptResourceRequest).sort((a, b) => b.createdAt.localeCompare(a.createdAt) || b.id.localeCompare(a.id));
  },

  /**
   * Retrieves single requisition by ID.
   */
  async getRequestById(id: string): Promise<ResourceRequest | undefined> {
    if (!isApiMode()) {
      const requests = mockRepository.getResourceRequests();
      return requests.find((r) => r.id === id);
    }

    try {
      const res = await apiClient.get(`/resource-requests/${id}/`);
      return adaptResourceRequest(res.data);
    } catch {
      return undefined;
    }
  },

  /**
   * Filters requests by recipient organization.
   */
  async getRequestsByRecipient(recipientId: string): Promise<ResourceRequest[]> {
    if (!isApiMode()) {
      const requests = mockRepository.getResourceRequests();
      return requests.filter((r) => r.recipientId === recipientId);
    }

    const all = await this.getResourceRequests();
    return all.filter((r) => r.recipientId === recipientId);
  },

  /**
   * Submits a new community or disaster relief resource request.
   */
  async createRequest(
    requestData: Omit<ResourceRequest, 'id' | 'createdAt' | 'status' | 'fulfilledQuantity'>
  ): Promise<ResourceRequest> {
    if (!isApiMode()) {
      const newRequest: ResourceRequest = {
        ...requestData,
        id: `REQ-${Date.now().toString().slice(-4)}`,
        status: 'pending',
        fulfilledQuantity: 0,
        createdAt: new Date().toISOString(),
      };
      mockRepository.addResourceRequest(newRequest);
      return newRequest;
    }

    const payload = {
      item_name: requestData.itemName,
      deliveryAddress: requestData.deliveryAddress || '',
      delivery_latitude: requestData.deliveryLatitude ?? null,
      delivery_longitude: requestData.deliveryLongitude ?? null,
      allow_partial: requestData.allowPartial ?? true,
      category: String(requestData.category || 'cooked_meals').toLowerCase().replace(/[\s-]/g, '_'),
      requestedQuantity: Number(requestData.requestedQuantity),
      unit: requestData.unit || 'meals',
      priority: String(requestData.priority || 'medium').toLowerCase(),
      urgencyDeadline: requestData.urgencyDeadline,
      peopleImpacted: Number(requestData.peopleImpacted || 0),
      specialInstructions: requestData.specialInstructions || '',
      isDisasterRelief: Boolean(requestData.isDisasterRelief),
      disasterEventId: requestData.disasterEventId || null,
    };

    const res = await apiClient.post('/resource-requests/', payload);
    return adaptResourceRequest(res.data);
  },

  /**
   * Cancels an open requisition.
   */
  async cancelRequest(id: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateResourceRequest(id, { status: 'cancelled' });
      return;
    }

    await apiClient.post(`/resource-requests/${id}/cancel/`);
  },

  /**
   * Backward compatibility for status updates.
   */
  async updateRequestStatus(id: string, status: RequestStatus): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateResourceRequest(id, { status });
      return;
    }

    if (status === 'cancelled') {
      await this.cancelRequest(id);
    }
  },
};

export default requestService;
