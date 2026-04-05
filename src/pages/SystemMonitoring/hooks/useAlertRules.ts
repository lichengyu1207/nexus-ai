import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AlertRule, AlertCondition } from '../types';

interface CreateAlertRuleInput {
  name: string;
  metric: string;
  condition: AlertCondition;
  threshold: number;
  duration: number;
  channels: string[];
  silenceMinutes: number;
}

interface UpdateAlertRuleInput extends Partial<CreateAlertRuleInput> {
  id: string;
}

async function fetchAlertRules(): Promise<AlertRule[]> {
  const response = await fetch('/api/monitoring/alerts/rules');
  if (!response.ok) throw new Error('Failed to fetch alert rules');
  return response.json();
}

async function createAlertRule(data: CreateAlertRuleInput): Promise<AlertRule> {
  const response = await fetch('/api/monitoring/alerts/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create alert rule');
  return response.json();
}

async function updateAlertRule(data: UpdateAlertRuleInput): Promise<AlertRule> {
  const response = await fetch(`/api/monitoring/alerts/rules/${data.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update alert rule');
  return response.json();
}

async function deleteAlertRule(id: string): Promise<void> {
  const response = await fetch(`/api/monitoring/alerts/rules/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete alert rule');
}

async function toggleAlertRule(id: string, enabled: boolean): Promise<AlertRule> {
  const response = await fetch(`/api/monitoring/alerts/rules/${id}/toggle`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) throw new Error('Failed to toggle alert rule');
  return response.json();
}

export function useAlertRules() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: fetchAlertRules,
    staleTime: 30000,
  });

  const createMutation = useMutation({
    mutationFn: createAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: updateAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      toggleAlertRule(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  return {
    rules: data || [],
    isLoading,
    error,
    createRule: createMutation.mutate,
    updateRule: updateMutation.mutate,
    deleteRule: deleteMutation.mutate,
    toggleRule: toggleMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isToggling: toggleMutation.isPending,
  };
}

export default useAlertRules;
