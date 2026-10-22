import { DeliveryTask, DeliveryTaskStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptDeliveryTask } from './apiAdapters';

const VALID_TRANSITIONS: Record<DeliveryTaskStatus, DeliveryTaskStatus[]> = {
  AVAILABLE: ['ACCEPTED', 'CANCELLED'],
  ACCEPTED: ['ARRIVED_PICKUP', 'DECLINED', 'CANCELLED', 'DISRUPTED'],
  ARRIVED_PICKUP: ['PICKED_UP', 'CANCELLED', 'DISRUPTED'],
  PICKED_UP: ['ARRIVED_DELIVERY', 'DISRUPTED'],
  ARRIVED_DELIVERY: ['DELIVERED', 'DISRUPTED'],
  DELIVERED: [],
  DECLINED: ['AVAILABLE'],
  CANCELLED: [],
  DISRUPTED: ['ARRIVED_PICKUP', 'PICKED_UP', 'ARRIVED_DELIVERY', 'CANCELLED'],
};

export const deliveryService = {
  async confirmReceipt(taskId: string): Promise<DeliveryTask> {
    if (!isApiMode()) throw new Error('Verified receipt confirmation requires API mode.');
    const response=await apiClient.post(`/delivery-tasks/${taskId}/confirm_receipt/`);
    return adaptDeliveryTask(response.data.task);
  },
  /**
   * Fetches delivery tasks across all states.
   */
  async getDeliveryTasks(): Promise<DeliveryTask[]> {
    if (!isApiMode()) {
      return mockRepository.getDeliveryTasks();
    }

    try {
      const rawList = await getAllPages('/delivery-tasks/');
      return rawList.map(adaptDeliveryTask);
    } catch {
      return [];
    }
  },

  /**
   * Retrieves single delivery task by ID.
   */
  async getTaskById(id: string): Promise<DeliveryTask | undefined> {
    if (!isApiMode()) {
      const tasks = mockRepository.getDeliveryTasks();
      return tasks.find((t) => t.id === id);
    }

    try {
      const res = await apiClient.get(`/delivery-tasks/${id}/`);
      return adaptDeliveryTask(res.data);
    } catch {
      return undefined;
    }
  },

  /**
   * Retrieves tasks claimed by or assigned to a volunteer courier.
   */
  async getTasksForVolunteer(volunteerId: string): Promise<DeliveryTask[]> {
    if (!isApiMode()) {
      const tasks = mockRepository.getDeliveryTasks();
      return tasks.filter((t) => t.volunteerId === volunteerId);
    }

    const all = await this.getDeliveryTasks();
    return all.filter((t) => t.volunteerId === volunteerId);
  },

  /**
   * Advances delivery lifecycle state via backend transition endpoints.
   */
  async updateTaskStatus(
    taskId: string,
    newStatus: DeliveryTaskStatus,
    extraData?: { volunteerId?: string; volunteerName?: string; disruptionReason?: string }
  ): Promise<DeliveryTask> {
    if (!isApiMode()) {
      const task = await this.getTaskById(taskId);
      if (!task) {
        throw new Error(`Task with ID ${taskId} not found`);
      }

      const allowed = VALID_TRANSITIONS[task.status];
      if (allowed && !allowed.includes(newStatus)) {
        throw new Error(`Invalid status transition from ${task.status} to ${newStatus}`);
      }

      const now = new Date().toISOString();
      const timestamps = { ...task.statusTimestamps };

      if (newStatus === 'ACCEPTED') timestamps.accepted = now;
      if (newStatus === 'ARRIVED_PICKUP') timestamps.arrivedPickup = now;
      if (newStatus === 'PICKED_UP') timestamps.pickedUp = now;
      if (newStatus === 'ARRIVED_DELIVERY') timestamps.arrivedDelivery = now;
      if (newStatus === 'DELIVERED') timestamps.delivered = now;

      const updates: Partial<DeliveryTask> = {
        status: newStatus,
        statusTimestamps: timestamps,
        ...(extraData || {}),
      };

      mockRepository.updateDeliveryTask(taskId, updates);
      return { ...task, ...updates };
    }

    // Call designated Django state transition endpoint
    let res: any;
    if (newStatus === 'ACCEPTED') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/accept/`);
    } else if (newStatus === 'ARRIVED_PICKUP') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/arrived_pickup/`);
    } else if (newStatus === 'PICKED_UP') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/pickup/`);
    } else if (newStatus === 'ARRIVED_DELIVERY') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/arrived_delivery/`);
    } else if (newStatus === 'DELIVERED') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/complete/`);
    } else if (newStatus === 'DISRUPTED') {
      res = await apiClient.post(`/delivery-tasks/${taskId}/disrupt/`, {
        reason: extraData?.disruptionReason || 'Route hazard or heavy flooding encountered',
      });
    } else {
      throw new Error(`Unsupported delivery action: ${newStatus}`);
    }

    const taskData = res.data?.task || res.data;
    return adaptDeliveryTask(taskData);
  },
};

export default deliveryService;
