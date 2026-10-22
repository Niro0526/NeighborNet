import React, { useEffect, useState } from 'react';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { deliveryService } from '../../services/deliveryService';
import { volunteerService } from '../../services/volunteerService';
import { DeliveryTask, Volunteer, DeliveryTaskStatus } from '../../types';
import {
  Truck,
  CheckCircle2,
  Clock,
  Bike,
  Flame,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth, useOperational, useLivePolling } from '../../hooks';
import { isApiMode } from '../../services/apiClient';
import { DeliveryStatusTimeline } from '../../components/delivery/DeliveryStatusTimeline';

export const VolunteerDashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { isDisasterMode, activeDisaster } = useOperational();
  const [volunteer, setVolunteer] = useState<Volunteer | null>(null);
  const [tasks, setTasks] = useState<DeliveryTask[]>([]);
  const [isOnline, setIsOnline] = useState(false);

  const refreshData = async () => {
    let vol = await volunteerService.getVolunteerByUserId(currentUser.id);
    if (!vol && !isApiMode()) {
      vol = await volunteerService.getVolunteerById('VOL-001');
    }
    if (vol) {
      setVolunteer(vol);
      setIsOnline(vol.status !== 'offline');
    }
    const allTasks = await deliveryService.getDeliveryTasks();
    setTasks(allTasks);
  };

  useLivePolling({
    fetcher: refreshData,
    intervalMs: 15000,
    enabled: true,
  });


  useEffect(() => {
    let active = true;
    (async () => {
      let vol = await volunteerService.getVolunteerByUserId(currentUser.id);
      if (!vol && !isApiMode()) {
        vol = await volunteerService.getVolunteerById('VOL-001');
      }
      const allTasks = await deliveryService.getDeliveryTasks();
      if (!active) return;
      if (vol) {
        setVolunteer(vol);
        setIsOnline(vol.status !== 'offline');
      }
      setTasks(allTasks);
    })();

    return () => {
      active = false;
    };
  }, [currentUser.id]);

  const toggleAvailability = async () => {
    const next = !isOnline;
    if (volunteer) {
      try {
        await volunteerService.setAvailabilityStatus(volunteer.id, next ? 'available' : 'offline');
        setIsOnline(next);
      } catch (err: any) {
        alert(err.message || 'Availability was not saved.');
      }
    }
  };

  // Find active task for this volunteer
  const currentVolunteerId = volunteer?.id || (isApiMode() ? '' : 'VOL-001');

  const activeTask = tasks.find(
    (t) =>
      t.volunteerId === currentVolunteerId &&
      t.status !== 'DELIVERED' &&
      t.status !== 'DECLINED' &&
      t.status !== 'CANCELLED'
  );

  const availableTasks = tasks.filter((t) => t.status === 'AVAILABLE' && (!isApiMode() || t.allocationStatus==='APPROVED') && new Date(t.deliveryDeadline) > new Date());

  const handleTaskAction = async (taskId: string, nextStatus: DeliveryTaskStatus) => {
    try {
      await deliveryService.updateTaskStatus(taskId, nextStatus, {
        volunteerId: currentVolunteerId,
        volunteerName: volunteer?.fullName || currentUser.name,
      });
      await refreshData();
    } catch (e: any) {
      alert(e.message || 'Error updating task state');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Mobile Optimized Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5EAE7]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-[#182B25]">
              Hello, {volunteer?.fullName || currentUser.name}!
            </h1>
            <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
              {volunteer?.badge || 'Rapid Delivery'}
            </span>
          </div>
          <p className="text-xs text-[#64748B]">
            Vehicle: <span className="font-semibold text-[#182B25] capitalize">{volunteer?.vehicleType || 'Unavailable'}</span> ({volunteer?.vehicleCapacityKg ?? 0} kg max)
          </p>
        </div>

        {/* Online / Offline Availability Toggle */}
        <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-[#E5EAE7] shadow-xs">
          <span className="text-xs font-bold text-[#182B25]">
            {volunteer?.status === 'busy' ? 'Busy — Delivery in Progress' : isOnline ? 'Online & Available' : 'Offline'}
          </span>
          <button
            onClick={toggleAvailability}
            disabled={volunteer?.status === 'busy'}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              isOnline ? 'bg-[#16866A]' : 'bg-slate-300'
            }`}
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition duration-200 ease-in-out ${
                isOnline ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Contextual Disaster Relief Mobilization Banner */}
      {isDisasterMode && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
          <Flame className="h-5 w-5 text-red-600 shrink-0 mt-0.5 animate-bounce" />
          <div className="text-xs">
            <span className="font-bold text-red-800">
              Disaster Response Emergency Active — {activeDisaster?.title || 'Active emergency'}
            </span>
            <p className="text-red-700/80 mt-0.5">
              {activeDisaster?.description}
            </p>
          </div>
        </div>
      )}

      {/* Quick Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          title="Completed"
          value={volunteer?.completedDeliveriesCount ?? 0}
          subtitle="Total successful runs"
          icon={CheckCircle2}
          variant="emerald"
        />
        <StatCard
          title="Courier Rating"
          value={`${volunteer?.rating ? volunteer.rating.toFixed(1) : '5.0'} ★`}
          subtitle="Verified responder"
          icon={Bike}
          variant="amber"
        />
        <StatCard
          title="Current Tasks"
          value={activeTask ? '1 Active' : 'None'}
          subtitle={activeTask ? activeTask.status.replace('_', ' ') : 'Ready to accept'}
          icon={Truck}
          variant="blue"
        />
        <StatCard
          title="Available Tasks"
          value={availableTasks.length}
          subtitle="In your radius"
          icon={Clock}
          variant="default"
        />
      </div>

      {/* Active Delivery State Machine Card (If task is currently assigned) */}
      {activeTask ? (
        <DeliveryStatusTimeline
          task={activeTask}
          isCourierView={true}
          onTaskUpdated={() => refreshData()}
        />
      ) : (
        <div className="rounded-2xl border border-dashed border-[#E5EAE7] bg-white p-6 text-center">
          <Truck className="mx-auto h-8 w-8 text-[#94A3B8] mb-2" />
          <h3 className="text-sm font-bold text-[#182B25]">No Active Deliveries Assigned</h3>
          <p className="text-xs text-[#64748B]">
            You are ready to accept new runs below.
          </p>
        </div>
      )}

      {/* Available Tasks Section */}
      {tasks.filter(task=>task.volunteerId===currentVolunteerId && task.status==='DELIVERED').slice(0,3).map(task=><div key={task.id} className="rounded-xl border border-[#E5EAE7] bg-white p-3 text-xs"><strong>{task.title} · {task.id}</strong><p>Delivered: {task.statusTimestamps.delivered ? new Date(task.statusTimestamps.delivered).toLocaleString() : 'Timestamp not recorded'}</p><p>NGO receipt: {task.statusTimestamps.receiptConfirmed ? new Date(task.statusTimestamps.receiptConfirmed).toLocaleString() : 'Awaiting NGO confirmation'}</p></div>)}
      <div className="rounded-2xl bg-white p-5 border border-[#E5EAE7] shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5EAE7]">
          <div>
            <h3 className="text-sm font-bold text-[#182B25]">Available Volunteer Runs</h3>
            <p className="text-xs text-[#64748B]">Nearby requests matching your vehicle capacity</p>
          </div>
          <Link to="/volunteer/tasks" className="text-xs font-semibold text-[#16866A] hover:underline">
            View All ({availableTasks.length})
          </Link>
        </div>

        <div className="mt-4 space-y-3">
          {availableTasks.map((t) => (
            <div key={t.id} className="rounded-2xl border border-[#E5EAE7] p-4 bg-[#F8FAF9] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={t.priority} size="sm" />
                  <span className="text-[11px] font-bold text-[#182B25]">{t.quantityDescription}</span>
                </div>
                <h4 className="mt-1 text-xs font-bold text-[#182B25]">{t.title}</h4>
                <p className="text-[11px] text-[#64748B] mt-0.5">
                  Pickup: {t.pickupLocationName} ➔ Delivery: {t.deliveryLocationName}
                </p>
                <div className="mt-1 flex items-center gap-3 text-[10px] text-[#64748B]">
                  <span>{t.estimatedDistanceKm ? `Est. ${t.estimatedDistanceKm} km` : 'Distance not recorded'}</span>
                  <span>•</span>
                  <span>~{t.estimatedDurationMin} mins transit</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleTaskAction(t.id, 'ACCEPTED')}
                  className="rounded-xl bg-[#16866A] px-4 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-xs cursor-pointer"
                >
                  Accept Mission
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
