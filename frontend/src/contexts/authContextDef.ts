import { createContext } from 'react';
import { User, UserRole } from '../types';
import { LoginCredentials } from '../services/authService';

export interface AuthContextType {
  currentUser: User;
  assignedRoles: UserRole[];
  hasRole: (role: UserRole) => boolean;
  isCoordinator: boolean;
  isFoodProvider: boolean;
  isRecipient: boolean;
  isVolunteer: boolean;
  isAuthenticated: boolean;
  isLoading: boolean;
  allUsers: User[];
  login: (credentials: LoginCredentials) => Promise<User>;
  switchUser: (userId: string) => Promise<void>;
  logout: () => Promise<void>;
  resetDemoData: () => Promise<void>;
  // Backward compatibility aliases
  activeRole: UserRole;
  currentRole: UserRole;
  switchRole?: (role: UserRole) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
