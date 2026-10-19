import { User, UserRole } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, ensureCsrfToken } from './apiClient';
import { adaptUser } from './apiAdapters';

export interface LoginCredentials {
  email: string;
  password?: string;
}

export const authService = {
  /**
   * Retrieves currently authenticated user session.
   * In API mode, contacts GET /api/v1/auth/me/. Returns null if unauthenticated.
   */
  async getCurrentUser(): Promise<User | null> {
    if (!isApiMode()) {
      return mockRepository.getCurrentUser();
    }

    try {
      const res = await apiClient.get('/auth/me/');
      if (res.data?.user) {
        return adaptUser(res.data.user);
      }
      return null;
    } catch (err: any) {
      if (err.statusCode === 401 || err.statusCode === 403) {
        return null;
      }
      throw err;
    }
  },

  /**
   * Performs credential authentication.
   * Obtains CSRF cookie first, then posts credentials to /api/v1/auth/login/.
   */
  async login(credentials: LoginCredentials): Promise<User> {
    if (!isApiMode()) {
      const users = mockRepository.getUsers();
      let matched = users.find(
        (u) => u.email.trim().toLowerCase() === credentials.email.trim().toLowerCase()
      );
      if (!matched) {
        matched = users[0];
      }
      mockRepository.setCurrentUser(matched);
      return matched;
    }

    // Step 1: Handshake CSRF token
    await ensureCsrfToken();

    // Step 2: Submit credentials
    const res = await apiClient.post('/auth/login/', {
      email: credentials.email.trim(),
      password: credentials.password || 'password123',
    });

    const userData = res.data?.user || res.data;
    return adaptUser(userData);
  },

  /**
   * Terminates active user session.
   */
  async logout(): Promise<void> {
    if (!isApiMode()) {
      mockRepository.setCurrentUser(mockRepository.getUsers()[0]);
      return;
    }

    try {
      await apiClient.post('/auth/logout/');
    } catch (err) {
      console.warn('Backend logout encountered error, clearing client state:', err);
    }
  },

  /**
   * Registers a new organization user account.
   */
  async register(payload: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
    roles?: string[];
  }): Promise<User> {
    if (!isApiMode()) {
      const newUser: User = {
        id: `USR-${Date.now()}`,
        name: payload.full_name,
        fullName: payload.full_name,
        email: payload.email,
        phone: payload.phone || '',
        assignedRoles: (payload.roles as UserRole[]) || ['FOOD_PROVIDER'],
        status: 'active',
        createdAt: new Date().toISOString(),
      };
      mockRepository.setCurrentUser(newUser);
      return newUser;
    }

    await ensureCsrfToken();
    const res = await apiClient.post('/auth/register/', payload);
    const userData = res.data?.user || res.data;
    return adaptUser(userData);
  },

  async getAllUsers(): Promise<User[]> {
    return mockRepository.getUsers();
  },

  async hasRole(role: UserRole): Promise<boolean> {
    const current = await this.getCurrentUser();
    return current ? current.assignedRoles.includes(role) : false;
  },

  async resetDemoData(): Promise<void> {
    if (!isApiMode()) {
      mockRepository.resetToSeedData();
    }
  },
};

export default authService;
