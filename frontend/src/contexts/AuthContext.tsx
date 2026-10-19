import React, { useState, useEffect, useCallback } from 'react';
import { User, UserRole } from '../types';
import { authService, LoginCredentials } from '../services/authService';
import { mockRepository } from '../services/mockRepository';
import { isApiMode } from '../services/apiClient';
import { AuthContext } from './authContextDef';

const GUEST_FALLBACK_USER: User = {
  id: '',
  name: 'Guest',
  fullName: 'Guest User',
  email: '',
  phone: '',
  assignedRoles: [],
  status: 'active',
  createdAt: new Date().toISOString(),
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User>(() => {
    return isApiMode() ? GUEST_FALLBACK_USER : mockRepository.getCurrentUser();
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [allUsers, setAllUsers] = useState<User[]>(mockRepository.getUsers());

  // Session restoration on mount
  useEffect(() => {
    let isMounted = true;

    if (isApiMode()) {
      (async () => {
        try {
          const user = await authService.getCurrentUser();
          if (isMounted) {
            if (user) {
              setCurrentUser(user);
            } else {
              setCurrentUser(GUEST_FALLBACK_USER);
            }
          }
        } catch (err) {
          console.warn('Session restoration encountered issue:', err);
          if (isMounted) setCurrentUser(GUEST_FALLBACK_USER);
        } finally {
          if (isMounted) setIsLoading(false);
        }
      })();
    } else {
      setIsLoading(false);
      const unsubscribe = mockRepository.subscribe(() => {
        setCurrentUser(mockRepository.getCurrentUser());
        setAllUsers(mockRepository.getUsers());
      });
      return () => unsubscribe();
    }

    return () => {
      isMounted = false;
    };
  }, []);

  const assignedRoles = currentUser.assignedRoles || [];

  const hasRole = useCallback(
    (role: UserRole) => {
      return (currentUser.assignedRoles || []).includes(role);
    },
    [currentUser]
  );

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const user = await authService.login(credentials);
      setCurrentUser(user);
      return user;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const switchUser = useCallback(
    async (userId: string) => {
      const target = allUsers.find((u) => u.id === userId);
      if (target) {
        if (!isApiMode()) {
          mockRepository.setCurrentUser(target);
          setCurrentUser(mockRepository.getCurrentUser());
        } else {
          // In API mode, autofill/re-login as target user with default password
          try {
            await login({ email: target.email, password: 'password123' });
          } catch (err) {
            console.warn('Switch user via API failed:', err);
          }
        }
      }
    },
    [allUsers, login]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setCurrentUser(isApiMode() ? GUEST_FALLBACK_USER : mockRepository.getUsers()[0]);
    }
  }, []);

  const resetDemoData = useCallback(async () => {
    await authService.resetDemoData();
    if (!isApiMode()) {
      setCurrentUser(mockRepository.getCurrentUser());
      setAllUsers(mockRepository.getUsers());
    }
  }, []);

  const switchRole = useCallback(
    async (role: UserRole) => {
      if ((currentUser.assignedRoles || []).includes(role)) {
        if (!isApiMode()) {
          mockRepository.switchActiveRole(role);
          setCurrentUser(mockRepository.getCurrentUser());
        } else {
          setCurrentUser((prev) => ({
            ...prev,
            activeRole: role,
          }));
        }
      }
    },
    [currentUser]
  );

  const primaryRole: UserRole = currentUser.activeRole || assignedRoles[0] || 'VOLUNTEER';

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        assignedRoles,
        hasRole,
        isCoordinator: assignedRoles.includes('COORDINATOR'),
        isFoodProvider: assignedRoles.includes('FOOD_PROVIDER'),
        isRecipient: assignedRoles.includes('RECIPIENT'),
        isVolunteer: assignedRoles.includes('VOLUNTEER'),
        isAuthenticated: Boolean(currentUser.id && currentUser.email),
        isLoading,
        allUsers,
        login,
        switchUser,
        logout,
        resetDemoData,
        activeRole: primaryRole,
        currentRole: primaryRole,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
