import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Message, MessageInput, EndName } from '../types';

interface MessagesParams {
  endId: EndName;
  otherEnd: EndName;
  page?: number;
}

interface SendMessagePayload {
  toEnd: EndName;
  content: string;
  attachments?: File[];
}

async function fetchMessages(params: MessagesParams): Promise<Message[]> {
  const searchParams = new URLSearchParams({
    otherEnd: params.otherEnd,
    page: String(params.page || 1),
  });
  const response = await fetch(`/api/ends/${params.endId}/messages?${searchParams.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }
  return response.json();
}

async function sendMessage(
  endId: EndName,
  payload: SendMessagePayload
): Promise<Message> {
  const formData = new FormData();
  formData.append('toEnd', payload.toEnd);
  formData.append('content', payload.content);
  if (payload.attachments) {
    payload.attachments.forEach((file) => {
      formData.append('attachments', file);
    });
  }

  const response = await fetch(`/api/ends/${endId}/messages`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error('Failed to send message');
  }
  return response.json();
}

async function markMessagesAsRead(
  endId: EndName,
  messageIds: string[]
): Promise<void> {
  const response = await fetch(`/api/ends/${endId}/messages/read`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messageIds }),
  });
  if (!response.ok) {
    throw new Error('Failed to mark messages as read');
  }
}

export function useMessages(params: MessagesParams) {
  return useQuery<Message[], Error>({
    queryKey: ['messages', params.endId, params.otherEnd, params.page],
    queryFn: () => fetchMessages(params),
    staleTime: 30000,
    refetchOnWindowFocus: true,
  });
}

export function useSendMessage(endId: EndName) {
  const queryClient = useQueryClient();

  return useMutation<Message, Error, SendMessagePayload>({
    mutationFn: (payload) => sendMessage(endId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['messages', endId, variables.toEnd],
      });
    },
  });
}

export function useMarkMessagesAsRead(endId: EndName) {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { messageIds: string[]; otherEnd: EndName }>({
    mutationFn: ({ messageIds }) => markMessagesAsRead(endId, messageIds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['messages', endId, variables.otherEnd],
      });
    },
  });
}
