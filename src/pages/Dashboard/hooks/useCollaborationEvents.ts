import { useQuery } from '@tanstack/react-query';
import type { CollaborationEvent } from '../types';

async function fetchCollaborationEvents(): Promise<CollaborationEvent[]> {
  const response = await fetch('/api/dashboard/collaboration-events');
  if (!response.ok) throw new Error('Failed to fetch collaboration events');
  return response.json();
}

export function useCollaborationEvents() {
  return useQuery({
    queryKey: ['dashboard', 'collaboration-events'],
    queryFn: fetchCollaborationEvents,
    staleTime: 60000,
    refetchInterval: 30000,
  });
}
