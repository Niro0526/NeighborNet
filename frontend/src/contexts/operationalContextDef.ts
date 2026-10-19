import { createContext } from 'react';
import { OperationalMode, DisasterEvent } from '../types';

export interface OperationalContextType {
  mode: OperationalMode;
  activeDisaster?: DisasterEvent;
  isDisasterMode: boolean;
  setMode: (mode: OperationalMode) => Promise<void>;
  activateDisaster: (disasterId: string) => Promise<void>;
  resolveDisaster: (disasterId: string) => Promise<void>;
}

export const OperationalContext = createContext<OperationalContextType | undefined>(undefined);
