import { SystemNotification, UserRole } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptNotification } from './apiAdapters';

export const notificationService = {
  /**
   * Fetches user notifications.
   */
  async getNotifications(role?: UserRole, userId?: string): Promise<SystemNotification[]> {
    if (!isApiMode()) {
      const all = mockRepository.getNotifications();
      if (!role && !userId) return all;
      return all.filter((n) => {
        if (n.targetRole === 'ALL') return true;
        if (role && n.targetRole === role) return true;
        if (userId && n.targetUserId === userId) return true;
        return false;
      });
    }

    try {
      const rawList = await getAllPages('/notifications/');
      return rawList.map(adaptNotification);
    } catch {
      return [];
    }
  },

  /**
   * Fetches unread notification count.
   */
  async getUnreadCount(): Promise<number> {
    if (!isApiMode()) {
      const all = mockRepository.getNotifications();
      return all.filter((n) => !n.read).length;
    }

    try {
      const res = await apiClient.get<{ unreadCount: number }>('/notifications/unread_count/');
      return res.data?.unreadCount ?? 0;
    } catch {
      return 0;
    }
  },

  /**
   * Marks a single notification as read.
   */
  async markAsRead(id: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.markNotificationAsRead(id);
      return;
    }

    await apiClient.post(`/notifications/${id}/mark_read/`);
  },

  /**
   * Marks all user notifications as read.
   */
  async markAllAsRead(): Promise<void> {
    if (!isApiMode()) {
      mockRepository.markAllNotificationsAsRead();
      return;
    }

    await apiClient.post('/notifications/mark_all_read/');
  },
};

export default notificationService;
