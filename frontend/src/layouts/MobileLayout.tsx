import React from 'react';
import { Outlet } from 'react-router-dom';
import { MobileBottomNavigation } from '../components/common/MobileBottomNavigation';
import { Header } from '../components/common/Header';

export const MobileLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8FAF9] max-w-md mx-auto shadow-2xl relative">
      <Header />
      <main className="flex-1 p-4 pb-24 overflow-y-auto">
        <Outlet />
      </main>
      <MobileBottomNavigation />
    </div>
  );
};
