import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UserSettings, Theme, Language, NotificationSettings } from '../types';

async function fetchUserSettings(): Promise<UserSettings> {
  const response = await fetch('/api/user/settings');
  if (!response.ok) {
    throw new Error('Failed to fetch user settings');
  }
  return response.json();
}

async function updateUserSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
  const response = await fetch('/api/user/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    throw new Error('Failed to update user settings');
  }
  return response.json();
}

export function useUserSettings() {
  const queryClient = useQueryClient();

  const query = useQuery<UserSettings, Error>({
    queryKey: ['userSettings'],
    queryFn: fetchUserSettings,
    staleTime: 60000,
  });

  const updateMutation = useMutation<UserSettings, Error, Partial<UserSettings>>({
    mutationFn: updateUserSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] });
    },
  });

  const updateTheme = async (theme: Theme) => {
    return updateMutation.mutateAsync({ theme });
  };

  const updateLanguage = async (language: Language) => {
    return updateMutation.mutateAsync({ language });
  };

  const updateNotifications = async (notifications: NotificationSettings) => {
    return updateMutation.mutateAsync({ notifications });
  };

  const updateVoiceEnabled = async (voiceEnabled: boolean) => {
    return updateMutation.mutateAsync({ voiceEnabled });
  };

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateTheme,
    updateLanguage,
    updateNotifications,
    updateVoiceEnabled,
    updateSettings: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
  };
}
