import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

/**
 * NeighborNet AI - Core API Client
 * Manages Axios instance, base URL, withCredentials session handling, CSRF token injection,
 * and centralized error normalization.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const isApiMode = (): boolean => {
  const mode = import.meta.env.VITE_DATA_SOURCE || 'api';
  return mode.toLowerCase() === 'api';
};

// Helper to extract cookie by name
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Send session & CSRF cookies
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 15000,
});

let csrfPromise: Promise<string | null> | null = null;

// Ensure CSRF token is available before state-changing mutations
export async function ensureCsrfToken(): Promise<string | null> {
  let token = getCookie('csrftoken');
  if (token) return token;

  if (!csrfPromise) {
    csrfPromise = apiClient
      .get<{ csrfToken: string }>('/auth/csrf/')
      .then((res) => {
        csrfPromise = null;
        return res.data?.csrfToken || getCookie('csrftoken');
      })
      .catch((err) => {
        csrfPromise = null;
        console.warn('Failed to fetch CSRF token:', err.message);
        return null;
      });
  }

  return csrfPromise;
}

// Request interceptor: Inject X-CSRFToken header on unsafe methods
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const method = config.method?.toUpperCase();
    if (method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      let token = getCookie('csrftoken');
      if (!token) {
        token = await ensureCsrfToken();
      }
      if (token) {
        config.headers.set('X-CSRFToken', token);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Error normalization interface
export interface ApiErrorPayload {
  message: string;
  statusCode?: number;
  fieldErrors?: Record<string, string[]>;
  raw?: unknown;
}

export function normalizeApiError(error: unknown): ApiErrorPayload {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<any>;
    const status = axiosErr.response?.status;
    const data = axiosErr.response?.data;

    let message = 'An unexpected server error occurred. Please try again.';
    const fieldErrors: Record<string, string[]> = {};

    if (typeof data === 'string') {
      message = data;
    } else if (data && typeof data === 'object') {
      if (data.detail && typeof data.detail === 'string') {
        message = data.detail;
      } else if (data.message && typeof data.message === 'string') {
        message = data.message;
      } else if (data.error && typeof data.error === 'string') {
        message = data.error;
      } else {
        // Collect field validation errors
        const parts: string[] = [];
        for (const [key, val] of Object.entries(data)) {
          if (Array.isArray(val)) {
            fieldErrors[key] = val.map(String);
            parts.push(`${key}: ${val.join(', ')}`);
          } else if (typeof val === 'string') {
            fieldErrors[key] = [val];
            parts.push(`${key}: ${val}`);
          }
        }
        if (parts.length > 0) {
          message = parts.join(' | ');
        }
      }
    } else if (axiosErr.message) {
      if (axiosErr.code === 'ECONNABORTED') {
        message = 'Request timed out. Please check your network connection.';
      } else if (axiosErr.message === 'Network Error') {
        message = 'Cannot connect to backend server. Ensure Django is running on port 8000.';
      } else {
        message = axiosErr.message;
      }
    }

    return {
      message,
      statusCode: status,
      fieldErrors: Object.keys(fieldErrors).length > 0 ? fieldErrors : undefined,
      raw: data,
    };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  return { message: 'An unknown error occurred.' };
}

// Response interceptor: Normalize errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = normalizeApiError(error);
    return Promise.reject(normalized);
  }
);

export default apiClient;
