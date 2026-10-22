import React, { useState, useEffect } from 'react';
import { OperationalMode, DisasterEvent } from '../types';
import { disasterService } from '../services/disasterService';
import { mockRepository } from '../services/mockRepository';
import { isApiMode } from '../services/apiClient';
import { OperationalContext } from './operationalContextDef';
import { useAuth } from '../hooks/useAuth';

export const OperationalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentUser } = useAuth();
  const [mode, setModeState] = useState<OperationalMode>(() => {
    return isApiMode() ? 'NORMAL' : mockRepository.getOperationalMode();
  });
  const [activeDisaster, setActiveDisaster] = useState<DisasterEvent | undefined>(() => {
    return isApiMode() ? undefined : mockRepository.getDisasterEvents().find((d) => d.status === 'active');
  });

  const syncDisasterState = async () => {
    if (!isApiMode()) {
      setModeState(mockRepository.getOperationalMode());
      setActiveDisaster(mockRepository.getDisasterEvents().find((d) => d.status === 'active'));
      return;
    }

    try {
      const active = await disasterService.getActiveDisasterEvent();
      if (active) {
        setActiveDisaster(active);
        setModeState('DISASTER');
      } else {
        setActiveDisaster(undefined);
        setModeState('NORMAL');
      }
    } catch (err) {
      console.warn('Failed to sync disaster status from backend:', err);
    }
  };

  useEffect(() => {
    if (isApiMode() && !currentUser.id) {
      setModeState('NORMAL');
      setActiveDisaster(undefined);
      return;
    }
    syncDisasterState();

    if (!isApiMode()) {
      const unsubscribe = mockRepository.subscribe(() => {
        setModeState(mockRepository.getOperationalMode());
        setActiveDisaster(mockRepository.getDisasterEvents().find((d) => d.status === 'active'));
      });
      return () => unsubscribe();
    }
    const timer = window.setInterval(syncDisasterState, 10000);
    window.addEventListener('focus', syncDisasterState);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', syncDisasterState);
    };
  }, [currentUser.id]);

  const setMode = async (newMode: OperationalMode) => {
    await disasterService.setOperationalMode(newMode);
    await syncDisasterState();
  };

  const activateDisaster = async (disasterId: string) => {
    await disasterService.activateDisaster(disasterId);
    await syncDisasterState();
  };

  const resolveDisaster = async (disasterId: string) => {
    await disasterService.resolveDisaster(disasterId);
    await syncDisasterState();
  };

  return (
    <OperationalContext.Provider
      value={{
        mode,
        activeDisaster,
        isDisasterMode: mode === 'DISASTER',
        setMode,
        activateDisaster,
        resolveDisaster,
      }}
    >
      {children}
    </OperationalContext.Provider>
  );
};
