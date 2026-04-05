import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { NotificationChannel, NotificationType } from '../types';

interface CreateChannelInput {
  type: NotificationType;
  name: string;
  config: {
    recipients?: string[];
    webhookUrl?: string;
    secret?: string;
  };
  enabled: boolean;
}

interface UpdateChannelInput extends Partial<CreateChannelInput> {
  id: string;
}

async function fetchChannels(): Promise<NotificationChannel[]> {
  const response = await fetch('/api/monitoring/channels');
  if (!response.ok) throw new Error('Failed to fetch notification channels');
  return response.json();
}

async function createChannel(data: CreateChannelInput): Promise<NotificationChannel> {
  const response = await fetch('/api/monitoring/channels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create notification channel');
  return response.json();
}

async function updateChannel(data: UpdateChannelInput): Promise<NotificationChannel> {
  const response = await fetch(`/api/monitoring/channels/${data.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update notification channel');
  return response.json();
}

async function deleteChannel(id: string): Promise<void> {
  const response = await fetch(`/api/monitoring/channels/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete notification channel');
}

async function testChannel(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`/api/monitoring/channels/${id}/test`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to test notification channel');
  return response.json();
}

export function useNotificationChannels() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['notification-channels'],
    queryFn: fetchChannels,
    staleTime: 60000,
  });

  const createMutation = useMutation({
    mutationFn: createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: updateChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
    },
  });

  const testMutation = useMutation({
    mutationFn: testChannel,
  });

  return {
    channels: data || [],
    isLoading,
    error,
    createChannel: createMutation.mutate,
    updateChannel: updateMutation.mutate,
    deleteChannel: deleteMutation.mutate,
    testChannel: testMutation.mutate,
    testResult: testMutation.data,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isTesting: testMutation.isPending,
  };
}

export default useNotificationChannels;
