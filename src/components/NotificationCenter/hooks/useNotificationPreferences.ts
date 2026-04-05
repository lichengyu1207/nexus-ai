import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { NotificationPreference } from '../types';
import { DEFAULT_NOTIFICATION_PREFERENCES } from '../types';

const API_BASE = '/api/user/notification-preferences';
const STORAGE_KEY = 'notification_preferences';

function getStoredPreferences(): NotificationPreference[] | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function setStoredPreferences(preferences: NotificationPreference[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  } catch {
    console.error('Failed to store notification preferences');
  }
}

async function fetchPreferences(): Promise<NotificationPreference[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) {
    throw new Error('Failed to fetch notification preferences');
  }
  return response.json();
}

async function updatePreferences(
  preferences: NotificationPreference[]
): Promise<NotificationPreference[]> {
  const response = await fetch(API_BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferences }),
  });
  if (!response.ok) {
    throw new Error('Failed to update notification preferences');
  }
  return response.json();
}

export function useNotificationPreferences() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      const stored = getStoredPreferences();
      if (stored) {
        return stored;
      }
      try {
        const serverPreferences = await fetchPreferences();
        setStoredPreferences(serverPreferences);
        return serverPreferences;
      } catch {
        return DEFAULT_NOTIFICATION_PREFERENCES;
      }
    },
    staleTime: Infinity,
  });

  const updateMutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: (data) => {
      setStoredPreferences(data);
      queryClient.setQueryData(['notification-preferences'], data);
    },
  });

  const updateLocalPreferences = (
    type: NotificationPreference['type'],
    updates: Partial<Omit<NotificationPreference, 'type'>>
  ) => {
    const current = query.data ?? DEFAULT_NOTIFICATION_PREFERENCES;
    const updated = current.map((pref) =>
      pref.type === type ? { ...pref, ...updates } : pref
    );
    setStoredPreferences(updated);
    queryClient.setQueryData(['notification-preferences'], updated);
  };

  const getPreference = (type: NotificationPreference['type']) => {
    return (query.data ?? DEFAULT_NOTIFICATION_PREFERENCES).find(
      (pref) => pref.type === type
    );
  };

  const shouldShowPopup = (type: NotificationPreference['type']) => {
    const pref = getPreference(type);
    return pref?.enabled && pref.popup;
  };

  const shouldShowInApp = (type: NotificationPreference['type']) => {
    const pref = getPreference(type);
    return pref?.enabled && pref.inApp;
  };

  return {
    preferences: query.data ?? DEFAULT_NOTIFICATION_PREFERENCES,
    isLoading: query.isLoading,
    error: query.error,
    updatePreferences: updateMutation.mutate,
    updateLocalPreferences,
    getPreference,
    shouldShowPopup,
    shouldShowInApp,
    isUpdating: updateMutation.isPending,
  };
}
