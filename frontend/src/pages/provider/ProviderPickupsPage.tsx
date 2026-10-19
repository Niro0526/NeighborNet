import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Truck,
  MapPin,
  Clock,
  Phone,
  CheckCircle2,
  Navigation,
  ArrowRight,
  Package,
  RotateCcw,
  UserCheck,
} from 'lucide-react';
import { deliveryService } from '../../services/deliveryService';
import { useAuth } from '../../hooks';
import { DeliveryTask } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';

export const ProviderPickupsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [tasks, setTasks] = useState<DeliveryTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<DeliveryTask | null>(null);
  const [handoverSuccess, setHandoverSuccess] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const allTasks = await deliveryService.getDeliveryTasks();
      setTasks(allTasks);
      if (allTasks.length > 0 && !selectedTask) {
        setSelectedTask(allTasks[0]);
      }
    } catch (err) {
      console.error('Failed to load pickups data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentUser.id]);

  const handleConfirmHandover = async (taskId: string) => {
    try {
      await deliveryService.updateTaskStatus(taskId, 'PICKED_UP');
      setHandoverSuccess(`Food successfully handed over to volunteer courier! Dispatch is now en route to destination shelter.`);
      await loadData();
      setTimeout(() => setHandoverSuccess(null), 5000);
    } catch (err) {
      console.error('Handover confirmation failed:', err);
    }
  };

  // Status mapping helper
  const getStepProgress = (status: string): { step: number; percentage: number; label: string } => {
    switch (status) {
      case 'PENDING':
      case 'AVAILABLE':
        return { step: 0, percentage: 10, label: 'Matching Courier' };
      case 'ASSIGNED':
      case 'ACCEPTED':
        return { step: 1, percentage: 30, label: 'Courier Dispatched' };
      case 'ARRIVED_PICKUP':
        return { step: 2, percentage: 50, label: 'Courier at Your Kitchen' };
      case 'PICKED_UP':
      case 'EN_ROUTE':
        return { step: 3, percentage: 75, label: 'En Route to Shelter' };
      case 'ARRIVED_DELIVERY':
        return { step: 4, percentage: 90, label: 'Arrived at Shelter' };
      case 'DELIVERED':
      case 'FULFILLED':
        return { step: 5, percentage: 100, label: 'Delivered & Confirmed' };
      default:
        return { step: 1, percentage: 35, label: 'In Progress' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[#E5EAE7] pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#16866A]">
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <span>Food Provider</span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-[#182B25] mt-1">
            Scheduled Pickups & Live Courier Path
          </h1>
          <p className="text-xs text-[#64748B]">
            Real-time tracking of assigned volunteers, donor kitchen handovers, and recipient delivery routes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] shadow-2xs"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Refresh Status</span>
          </button>
          <Link
            to="/admin/map"
            className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-[#09664F]"
          >
            <Navigation className="h-3.5 w-3.5" />
            <span>Live Geospatial Map</span>
          </Link>
        </div>
      </div>

      {handoverSuccess && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 flex items-center gap-3 animate-in fade-in">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
          <p className="text-xs font-bold text-emerald-900">{handoverSuccess}</p>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: List of Scheduled Pickups */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-sm font-bold text-[#182B25] flex items-center justify-between">
            <span>Active Pickups</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-[#16866A] font-bold">
              {tasks.length} Active
            </span>
          </h3>

          {isLoading ? (
            <div className="py-12 text-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#16866A] border-t-transparent mx-auto" />
              <p className="text-xs text-[#64748B] mt-2">Loading scheduled pickups...</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="rounded-2xl border border-[#E5EAE7] bg-white p-6 text-center shadow-xs">
              <Package className="h-8 w-8 text-slate-300 mx-auto mb-2" />
              <h4 className="text-xs font-bold text-[#182B25]">No Active Pickups Scheduled</h4>
              <p className="text-[11px] text-[#64748B] mt-1">
                When an OR-Tools matching recommendation is approved, assigned volunteer couriers will appear here.
              </p>
            </div>
          ) : (
            tasks.map((task) => {
              const isSelected = selectedTask?.id === task.id;
              const progress = getStepProgress(task.status);
              return (
                <div
                  key={task.id}
                  onClick={() => setSelectedTask(task)}
                  className={`rounded-2xl border p-4 transition-all cursor-pointer shadow-xs ${
                    isSelected
                      ? 'border-[#16866A] bg-emerald-50/40 ring-1 ring-[#16866A]'
                      : 'border-[#E5EAE7] bg-white hover:border-[#16866A]/40'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#94A3B8]">
                        Task #{task.id.slice(-6)}
                      </span>
                      <h4 className="text-xs font-bold text-[#182B25] mt-0.5">{task.title || task.cargoDescription}</h4>
                    </div>
                    <StatusBadge status={task.status} size="sm" />
                  </div>

                  <div className="mt-3 space-y-1.5 text-[11px] text-[#64748B]">
                    <div className="flex items-center gap-1.5">
                      <Truck className="h-3.5 w-3.5 text-[#16866A] shrink-0" />
                      <span className="font-semibold text-[#182B25]">
                        {task.volunteerName || 'Assigned Motorcycle Courier'}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span className="truncate">{task.deliveryAddress || 'Community Shelter'}</span>
                    </div>
                  </div>

                  {/* Micro Progress Bar */}
                  <div className="mt-3 pt-2.5 border-t border-[#E5EAE7]/70">
                    <div className="flex items-center justify-between text-[10px] mb-1">
                      <span className="font-semibold text-[#182B25]">{progress.label}</span>
                      <span className="text-[#64748B]">{progress.percentage}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#16866A] rounded-full transition-all duration-500"
                        style={{ width: `${progress.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Detailed Live Volunteer Path & Handover Verification */}
        <div className="lg:col-span-2">
          {selectedTask ? (
            <div className="rounded-2xl border border-[#E5EAE7] bg-white p-5 shadow-xs space-y-5">
              {/* Header Info */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-[#E5EAE7]">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#16866A]">Active Mission Tracking</span>
                    <span className="text-slate-300">•</span>
                    <span className="text-xs text-[#64748B] font-mono">ID: {selectedTask.id}</span>
                  </div>
                  <h2 className="text-base font-bold text-[#182B25] mt-1">
                    {selectedTask.title || selectedTask.cargoDescription}
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={selectedTask.status} size="md" />
                </div>
              </div>

              {/* Courier Identity Card */}
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#16866A] text-white">
                      <UserCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-[#182B25]">
                        {selectedTask.volunteerName || 'Dinesh Mendis'}
                      </h4>
                      <p className="text-[11px] text-[#64748B]">
                        Verified Courier • Honda Wave 110cc (Insulated Thermal Box)
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={`tel:${selectedTask.pickupContactPhone || '+94771234567'}`}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-bold text-[#182B25] hover:bg-[#F8FAF9] shadow-2xs"
                    >
                      <Phone className="h-3.5 w-3.5 text-[#16866A]" />
                      <span>Call Courier</span>
                    </a>
                    {selectedTask.status === 'ARRIVED_PICKUP' && (
                      <button
                        onClick={() => handleConfirmHandover(selectedTask.id)}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-[#16866A] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#09664F] shadow-xs"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Confirm Food Handover</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Visual Volunteer Path Stepper */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#94A3B8] mb-3">
                  Live Dispatch Lifecycle & Waypoints
                </h4>
                <div className="relative border-l-2 border-emerald-200 ml-4 pl-6 space-y-6">
                  {/* Waypoint 1: Donor Kitchen */}
                  <div className="relative">
                    <div className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-white text-[10px] font-bold">
                      1
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <h5 className="text-xs font-bold text-[#182B25]">Pickup Location: Your Kitchen</h5>
                        <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                          Origin Point
                        </span>
                      </div>
                      <p className="text-xs text-[#64748B] mt-0.5">
                        {selectedTask.pickupAddress || 'GreenBites Bakery & Cafe, 248 Galle Road, Katubedda, Moratuwa'}
                      </p>
                      <p className="text-[11px] text-[#94A3B8] mt-1">
                        Cargo: <span className="font-semibold text-[#182B25]">{selectedTask.quantityDescription || 'Standard lot'}</span> ({selectedTask.cargoDescription})
                      </p>
                    </div>
                  </div>

                  {/* Waypoint 2: Courier Handover */}
                  <div className="relative">
                    <div className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full text-white text-[10px] font-bold ${
                      ['ARRIVED_PICKUP', 'PICKED_UP', 'ARRIVED_DELIVERY', 'DELIVERED'].includes(selectedTask.status)
                        ? 'bg-emerald-600'
                        : 'bg-slate-300'
                    }`}>
                      2
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-[#182B25]">Thermal Box Loading & Food Safety Check</h5>
                      <p className="text-xs text-[#64748B] mt-0.5">
                        Courier inspects temperature holding window (&gt;60°C hot food / &lt;5°C chilled).
                      </p>
                      {['PICKED_UP', 'ARRIVED_DELIVERY', 'DELIVERED'].includes(selectedTask.status) ? (
                        <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Handover verified by kitchen manager</span>
                        </div>
                      ) : (
                        <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg">
                          <Clock className="h-3.5 w-3.5" />
                          <span>Awaiting courier arrival at kitchen</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Waypoint 3: Transit Route */}
                  <div className="relative">
                    <div className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full text-white text-[10px] font-bold ${
                      ['PICKED_UP', 'ARRIVED_DELIVERY', 'DELIVERED'].includes(selectedTask.status)
                        ? 'bg-emerald-600'
                        : 'bg-slate-300'
                    }`}>
                      3
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <h5 className="text-xs font-bold text-[#182B25]">Transit Route: Galle Road Corridor</h5>
                        <span className="text-[11px] font-mono font-bold text-[#16866A]">
                          ~{selectedTask.estimatedDurationMin || 18} mins (2.4 km)
                        </span>
                      </div>
                      <p className="text-xs text-[#64748B] mt-0.5">
                        Transit via Galle Rd / Lunawa Station Rd. Real-time GPS coordinates active.
                      </p>
                    </div>
                  </div>

                  {/* Waypoint 4: Destination Shelter */}
                  <div className="relative">
                    <div className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full text-white text-[10px] font-bold ${
                      selectedTask.status === 'DELIVERED' ? 'bg-emerald-600' : 'bg-slate-300'
                    }`}>
                      4
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <h5 className="text-xs font-bold text-[#182B25]">Destination Shelter Receipt</h5>
                        {selectedTask.status === 'DELIVERED' && (
                          <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                            Completed
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#64748B] mt-0.5">
                        {selectedTask.deliveryAddress || 'Grace Home for the Elderly, 84 Lunawa Station Road, Moratuwa'}
                      </p>
                      <p className="text-[11px] text-[#94A3B8] mt-1">
                        Recipient Sign-off: <span className="font-semibold text-[#182B25]">Sister Mary Teresa</span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Geographic Path Preview Map Card */}
              <div className="rounded-2xl border border-[#E5EAE7] bg-[#F8FAF9] p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Navigation className="h-4 w-4 text-[#16866A]" />
                    <h4 className="text-xs font-bold text-[#182B25]">GPS Path & Transit Corridor</h4>
                  </div>
                  <Link
                    to="/admin/map"
                    className="text-xs font-bold text-[#16866A] hover:underline flex items-center gap-1"
                  >
                    <span>Full Screen Map</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>

                {/* SVG Route Visualization */}
                <div className="relative h-44 w-full rounded-xl bg-slate-900 overflow-hidden flex items-center justify-center border border-slate-800">
                  <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#16866A_1px,transparent_1px)] [background-size:16px_16px]" />

                  {/* Route Canvas */}
                  <svg className="w-full h-full" viewBox="0 0 400 160">
                    {/* Path Line */}
                    <path
                      d="M 60 80 Q 140 30, 200 90 T 340 70"
                      fill="none"
                      stroke="#16866A"
                      strokeWidth="4"
                      strokeDasharray="6 6"
                      className="animate-pulse"
                    />

                    {/* Origin Pin */}
                    <circle cx="60" cy="80" r="8" fill="#10B981" />
                    <text x="60" y="110" fill="#E2E8F0" fontSize="10" textAnchor="middle" fontWeight="bold">
                      Your Kitchen
                    </text>

                    {/* Volunteer Courier Icon Moving */}
                    <circle cx="200" cy="90" r="10" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="2" />
                    <text x="200" y="125" fill="#FDE68A" fontSize="10" textAnchor="middle" fontWeight="bold">
                      Courier (Motorcycle)
                    </text>

                    {/* Destination Pin */}
                    <circle cx="340" cy="70" r="8" fill="#3B82F6" />
                    <text x="340" y="100" fill="#BFDBFE" fontSize="10" textAnchor="middle" fontWeight="bold">
                      Grace Home
                    </text>
                  </svg>

                  {/* Overlay Badges */}
                  <div className="absolute top-2 left-2 bg-slate-800/90 backdrop-blur-xs text-[10px] text-white px-2.5 py-1 rounded-md border border-slate-700">
                    Galle Road ➔ Lunawa Sector
                  </div>
                  <div className="absolute bottom-2 right-2 bg-emerald-950/90 text-emerald-300 text-[10px] font-mono px-2.5 py-1 rounded-md border border-emerald-800">
                    Live GPS Stream: Active
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-[#E5EAE7] bg-white p-12 text-center shadow-xs">
              <Package className="h-10 w-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-[#182B25]">Select a Pickup to View Volunteer Path</h3>
              <p className="text-xs text-[#64748B] mt-1 max-w-sm mx-auto">
                Choose an active pickup from the list to inspect assigned volunteer courier credentials, transit coordinates, and handover confirmations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
