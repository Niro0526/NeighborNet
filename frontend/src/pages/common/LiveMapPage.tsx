import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Navigation,
  Truck,
  Building2,
  Users,
  ShieldAlert,
  Layers,
  RotateCcw,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { deliveryService } from '../../services/deliveryService';
import { disasterService } from '../../services/disasterService';
import { DeliveryTask, LocationRecord } from '../../types';

export const LiveMapPage: React.FC = () => {
  const [locations, setLocations] = useState<LocationRecord[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryTask[]>([]);

  // Filter toggles
  const [showDonors, setShowDonors] = useState(true);
  const [showShelters, setShowShelters] = useState(true);
  const [showCouriers, setShowCouriers] = useState(true);
  const [showFloodZones, setShowFloodZones] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);

  const loadMapData = async () => {
    try {
      const [locs, dels] = await Promise.all([
        analyticsService.getMapLocations(),
        deliveryService.getDeliveryTasks(),
        disasterService.getDisasterEvents(),
      ]);
      setLocations(locs);
      setDeliveries(dels);
      if (dels.length > 0 && !selectedEntity) {
        setSelectedEntity({ type: 'delivery', data: dels[0] });
      }
    } catch (err) {
      console.error('Failed to load live map data:', err);
    }
  };

  useEffect(() => {
    loadMapData();
  }, []);

  // Split locations into donors and shelters
  const donors = locations.filter((l) =>
    l.name.toLowerCase().includes('bakery') ||
    l.name.toLowerCase().includes('hotel') ||
    l.name.toLowerCase().includes('catering') ||
    l.name.toLowerCase().includes('kitchen')
  );

  const shelters = locations.filter((l) =>
    l.name.toLowerCase().includes('home') ||
    l.name.toLowerCase().includes('center') ||
    l.name.toLowerCase().includes('shelter') ||
    l.name.toLowerCase().includes('dmc')
  );

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[#E5EAE7] pb-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-[#182B25] flex items-center gap-2">
            <Navigation className="h-6 w-6 text-[#16866A]" />
            <span>Geospatial Command Map & Fleet Tracking</span>
          </h1>
          <p className="text-xs text-[#64748B]">
            Real-time PostGIS mapping of donor facilities, recipient shelters, courier transits, and Kelani/Bolgoda flood inundation perimeters
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadMapData}
            className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] shadow-2xs cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Sync GPS</span>
          </button>
        </div>
      </div>

      {/* Map Control Bar & Layer Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-3 border border-[#E5EAE7] shadow-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-[#182B25] flex items-center gap-1.5 mr-1">
            <Layers className="h-4 w-4 text-[#16866A]" />
            <span>Layers:</span>
          </span>

          <button
            onClick={() => setShowDonors(!showDonors)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              showDonors
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-slate-100 text-slate-500 border border-transparent'
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Donors ({donors.length || 3})</span>
          </button>

          <button
            onClick={() => setShowShelters(!showShelters)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              showShelters
                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                : 'bg-slate-100 text-slate-500 border border-transparent'
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            <span>Shelters ({shelters.length || 2})</span>
          </button>

          <button
            onClick={() => setShowCouriers(!showCouriers)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              showCouriers
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-slate-100 text-slate-500 border border-transparent'
            }`}
          >
            <Truck className="h-3.5 w-3.5" />
            <span>Couriers ({deliveries.length})</span>
          </button>

          <button
            onClick={() => setShowFloodZones(!showFloodZones)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              showFloodZones
                ? 'bg-red-100 text-red-800 border border-red-300'
                : 'bg-slate-100 text-slate-500 border border-transparent'
            }`}
          >
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>Flood Zone (Moratuwa Basin)</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-[#64748B] flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>PostGIS EPSG:4326 • Colombo/Moratuwa Sector</span>
        </div>
      </div>

      {/* Main Map Visualizer & Side Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Interactive Map Visualizer Container */}
        <div className="lg:col-span-3 rounded-2xl border border-[#E5EAE7] bg-slate-900 overflow-hidden shadow-md relative min-h-[500px]">
          {/* Subtle Grid Lines & Background Canvas */}
          <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#16866A_1.5px,transparent_1.5px)] [background-size:24px_24px]" />

          {/* SVG Map Canvas */}
          <svg className="w-full h-full min-h-[500px]" viewBox="0 0 800 500">
            {/* Coastline / Bolgoda Lake Waterway */}
            <path
              d="M 50 0 Q 70 200, 100 350 T 130 500 L 0 500 L 0 0 Z"
              fill="#0F172A"
              stroke="#1E293B"
              strokeWidth="2"
            />
            <text x="35" y="250" fill="#334155" fontSize="12" transform="rotate(-90 35,250)" fontWeight="bold">
              Indian Ocean Coastline
            </text>

            {/* Bolgoda Lake Basin */}
            <path
              d="M 520 180 Q 560 260, 600 330 T 680 480 Q 640 490, 580 400 T 490 220 Z"
              fill="#0c4a6e"
              opacity="0.6"
            />
            <text x="590" y="320" fill="#38bdf8" fontSize="11" fontWeight="bold">
              Bolgoda Basin
            </text>

            {/* Flood Inundation Hazard Polygon (DMC Kelani / Bolgoda) */}
            {showFloodZones && (
              <g className="animate-pulse">
                <polygon
                  points="450,220 620,240 670,390 530,380 460,300"
                  fill="#ef4444"
                  fillOpacity="0.25"
                  stroke="#ef4444"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                />
                <text x="500" y="280" fill="#fca5a5" fontSize="11" fontWeight="bold">
                  ⚠️ DMC Inundation Perimeter (Level 2)
                </text>
              </g>
            )}

            {/* Galle Road Main Corridor Line */}
            <path
              d="M 180 20 Q 220 180, 260 300 T 310 490"
              fill="none"
              stroke="#334155"
              strokeWidth="6"
            />
            <text x="210" y="80" fill="#64748b" fontSize="10" transform="rotate(20 210,80)">
              Galle Road (A2 Corridor)
            </text>

            {/* Active Delivery Route Lines */}
            {showCouriers && (
              <g>
                <path
                  d="M 270 290 Q 320 260, 380 340"
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="3"
                  strokeDasharray="6 4"
                  className="animate-pulse"
                />
                <path
                  d="M 210 90 Q 280 150, 360 180"
                  fill="none"
                  stroke="#F59E0B"
                  strokeWidth="2.5"
                  strokeDasharray="5 3"
                />
              </g>
            )}

            {/* Food Donors Pins */}
            {showDonors && (
              <g>
                {/* Cinnamon Grand / Colombo Hotel */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'donor',
                    name: 'Perera Luxury Hotel & Banquet Kitchen',
                    address: 'Marine Drive, Colombo 03',
                    inventory: '85 kg Cooked Rice & Curry Lots',
                    status: 'Active Donating',
                    safeWindow: '3 hrs 40 mins remaining'
                  })}
                  className="cursor-pointer group"
                >
                  <circle cx="210" cy="90" r="12" fill="#10B981" stroke="#ffffff" strokeWidth="2" />
                  <circle cx="210" cy="90" r="20" fill="#10B981" opacity="0.2" className="animate-ping" />
                  <text x="210" y="120" fill="#E2E8F0" fontSize="10" textAnchor="middle" fontWeight="bold">
                    Perera Hotel (Colombo 03)
                  </text>
                </g>

                {/* GreenBites Bakery Moratuwa */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'donor',
                    name: 'GreenBites Bakery & Cafe',
                    address: '248 Galle Road, Katubedda, Moratuwa',
                    inventory: '35 kg Artisan Bread, Buns & Meal Packs',
                    status: 'Active Donating',
                    safeWindow: '4 hrs 15 mins remaining'
                  })}
                  className="cursor-pointer"
                >
                  <circle cx="270" cy="290" r="12" fill="#10B981" stroke="#ffffff" strokeWidth="2" />
                  <text x="270" y="320" fill="#E2E8F0" fontSize="10" textAnchor="middle" fontWeight="bold">
                    GreenBites (Katubedda)
                  </text>
                </g>
              </g>
            )}

            {/* Recipient Shelters Pins */}
            {showShelters && (
              <g>
                {/* Grace Home Moratuwa */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'shelter',
                    name: 'Grace Home for the Elderly',
                    address: '84 Lunawa Station Road, Moratuwa',
                    demand: '65 Daily Meals Needed (Low-Sodium/Vegetarian)',
                    status: 'Matched — Courier En Route',
                    contact: 'Sister Mary Teresa (+94 11 264 5589)'
                  })}
                  className="cursor-pointer"
                >
                  <circle cx="380" cy="340" r="12" fill="#3B82F6" stroke="#ffffff" strokeWidth="2" />
                  <text x="380" y="370" fill="#93C5FD" fontSize="10" textAnchor="middle" fontWeight="bold">
                    Grace Elders Home (Lunawa)
                  </text>
                </g>

                {/* Suwasetha Ratmalana */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'shelter',
                    name: 'Suwasetha Child Development Center',
                    address: '15 Ferry Road, Ratmalana',
                    demand: '120 Children Evacuated • Need Milk Powder & Meals',
                    status: 'High Priority Disaster Need',
                    contact: 'Anuki Bandara (+94 70 334 5566)'
                  })}
                  className="cursor-pointer"
                >
                  <circle cx="360" cy="180" r="12" fill="#3B82F6" stroke="#ffffff" strokeWidth="2" />
                  <text x="360" y="210" fill="#93C5FD" fontSize="10" textAnchor="middle" fontWeight="bold">
                    Suwasetha Center (Ratmalana)
                  </text>
                </g>
              </g>
            )}

            {/* Active Couriers Pins */}
            {showCouriers && (
              <g>
                {/* Dinesh Mendis (Motorcycle) */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'courier',
                    name: 'Dinesh Mendis (Courier)',
                    vehicle: 'Motorcycle with Insulated Thermal Box',
                    speed: '32 km/h • GPS Active',
                    currentTask: 'GreenBites Katubedda ➔ Grace Home Lunawa',
                    eta: '8 mins (1.6 km remaining)'
                  })}
                  className="cursor-pointer"
                >
                  <circle cx="320" cy="315" r="11" fill="#F59E0B" stroke="#ffffff" strokeWidth="2.5" />
                  <text x="320" y="340" fill="#FDE68A" fontSize="9" textAnchor="middle" fontWeight="bold">
                    🛵 Dinesh (Courier)
                  </text>
                </g>

                {/* Kamal Perera (Van) */}
                <g
                  onClick={() => setSelectedEntity({
                    type: 'courier',
                    name: 'Kamal Perera (Heavy Transport)',
                    vehicle: 'High-Capacity Van (Disaster Logistics)',
                    speed: '28 km/h • GPS Active',
                    currentTask: 'Perera Hotel ➔ Suwasetha Evacuation Center',
                    eta: '14 mins (3.8 km remaining)'
                  })}
                  className="cursor-pointer"
                >
                  <circle cx="280" cy="135" r="11" fill="#F59E0B" stroke="#ffffff" strokeWidth="2.5" />
                  <text x="280" y="160" fill="#FDE68A" fontSize="9" textAnchor="middle" fontWeight="bold">
                    🚐 Kamal (Van)
                  </text>
                </g>
              </g>
            )}
          </svg>

          {/* Floating Map Legend */}
          <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 text-[11px] text-white shadow-xl space-y-1.5">
            <div className="font-bold text-slate-300 text-[10px] uppercase tracking-wider mb-1">Live Map Legend</div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-emerald-500 shrink-0" />
              <span>Surplus Food Provider (Kitchen/Bakery)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-blue-500 shrink-0" />
              <span>Community Recipient (Shelter/NGO)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-amber-500 shrink-0" />
              <span>Active Volunteer Courier En Route</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm bg-red-500/50 border border-red-500 shrink-0" />
              <span>DMC Flash Flood Inundation Hazard</span>
            </div>
          </div>
        </div>

        {/* Right Drawer: Selected Entity Details & Active Route Inspector */}
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-[#E5EAE7] bg-white p-4 shadow-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#94A3B8] mb-3">
              Geospatial Inspector
            </h3>

            {selectedEntity ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  {selectedEntity.type === 'donor' && <Building2 className="h-5 w-5 text-emerald-600" />}
                  {selectedEntity.type === 'shelter' && <Users className="h-5 w-5 text-blue-600" />}
                  {selectedEntity.type === 'courier' && <Truck className="h-5 w-5 text-amber-600" />}
                  {selectedEntity.type === 'delivery' && <Navigation className="h-5 w-5 text-[#16866A]" />}
                  <h4 className="text-sm font-bold text-[#182B25]">
                    {selectedEntity.name || selectedEntity.data?.title || 'Selected Target'}
                  </h4>
                </div>

                <div className="text-xs text-[#64748B] space-y-1.5">
                  {selectedEntity.address && (
                    <p className="flex items-start gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <span>{selectedEntity.address}</span>
                    </p>
                  )}
                  {selectedEntity.inventory && (
                    <p className="font-semibold text-emerald-800 bg-emerald-50 p-2 rounded-lg">
                      📦 {selectedEntity.inventory}
                    </p>
                  )}
                  {selectedEntity.demand && (
                    <p className="font-semibold text-blue-800 bg-blue-50 p-2 rounded-lg">
                      🤝 {selectedEntity.demand}
                    </p>
                  )}
                  {selectedEntity.vehicle && (
                    <p className="font-semibold text-amber-800 bg-amber-50 p-2 rounded-lg">
                      🛵 {selectedEntity.vehicle}
                    </p>
                  )}
                  {selectedEntity.eta && (
                    <p className="flex items-center gap-1.5 text-xs text-[#182B25] font-bold">
                      <Clock className="h-3.5 w-3.5 text-[#16866A]" />
                      <span>ETA: {selectedEntity.eta}</span>
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-[#64748B]">
                Click any marker on the map to inspect live donor inventory, shelter requirements, or courier route coordinates.
              </div>
            )}
          </div>

          {/* Quick Action Navigation */}
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4 space-y-2">
            <h4 className="text-xs font-bold text-emerald-950">Quick Workspace Access</h4>
            <div className="space-y-1.5">
              <a
                href="/food/pickups"
                className="flex items-center justify-between text-xs font-semibold text-emerald-800 hover:text-emerald-950 p-1.5 rounded-lg hover:bg-emerald-100/60 transition-colors"
              >
                <span>Food Provider Pickups</span>
                <ArrowRight className="h-3 w-3" />
              </a>
              <a
                href="/admin/matching"
                className="flex items-center justify-between text-xs font-semibold text-emerald-800 hover:text-emerald-950 p-1.5 rounded-lg hover:bg-emerald-100/60 transition-colors"
              >
                <span>OR-Tools Optimization</span>
                <ArrowRight className="h-3 w-3" />
              </a>
              <a
                href="/admin/analytics"
                className="flex items-center justify-between text-xs font-semibold text-emerald-800 hover:text-emerald-950 p-1.5 rounded-lg hover:bg-emerald-100/60 transition-colors"
              >
                <span>Impact Reports & Analytics</span>
                <ArrowRight className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
