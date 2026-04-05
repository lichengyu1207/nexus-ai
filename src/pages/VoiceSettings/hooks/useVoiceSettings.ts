import { useState, useEffect, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { VoiceSettings } from '../types';
import { DEFAULT_VOICE_SETTINGS } from '../types';

const STORAGE_KEY = 'voice-settings';

async function fetchVoiceSettings(): Promise<VoiceSettings> {
  try {
    const response = await fetch('/api/user/voice-settings');
    if (!response.ok) {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_VOICE_SETTINGS;
    }
    return response.json();
  } catch {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : DEFAULT_VOICE_SETTINGS;
  }
}

async function saveVoiceSettings(settings: VoiceSettings): Promise<VoiceSettings> {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  try {
    const response = await fetch('/api/user/voice-settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to save');
    return response.json();
  } catch {
    return settings;
  }
}

export function useVoiceSettings() {
  const queryClient = useQueryClient();
  const [localSettings, setLocalSettings] = useState<VoiceSettings | null>(null);

  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['voice-settings'],
    queryFn: fetchVoiceSettings,
  });

  const mutation = useMutation({
    mutationFn: saveVoiceSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(['voice-settings'], data);
      setLocalSettings(data);
    },
  });

  useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
    }
  }, [settings]);

  const updateSettings = useCallback((updates: Partial<VoiceSettings>) => {
    if (!localSettings) return;
    const newSettings = { ...localSettings, ...updates };
    setLocalSettings(newSettings);
    mutation.mutate(newSettings);
  }, [localSettings, mutation]);

  const updateEvent = useCallback((event: keyof VoiceSettings['events'], enabled: boolean) => {
    if (!localSettings) return;
    updateSettings({
      events: { ...localSettings.events, [event]: enabled },
    });
  }, [localSettings, updateSettings]);

  const setCustomSound = useCallback((type: keyof VoiceSettings['customSounds'], url: string | undefined) => {
    if (!localSettings) return;
    updateSettings({
      customSounds: { ...localSettings.customSounds, [type]: url },
    });
  }, [localSettings, updateSettings]);

  const setAgentVoice = useCallback((agentId: string, voiceURI: string) => {
    if (!localSettings) return;
    updateSettings({
      agentVoices: { ...localSettings.agentVoices, [agentId]: voiceURI },
    });
  }, [localSettings, updateSettings]);

  return {
    settings: localSettings ?? settings ?? DEFAULT_VOICE_SETTINGS,
    isLoading,
    error,
    updateSettings,
    updateEvent,
    setCustomSound,
    setAgentVoice,
    isSaving: mutation.isPending,
  };
}
