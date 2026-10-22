import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCircle2,
  Filter,
  RotateCcw,
  Info,
  AlertTriangle,
  Truck,
  Package,
  Flame,
} from 'lucide-react';
import { SystemNotification } from '../../types';
import { notificationService } from '../../services/notificationService';
import { useAuth, useLivePolling } from '../../hooks';

export const NotificationsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [notifications, setNotifications] = useState<SystemNotification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const loadNotifications = async () => {
    const notifs = await notificationService.getNotifications(
      currentUser.assignedRoles[0] || 'FOOD_PROVIDER',
      currentUser.id
    );
    setNotifications(notifs);
  };

  useEffect(() => {
    loadNotifications();
  }, [currentUser.id]);

  useLivePolling({
    fetcher: loadNotifications,
    intervalMs: 15000,
    enabled: true,
  });

  const handleMarkRead = async (id: string) => {
    await notificationService.markAsRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const handleMarkAllRead = async () => {
    await notificationService.markAllAsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const filtered =
    filter === 'unread'
      ? notifications.filter((n) => !n.read)
      : notifications;

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'delivery':
        return <Truck className="h-4 w-4 text-blue-600" />;
      case 'resource':
        return <Package className="h-4 w-4 text-emerald-600" />;
      case 'disaster':
        return <Flame className="h-4 w-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-600" />;
      default:
        return <Info className="h-4 w-4 text-[#16866A]" />;
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5EAE7] pb-4">
        <div>
          <h1 className="text-xl font-extrabold text-[#182B25] flex items-center gap-2">
            <Bell className="h-5 w-5 text-[#16866A]" />
            <span>Notifications</span>
            {unreadCount > 0 && (
              <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-700 border border-red-200">
                {unreadCount} unread
              </span>
            )}
          </h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Real-time platform alerts, courier dispatches, and emergency broadcasts
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadNotifications()}
            className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer disabled:opacity-50"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Mark All Read</span>
          </button>
        </div>
      </div>

      {/* Filter Toggle */}
      <div className="flex items-center bg-[#F8FAF9] p-1 rounded-xl border border-[#E5EAE7] w-fit">
        <button
          onClick={() => setFilter('all')}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
            filter === 'all'
              ? 'bg-white text-[#182B25] shadow-xs border border-[#E5EAE7]'
              : 'text-[#64748B] hover:text-[#182B25]'
          }`}
        >
          <Filter className="h-3 w-3" />
          <span>All ({notifications.length})</span>
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
            filter === 'unread'
              ? 'bg-white text-[#182B25] shadow-xs border border-[#E5EAE7]'
              : 'text-[#64748B] hover:text-[#182B25]'
          }`}
        >
          <Bell className="h-3 w-3" />
          <span>Unread ({unreadCount})</span>
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#E5EAE7] bg-white p-8 text-center">
            <Bell className="mx-auto h-8 w-8 text-[#94A3B8] mb-2" />
            <h3 className="text-sm font-bold text-[#182B25]">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </h3>
            <p className="text-xs text-[#64748B]">
              Alerts will appear here when there are delivery updates, resource changes, or emergency broadcasts.
            </p>
          </div>
        ) : (
          filtered.map((n) => (
            <div
              key={n.id}
              className={`rounded-2xl border p-4 transition-colors ${
                !n.read
                  ? 'border-[#16866A]/30 bg-emerald-50/30 shadow-xs'
                  : 'border-[#E5EAE7] bg-white hover:bg-[#F8FAF9]'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#F8FAF9] border border-[#E5EAE7]">
                  {getTypeIcon(n.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-xs font-bold text-[#182B25]">{n.title}</h4>
                      <p className="text-[11px] text-[#64748B] mt-0.5 leading-relaxed">
                        {n.message}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-[#94A3B8] font-mono whitespace-nowrap">
                        {new Date(n.createdAt).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}{' '}
                        {new Date(n.createdAt).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      {!n.read && (
                        <button
                          onClick={() => handleMarkRead(n.id)}
                          title="Mark as read"
                          className="rounded-lg p-1 text-[#16866A] hover:bg-emerald-100 cursor-pointer"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                  {n.actionUrl && (
                    <a
                      href={n.actionUrl}
                      className="inline-block mt-2 text-[11px] font-bold text-[#16866A] hover:underline"
                    >
                      View Details →
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;
