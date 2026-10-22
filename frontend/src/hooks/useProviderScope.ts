import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { organizationService } from '../services/organizationService';
import { isApiMode } from '../services/apiClient';

export function useProviderScope() {
  const { currentUser } = useAuth();
  const [providerIds, setProviderIds] = useState<string[]>(
    currentUser.organizationId ? [currentUser.organizationId] : []
  );
  const [organizationName, setOrganizationName] = useState<string>('');
  const [ready, setReady] = useState(!isApiMode());

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!isApiMode()) {
        if (mounted) {
          setProviderIds(currentUser.organizationId ? [currentUser.organizationId] : []);
          setOrganizationName('');
          setReady(true);
        }
        return;
      }
      const orgs = await organizationService.getMyOrganizations();
      if (!mounted) return;
      setProviderIds(orgs.map((org) => org.id).filter(Boolean));
      setOrganizationName(orgs[0]?.name || '');
      setReady(true);
    })();
    return () => {
      mounted = false;
    };
  }, [currentUser.id, currentUser.organizationId]);

  return { providerIds, organizationName, userName: currentUser.name, ready };
}
