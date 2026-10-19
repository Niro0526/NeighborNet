import React from 'react';
import { MantineProvider } from '@mantine/core';
import { theme } from '../styles/theme';
import { AuthProvider } from '../contexts/AuthContext';
import { OperationalProvider } from '../contexts/OperationalContext';

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <AuthProvider>
        <OperationalProvider>
          {children}
        </OperationalProvider>
      </AuthProvider>
    </MantineProvider>
  );
};
