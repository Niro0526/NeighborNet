import { useContext } from 'react';
import { OperationalContext } from '../contexts/operationalContextDef';

export const useOperational = () => {
  const context = useContext(OperationalContext);
  if (!context) {
    throw new Error('useOperational must be used within an OperationalProvider');
  }
  return context;
};
