import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CollaborationEvent, EndName, EndStatus } from '../types';

type EventFilter = 'all' | 'request' | 'response' | 'task_assignment';

interface CollaborationEventsParams {
  endId: EndName;
  filter?: EventFilter;
}

async function fetchCollaborationEvents(
  endId: EndName,
  filter: EventFilter = 'all'
): Promise<CollaborationEvent[]> {
  const params = new URLSearchParams();
  if (filter !== 'all') {
    params.append('filter', filter);
  }
  const response = await fetch(`/api/ends/${endId}/collaborations?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch collaboration events');
  }
  return response.json();
}

async function processEvent(eventId: string): Promise<CollaborationEvent> {
  const response = await fetch(`/api/collaborations/${eventId}/process`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to process event');
  }
  return response.json();
}

export function useCollaborationEvents(params: CollaborationEventsParams) {
  return useQuery<CollaborationEvent[], Error>({
    queryKey: ['collaborationEvents', params.endId, params.filter],
    queryFn: () => fetchCollaborationEvents(params.endId, params.filter),
    staleTime: 60000,
    refetchOnWindowFocus: true,
  });
}

export function useProcessEvent() {
  const queryClient = useQueryClient();

  return useMutation<CollaborationEvent, Error, { eventId: string; endId: EndName }>({
    mutationFn: ({ eventId }) => processEvent(eventId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['collaborationEvents', variables.endId],
      });
    },
  });
}
