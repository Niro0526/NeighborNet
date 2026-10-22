import { useState, useEffect, useRef, useCallback } from 'react';

export interface UseLivePollingOptions<T> {
  fetcher?: () => Promise<T>;
  intervalMs?: number;
  enabled?: boolean;
  refetchOnFocus?: boolean;
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (err: any) => void;
}

export interface UseLivePollingResult<T> {
  data: T | undefined;
  loading: boolean;
  isRefreshing: boolean;
  error: any;
  lastRefreshedAt: Date | null;
  refetch: () => Promise<void>;
  statusLabel: string;
  isPolling: boolean;
  lastPolledAt: Date | null;
  forcePoll: () => Promise<void>;
}

/**
 * useLivePolling:
 * Reliable live operational data updates across dashboards with:
 * - Configurable interval polling (default 15s)
 * - Refetch-on-focus / window tab visibility awareness
 * - In-flight request deduplication
 * - Graceful loading, empty, and network-error state management
 * - Clean unmount timer cleanup
 * - Clear distinction of refreshed server data
 */
export function useLivePolling<T>(
  fetcherOrOptions: (() => Promise<T>) | (UseLivePollingOptions<T> & { fetcher: () => Promise<T> }),
  options: UseLivePollingOptions<T> = {}
): UseLivePollingResult<T> {
  const fetcher = typeof fetcherOrOptions === 'function' ? fetcherOrOptions : fetcherOrOptions.fetcher;
  const mergedOptions = typeof fetcherOrOptions === 'function' ? options : fetcherOrOptions;
  const {
    intervalMs = 15000,
    enabled = true,
    refetchOnFocus = true,
    initialData,
    onSuccess,
    onError,
  } = mergedOptions;

  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<any>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const executeFetch = useCallback(
    async (isBackground = false) => {
      if (inFlightRef.current || !enabled) return;

      inFlightRef.current = true;
      if (isBackground) {
        setIsRefreshing(true);
      } else {
        setLoading(true);
      }

      try {
        const result = await fetcherRef.current();
        if (mountedRef.current) {
          setData(result);
          setError(null);
          setLastRefreshedAt(new Date());
          onSuccess?.(result);
        }
      } catch (err: any) {
        if (mountedRef.current) {
          setError(err);
          onError?.(err);
        }
      } finally {
        inFlightRef.current = false;
        if (mountedRef.current) {
          setLoading(false);
          setIsRefreshing(false);
        }
      }
    },
    [enabled, onSuccess, onError]
  );

  // Initial fetch and interval timer
  useEffect(() => {
    mountedRef.current = true;
    executeFetch(false);

    if (!enabled || intervalMs <= 0) return;

    const timer = setInterval(() => {
      executeFetch(true);
    }, intervalMs);

    return () => {
      clearInterval(timer);
      mountedRef.current = false;
    };
  }, [executeFetch, enabled, intervalMs]);

  // Window focus / tab visibility refetch
  useEffect(() => {
    if (!enabled || !refetchOnFocus) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        executeFetch(true);
      }
    };

    window.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleVisibilityChange);

    return () => {
      window.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleVisibilityChange);
    };
  }, [executeFetch, enabled, refetchOnFocus]);

  const statusLabel = lastRefreshedAt
    ? `Server data refreshed at ${lastRefreshedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} (${Math.round(intervalMs / 1000)}s poll)`
    : 'Connecting to database...';

  return {
    data,
    loading,
    isRefreshing,
    error,
    lastRefreshedAt,
    refetch: () => executeFetch(false),
    statusLabel,
    isPolling: isRefreshing,
    lastPolledAt: lastRefreshedAt,
    forcePoll: () => executeFetch(false),
  };
}

export default useLivePolling;
