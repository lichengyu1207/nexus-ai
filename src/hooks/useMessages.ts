import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  agentUsed?: string;
}

interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

interface MessagesResponse {
  messages: Message[];
  total: number;
  page: number;
  limit: number;
}

interface SessionsResponse {
  sessions: Session[];
  total: number;
}

const fetchSessions = async (): Promise<SessionsResponse> => {
  const response = await fetch('/api/chat/sessions');
  if (!response.ok) throw new Error('Failed to fetch sessions');
  return response.json();
};

const fetchMessages = async (
  sessionId: string,
  page: number = 1,
  limit: number = 50
): Promise<MessagesResponse> => {
  const response = await fetch(
    `/api/chat/sessions/${sessionId}/messages?page=${page}&limit=${limit}`
  );
  if (!response.ok) throw new Error('Failed to fetch messages');
  return response.json();
};

const sendMessage = async (data: {
  sessionId?: string;
  content: string;
  agent?: string;
}): Promise<{ sessionId: string; messageId: string }> => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
};

const deleteSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(`/api/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete session');
};

export const useSessions = () => {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: fetchSessions,
    staleTime: 5 * 60 * 1000,
  });
};

export const useMessages = (sessionId: string | null, page: number = 1) => {
  return useQuery({
    queryKey: ['messages', sessionId, page],
    queryFn: () => sessionId ? fetchMessages(sessionId, page) : Promise.resolve({ messages: [], total: 0, page: 1, limit: 50 }),
    enabled: !!sessionId,
    staleTime: 2 * 60 * 1000,
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendMessage,
    onSuccess: (_, variables) => {
      if (variables.sessionId) {
        queryClient.invalidateQueries({ queryKey: ['messages', variables.sessionId] });
      }
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
};

export const useDeleteSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
};
