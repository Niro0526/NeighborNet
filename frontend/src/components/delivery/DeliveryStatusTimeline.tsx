import React, { useState } from 'react';
import { DeliveryTask, DeliveryTaskStatus } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import {
  CheckCircle2,
  Clock,
  MapPin,
  AlertTriangle,
  Phone,
  ShieldCheck,
  ChevronRight,
  History,
} from 'lucide-react';
import { deliveryService } from '../../services/deliveryService';

interface DeliveryStatusTimelineProps {
  task: DeliveryTask;
  isCourierView?: boolean;
  onTaskUpdated?: (updatedTask: DeliveryTask) => void;
}

interface StepConfig {
  key: DeliveryTaskStatus | 'CREATED';
  label: string;
  description: string;
  timestamp?: string;
  isDone: boolean;
  isCurrent: boolean;
}

export const DeliveryStatusTimeline: React.FC<DeliveryStatusTimelineProps> = ({
  task,
  isCourierView = false,
  onTaskUpdated,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDisruptionModal, setShowDisruptionModal] = useState(false);
  const [disruptionReason, setDisruptionReason] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const formatTime = (ts?: string) => {
    if (!ts) return null;
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' +
        d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return ts;
    }
  };

  const status = task.status;
  const isDisrupted = status === 'DISRUPTED';
  const isCancelled = status === 'CANCELLED';

  const steps: StepConfig[] = [
    {
      key: 'CREATED',
      label: 'Mission Created',
      description: 'Allocation generated and published',
      timestamp: task.statusTimestamps.created,
      isDone: true,
      isCurrent: status === 'AVAILABLE',
    },
    {
      key: 'ACCEPTED',
      label: 'Courier Assigned',
      description: task.volunteerName ? `Assigned to ${task.volunteerName}` : 'Accepted by responder',
      timestamp: task.statusTimestamps.accepted,
      isDone: Boolean(task.statusTimestamps.accepted),
      isCurrent: status === 'ACCEPTED',
    },
    {
      key: 'ARRIVED_PICKUP',
      label: 'Arrived at Pickup',
      description: task.pickupLocationName || 'At supplier depot',
      timestamp: task.statusTimestamps.arrivedPickup,
      isDone: Boolean(task.statusTimestamps.arrivedPickup),
      isCurrent: status === 'ARRIVED_PICKUP',
    },
    {
      key: 'PICKED_UP',
      label: 'Cargo Loaded & In Transit',
      description: task.cargoDescription || 'Surplus goods secured',
      timestamp: task.statusTimestamps.pickedUp,
      isDone: Boolean(task.statusTimestamps.pickedUp),
      isCurrent: status === 'PICKED_UP',
    },
    {
      key: 'ARRIVED_DELIVERY',
      label: 'Arrived at Recipient',
      description: task.deliveryLocationName || 'At destination shelter',
      timestamp: task.statusTimestamps.arrivedDelivery,
      isDone: Boolean(task.statusTimestamps.arrivedDelivery),
      isCurrent: status === 'ARRIVED_DELIVERY',
    },
    {
      key: 'DELIVERED',
      label: 'Delivered',
      description: 'Delivery recorded; NGO receipt is confirmed separately',
      timestamp: task.statusTimestamps.delivered,
      isDone: Boolean(task.statusTimestamps.delivered),
      isCurrent: status === 'DELIVERED',
    },
  ];

  const handleTransition = async (nextStatus: DeliveryTaskStatus, extra?: { disruptionReason?: string }) => {
    setIsSubmitting(true);
    setActionError(null);
    try {
      const updated = await deliveryService.updateTaskStatus(task.id, nextStatus, {
        volunteerId: task.volunteerId,
        volunteerName: task.volunteerName,
        ...extra,
      });
      if (onTaskUpdated) {
        onTaskUpdated(updated);
      }
      setShowDisruptionModal(false);
      setDisruptionReason('');
    } catch (err: any) {
      setActionError(err.message || 'Failed to update delivery status');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-3xl border border-[#E5EAE7] bg-white p-5 shadow-sm space-y-6">
      {/* Header Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E5EAE7]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-extrabold text-[#182B25]">{task.title}</h3>
            <StatusBadge status={task.status} />
            {task.isDisasterMode && (
              <span className="rounded-md bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">
                Disaster Route
              </span>
            )}
          </div>
          <p className="text-xs text-[#64748B] mt-1">
            Tracking ID: <span className="font-mono text-[#182B25]">{task.id}</span> • Cargo: <span className="font-semibold text-[#16866A]">{task.cargoDescription}</span> ({task.quantityDescription})
          </p>
        </div>

        {task.volunteerName && (
          <div className="flex items-center gap-2 bg-[#F8FAF9] px-3 py-1.5 rounded-xl border border-[#E5EAE7]">
            <ShieldCheck className="h-4 w-4 text-[#16866A]" />
            <div className="text-xs">
              <span className="text-[10px] text-[#64748B] block uppercase tracking-wider font-semibold">Assigned Courier</span>
              <span className="font-bold text-[#182B25]">{task.volunteerName}</span>
            </div>
          </div>
        )}
      </div>

      {actionError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Disruption Alert if in disrupted state */}
      {isDisrupted && (
        <div className="rounded-2xl border border-red-300 bg-red-50/80 p-4">
          <div className="flex items-center gap-2 text-red-800 font-bold text-sm">
            <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
            <span>Delivery Disruption Reported</span>
          </div>
          <p className="text-xs text-red-700 mt-1">
            Reason: <span className="font-semibold">{task.disruptionReason || 'Encountered obstruction or impassable road'}</span>
          </p>
          <p className="text-[11px] text-red-600/80 mt-1">
            The Coordinator Live Operations Center has been flagged for route reassignment or recovery.
          </p>
        </div>
      )}

      {/* Verified Status Timeline Stepper */}
      <div className="space-y-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#64748B] flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5" />
          <span>Lifecycle Timeline (Recorded Timestamps)</span>
        </h4>

        <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#E5EAE7]">
          {steps.map((s, idx) => {
            const hasTimestamp = Boolean(s.timestamp);
            return (
              <div key={idx} className="relative flex items-start gap-4">
                {/* Step Circle */}
                <div
                  className={`absolute -left-6 flex h-5 w-5 items-center justify-center rounded-full border-2 text-[10px] font-bold ${
                    s.isDone
                      ? 'border-[#16866A] bg-[#16866A] text-white shadow-xs'
                      : s.isCurrent
                      ? 'border-[#16866A] bg-white text-[#16866A] ring-4 ring-[#16866A]/10'
                      : 'border-slate-300 bg-white text-slate-400'
                  }`}
                >
                  {s.isDone ? <CheckCircle2 className="h-3.5 w-3.5" /> : idx + 1}
                </div>

                {/* Step Info */}
                <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div>
                    <h5
                      className={`text-xs font-bold ${
                        s.isDone || s.isCurrent ? 'text-[#182B25]' : 'text-slate-400'
                      }`}
                    >
                      {s.label}
                    </h5>
                    <p className="text-[11px] text-[#64748B]">{s.description}</p>
                  </div>

                  <div className="shrink-0 text-right">
                    {hasTimestamp ? (
                      <span className="inline-block rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800 border border-emerald-100">
                        {formatTime(s.timestamp)}
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">
                        {s.isCurrent ? 'In Progress' : 'Pending'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pickup & Destination Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
        <div className="rounded-2xl bg-[#F8FAF9] p-3.5 border border-[#E5EAE7]">
          <span className="text-[10px] font-bold text-[#64748B] uppercase flex items-center gap-1">
            <MapPin className="h-3 w-3 text-[#16866A]" /> Pickup Point
          </span>
          <p className="text-xs font-bold text-[#182B25] mt-1">{task.pickupLocationName}</p>
          <p className="text-[11px] text-[#64748B]">{task.pickupAddress}</p>
          {task.pickupContactPhone && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-[#16866A] font-semibold">
              <Phone className="h-3.5 w-3.5" />
              <span>{task.pickupContactPhone}</span>
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-[#F8FAF9] p-3.5 border border-[#E5EAE7]">
          <span className="text-[10px] font-bold text-[#64748B] uppercase flex items-center gap-1">
            <MapPin className="h-3 w-3 text-blue-600" /> Dropoff Destination
          </span>
          <p className="text-xs font-bold text-[#182B25] mt-1">{task.deliveryLocationName}</p>
          <p className="text-[11px] text-[#64748B]">{task.deliveryAddress}</p>
          {task.deliveryContactPhone && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-blue-700 font-semibold">
              <Phone className="h-3.5 w-3.5" />
              <span>{task.deliveryContactPhone}</span>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Courier Action Bar (if active and in Courier View) */}
      {isCourierView && !isCancelled && status !== 'DELIVERED' && (
        <div className="pt-3 border-t border-[#E5EAE7] flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => setShowDisruptionModal(true)}
            disabled={isSubmitting}
            className="rounded-xl border border-red-200 bg-red-50 px-3.5 py-2 text-xs font-bold text-red-700 hover:bg-red-100 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Report Road Hazard / Disruption</span>
          </button>

          <div className="flex items-center gap-2">
            {status === 'AVAILABLE' && (
              <button
                onClick={() => handleTransition('ACCEPTED')}
                disabled={isSubmitting}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-sm cursor-pointer disabled:opacity-50"
              >
                Accept Delivery Run
              </button>
            )}

            {status === 'ACCEPTED' && (
              <button
                onClick={() => handleTransition('ARRIVED_PICKUP')}
                disabled={isSubmitting}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-sm cursor-pointer disabled:opacity-50"
              >
                1. Confirm Arrived at Pickup
              </button>
            )}

            {status === 'ARRIVED_PICKUP' && (
              <button
                onClick={() => handleTransition('PICKED_UP')}
                disabled={isSubmitting}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-sm cursor-pointer disabled:opacity-50"
              >
                2. Confirm Cargo Loaded (In Transit)
              </button>
            )}

            {status === 'PICKED_UP' && (
              <button
                onClick={() => handleTransition('ARRIVED_DELIVERY')}
                disabled={isSubmitting}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-sm cursor-pointer disabled:opacity-50"
              >
                3. Confirm Arrived at Recipient
              </button>
            )}

            {status === 'ARRIVED_DELIVERY' && (
              <button
                onClick={() => handleTransition('DELIVERED')}
                disabled={isSubmitting}
                className="rounded-xl bg-emerald-700 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-800 shadow-sm cursor-pointer disabled:opacity-50"
              >
                4. Confirm Delivered
              </button>
            )}

            {status === 'DISRUPTED' && (
              <button
                onClick={() => handleTransition(task.statusTimestamps.arrivedDelivery ? 'ARRIVED_DELIVERY' : task.statusTimestamps.pickedUp ? 'PICKED_UP' : task.statusTimestamps.arrivedPickup ? 'ARRIVED_PICKUP' : 'ACCEPTED')}
                disabled={isSubmitting}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] shadow-sm cursor-pointer disabled:opacity-50"
              >
                Resume Delivery Route
              </button>
            )}
          </div>
        </div>
      )}

      {/* Disruption Modal */}
      {showDisruptionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              <h4 className="text-base font-bold">Report Route Disruption</h4>
            </div>
            <p className="text-xs text-[#64748B]">
              Document unexpected hazards (e.g. flash flooding, vehicle breakdown, impassable road). The Coordinator Operations Center will be notified immediately for rerouting or recovery.
            </p>
            <div>
              <label className="block text-xs font-bold text-[#182B25] mb-1">
                Disruption Reason / Description
              </label>
              <textarea
                value={disruptionReason}
                onChange={(e) => setDisruptionReason(e.target.value)}
                placeholder="e.g. Flash flooding along Galle Road near Lunawa Bridge, 2ft water level."
                rows={3}
                className="w-full rounded-xl border border-[#E5EAE7] p-2.5 text-xs text-[#182B25] focus:border-red-500 focus:outline-none"
              />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowDisruptionModal(false)}
                className="rounded-xl border border-[#E5EAE7] px-4 py-2 text-xs font-bold text-[#64748B] hover:bg-[#F8FAF9]"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  handleTransition('DISRUPTED', {
                    disruptionReason: disruptionReason || 'Road impassable / hazard reported',
                  })
                }
                disabled={isSubmitting}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-50"
              >
                Submit Disruption Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Append-Only Status Events Audit Trail */}
      {task.statusEvents && task.statusEvents.length > 0 && (
        <div className="pt-2">
          <details className="group rounded-2xl bg-[#F8FAF9] p-3.5 border border-[#E5EAE7]">
            <summary className="flex cursor-pointer items-center justify-between text-xs font-bold text-[#182B25] select-none">
              <span className="flex items-center gap-1.5">
                <History className="h-3.5 w-3.5 text-[#16866A]" />
                <span>Append-Only Transition Audit History ({task.statusEvents.length} events)</span>
              </span>
              <ChevronRight className="h-4 w-4 text-[#64748B] transition-transform group-open:rotate-90" />
            </summary>

            <div className="mt-3 space-y-2 border-t border-[#E5EAE7] pt-2">
              {task.statusEvents.map((evt) => (
                <div key={evt.id} className="text-[11px] flex items-start justify-between gap-2 py-1 border-b border-[#E5EAE7]/50 last:border-none">
                  <div>
                    <span className="font-semibold text-[#182B25]">
                      {evt.fromStatus} ➔ <span className="text-[#16866A]">{evt.toStatus}</span>
                    </span>
                    {evt.changedByName && (
                      <span className="text-[#64748B] ml-1.5">by {evt.changedByName}</span>
                    )}
                    {evt.notes && (
                      <p className="text-[#64748B] italic mt-0.5">{evt.notes}</p>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono shrink-0">
                    {formatTime(evt.createdAt)}
                  </span>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default DeliveryStatusTimeline;
