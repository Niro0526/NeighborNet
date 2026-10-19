import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Users,
  Building2,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../../hooks';
import { UserRole } from '../../types';

export const LandingPage: React.FC = () => {
  const { allUsers, switchUser, switchRole } = useAuth();
  const navigate = useNavigate();

  const handleQuickDemo = async (role: UserRole, targetPath: string) => {
    const matched = allUsers.find((u) => u.assignedRoles.includes(role));
    if (matched) {
      await switchUser(matched.id);
      await switchRole?.(role);
    }
    navigate(targetPath);
  };

  return (
    <div className="min-h-screen bg-[#F8FAF9]">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 border-b border-[#E5EAE7] bg-white/95 backdrop-blur-md px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#16866A] text-white shadow-md">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
              </svg>
            </div>
            <div>
              <span className="font-extrabold text-[#182B25] text-lg tracking-tight">
                NeighborNet <span className="text-[#16866A]">AI</span>
              </span>
              <p className="text-[10px] text-[#64748B] font-medium hidden sm:block">
                Intelligent Food Rescue & Disaster Coordination
              </p>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-8 text-xs font-semibold text-[#64748B]">
            <a href="#features" className="hover:text-[#16866A] transition-colors">Features</a>
            <a href="#roles" className="hover:text-[#16866A] transition-colors">User Roles</a>
            <a href="#disaster-mode" className="hover:text-[#16866A] transition-colors">Disaster Response</a>
            <a href="#stats" className="hover:text-[#16866A] transition-colors">Impact</a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-xl px-4 py-2 text-xs font-semibold text-[#182B25] hover:bg-[#F8FAF9] transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/coordinator/dashboard"
              className="rounded-xl bg-[#16866A] px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-[#09664F] transition-all"
            >
              Open Dashboard
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3.5 py-1 text-xs font-semibold text-emerald-800">
                <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                <span>ModelX 2.0 Competition Prototype • Sri Lanka Region</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#182B25] leading-tight">
                Food Rescue Today. <br />
                <span className="text-[#16866A]">Stronger Communities</span> Tomorrow.
              </h1>

              <p className="text-base sm:text-lg text-[#64748B] max-w-xl leading-relaxed">
                An AI-coordinated platform that connects surplus food from local restaurants and bakeries with verified shelters, while instantly pivoting to emergency relief logistics during natural disasters.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => handleQuickDemo('COORDINATOR', '/coordinator/dashboard')}
                  className="flex items-center gap-2 rounded-2xl bg-[#16866A] px-6 py-3.5 text-sm font-bold text-white shadow-md hover:bg-[#09664F] transition-all"
                >
                  <span>Launch Live Platform</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <Link
                  to="/login"
                  className="rounded-2xl border border-[#E5EAE7] bg-white px-6 py-3.5 text-sm font-bold text-[#182B25] shadow-2xs hover:bg-[#F8FAF9] transition-all"
                >
                  Explore Demo Portals
                </Link>
              </div>

              {/* Trust Badges */}
              <div className="pt-4 flex items-center gap-6 text-xs text-[#64748B]">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[#16866A]" />
                  <span>Dual Operating Modes</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[#16866A]" />
                  <span>Moratuwa / Colombo Geospatial</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[#16866A]" />
                  <span>Zero Server Requirement</span>
                </div>
              </div>
            </div>

            {/* Hero Visual Card Stack */}
            <div className="lg:col-span-5">
              <div className="relative rounded-3xl border border-[#E5EAE7] bg-white p-6 shadow-2xl">
                <div className="flex items-center justify-between pb-4 border-b border-[#E5EAE7]">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-emerald-500 animate-ping" />
                    <span className="text-xs font-bold text-[#182B25]">Live Operational Status</span>
                  </div>
                  <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                    Normal Mode
                  </span>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-2xl bg-[#F8FAF9] p-3.5 border border-[#E5EAE7]">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#182B25]">GreenBites Kitchen & Bistro</span>
                      <span className="text-emerald-700 font-semibold">50 kg Available</span>
                    </div>
                    <p className="mt-1 text-[11px] text-[#64748B]">Steamed Basmati Rice & Dhal Curry • Safe until 22:30</p>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className="text-[#64748B]">AI Match: 98% Compatibility</span>
                      <span className="font-bold text-[#16866A]">Assigned to Hope Foundation</span>
                    </div>
                  </div>

                  <div className="rounded-2xl bg-[#F8FAF9] p-3.5 border border-[#E5EAE7]">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#182B25]">Royal Cinnamon Bakery</span>
                      <span className="text-amber-700 font-semibold">35 kg Available</span>
                    </div>
                    <p className="mt-1 text-[11px] text-[#64748B]">Artisan Crusty Sourdough & Rolls • Moratuwa Station</p>
                  </div>

                  <div className="rounded-2xl bg-red-50 p-3.5 border border-red-200">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-red-700 flex items-center gap-1.5">
                        <ShieldAlert className="h-3.5 w-3.5" /> Disaster Preparedness
                      </span>
                      <span className="text-[10px] bg-red-600 text-white px-2 py-0.5 rounded-full font-bold">
                        Standby
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-red-600/80">
                      Lunawa coastal flood zones monitored; relief allocation matrices active.
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-[#E5EAE7] flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-[#182B25]">1,240 kg</p>
                    <p className="text-[10px] text-[#64748B]">Food Rescued This Week</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#182B25]">54 Volunteers</p>
                    <p className="text-[10px] text-[#64748B]">Active Couriers</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#182B25]">94.8%</p>
                    <p className="text-[10px] text-[#64748B]">On-Time Safety Delivery</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Row */}
      <section id="stats" className="border-y border-[#E5EAE7] bg-white py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
              <p className="text-3xl lg:text-4xl font-extrabold text-[#16866A]">1,240+ kg</p>
              <p className="mt-1 text-xs font-semibold text-[#64748B]">Surplus Food Rescued</p>
            </div>
            <div>
              <p className="text-3xl lg:text-4xl font-extrabold text-[#182B25]">50+ NGOs</p>
              <p className="mt-1 text-xs font-semibold text-[#64748B]">Connected Shelters</p>
            </div>
            <div>
              <p className="text-3xl lg:text-4xl font-extrabold text-[#16866A]">200+</p>
              <p className="mt-1 text-xs font-semibold text-[#64748B]">Active Volunteers</p>
            </div>
            <div>
              <p className="text-3xl lg:text-4xl font-extrabold text-[#182B25]">2 Modes</p>
              <p className="mt-1 text-xs font-semibold text-[#64748B]">Community & Disaster Modes</p>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Role Selector Section */}
      <section id="roles" className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#182B25]">
              Tailored Workflows for Every Stakeholder
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-[#64748B]">
              Experience how each actor interacts with NeighborNet AI in real time. Click any portal to test the prototype.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Food Provider */}
            <div className="rounded-2xl bg-white p-6 border border-[#E5EAE7] shadow-xs hover:border-[#16866A] transition-all flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 mb-4">
                  <Building2 className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-[#182B25]">Food Provider</h3>
                <p className="mt-2 text-xs text-[#64748B] leading-relaxed">
                  Restaurants, bakeries, and grocers register surplus meals with temperature guidelines, pickup timeframes, and dietary tags.
                </p>
              </div>
              <button
                onClick={() => handleQuickDemo('FOOD_PROVIDER', '/provider/dashboard')}
                className="mt-6 flex items-center justify-between rounded-xl bg-[#F8FAF9] px-4 py-2.5 text-xs font-bold text-[#16866A] hover:bg-emerald-50 transition-colors"
              >
                <span>Enter Provider Portal</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Recipient NGO */}
            <div className="rounded-2xl bg-white p-6 border border-[#E5EAE7] shadow-xs hover:border-blue-500 transition-all flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 mb-4">
                  <Users className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-[#182B25]">NGO / Recipient</h3>
                <p className="mt-2 text-xs text-[#64748B] leading-relaxed">
                  Community shelters and food banks request supplies, view eligible offers, accept AI match suggestions, and verify drop-offs.
                </p>
              </div>
              <button
                onClick={() => handleQuickDemo('RECIPIENT', '/recipient/dashboard')}
                className="mt-6 flex items-center justify-between rounded-xl bg-[#F8FAF9] px-4 py-2.5 text-xs font-bold text-blue-700 hover:bg-blue-50 transition-colors"
              >
                <span>Enter NGO Portal</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Volunteer Courier */}
            <div className="rounded-2xl bg-white p-6 border border-[#E5EAE7] shadow-xs hover:border-amber-500 transition-all flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-700 mb-4">
                  <Users className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-[#182B25]">Volunteer Courier</h3>
                <p className="mt-2 text-xs text-[#64748B] leading-relaxed">
                  Mobile-optimized delivery tasks: accept assignments, follow turn-by-turn route suggestions, and mark state transitions.
                </p>
              </div>
              <button
                onClick={() => handleQuickDemo('VOLUNTEER', '/volunteer/dashboard')}
                className="mt-6 flex items-center justify-between rounded-xl bg-[#F8FAF9] px-4 py-2.5 text-xs font-bold text-amber-700 hover:bg-amber-50 transition-colors"
              >
                <span>Enter Volunteer Portal</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Coordinator Admin */}
            <div className="rounded-2xl bg-white p-6 border border-[#E5EAE7] shadow-xs hover:border-purple-500 transition-all flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-700 mb-4">
                  <ShieldAlert className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-[#182B25]">Coordinator / Admin</h3>
                <p className="mt-2 text-xs text-[#64748B] leading-relaxed">
                  Real-time command center: inventory overview, AI matching approvals, MapLibre geographic tracking, and disaster escalation.
                </p>
              </div>
              <button
                onClick={() => handleQuickDemo('COORDINATOR', '/coordinator/dashboard')}
                className="mt-6 flex items-center justify-between rounded-xl bg-[#F8FAF9] px-4 py-2.5 text-xs font-bold text-purple-700 hover:bg-purple-50 transition-colors"
              >
                <span>Enter Admin Console</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#E5EAE7] bg-white py-12">
        <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#16866A] text-white">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
              </svg>
            </div>
            <span className="font-bold text-sm text-[#182B25]">NeighborNet AI</span>
            <span className="text-xs text-[#64748B]">ModelX 2.0 Edition</span>
          </div>

          <p className="text-xs text-[#64748B] text-center md:text-right">
            Designed for Community Resilience & Rapid Relief Distribution in Sri Lanka.
          </p>
        </div>
      </footer>
    </div>
  );
};
