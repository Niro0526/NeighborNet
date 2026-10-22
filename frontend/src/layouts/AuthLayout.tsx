import React from 'react';
import { Outlet, Link } from 'react-router-dom';

export const AuthLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-[#F8FAF9]">
      <div className="flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:flex-none lg:px-20 xl:px-24 w-full lg:w-1/2">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div className="flex items-center gap-3 mb-8">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#16866A] text-white shadow-md">
                <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
                </svg>
              </div>
              <div>
                <span className="font-extrabold text-[#182B25] text-xl tracking-tight">
                  NeighborNet <span className="text-[#16866A]">AI</span>
                </span>
                <p className="text-xs text-[#64748B]">Surplus to Support</p>
              </div>
            </Link>
          </div>

          <Outlet />

          <div className="mt-8 pt-6 border-t border-[#E5EAE7] text-center">
            <p className="text-xs text-[#64748B]">
              Simulated Prototype for ModelX 2.0 • Sri Lanka Region
            </p>
          </div>
        </div>
      </div>

      {/* Right Hero Graphic Showcase */}
      <div className="relative hidden w-0 flex-1 lg:block bg-[#09664F] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-tr from-[#09664F] via-[#16866A] to-[#34C19E] opacity-95" />
        <div className="absolute inset-0 flex flex-col justify-between p-16 text-white z-10">
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-white/20 px-4 py-1.5 text-xs font-semibold backdrop-blur-md">
              AI-Powered Surplus & Disaster Coordination
            </span>
            <span className="text-xs text-white/80">Moratuwa & Colombo Region</span>
          </div>

          <div className="max-w-md space-y-4">
            <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl leading-tight">
              Food Rescue Today. <br />
              Stronger Communities Tomorrow.
            </h2>
            <p className="text-sm text-emerald-100 leading-relaxed">
              Empowering food providers, shelters, and rapid response volunteers with real-time heuristic matching and emergency logistics.
            </p>
            <div className="pt-4 grid grid-cols-2 gap-4">
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm border border-white/10">
                <p className="text-2xl font-bold">Food Rescue</p>
                <p className="text-xs text-emerald-100">Surplus redistribution</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm border border-white/10">
                <p className="text-2xl font-bold">2 Modes</p>
                <p className="text-xs text-emerald-100">Community & Disaster</p>
              </div>
            </div>
          </div>

          <div className="text-xs text-white/60">
            © 2026 NeighborNet AI Architecture • ModelX 2.0 Prototype
          </div>
        </div>
      </div>
    </div>
  );
};
