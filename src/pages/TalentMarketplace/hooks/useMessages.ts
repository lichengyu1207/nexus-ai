import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Message, Conversation } from '../types';

interface UseMessagesOptions {
  conversationId?: string;
  currentUserId: string;
}

interface SendMessageData {
  conversationId: string;
  content: string;
  type?: 'text' | 'file';
}

async function fetchConversations(): Promise<Conversation[]> {
  const response = await fetch('/api/conversations');
  if (!response.ok) throw new Error('Failed to fetch conversations');
  return response.json();
}

async function fetchMessages(conversationId: string): Promise<Message[]> {
  const response = await fetch(`/api/conversations/${conversationId}/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  return response.json();
}

async function sendMessage(data: SendMessageData): Promise<Message> {
  const response = await fetch('/api/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
}

async function markAsRead(messageIds: string[]): Promise<void> {
  await fetch('/api/messages/mark-read', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messageIds }),
  });
}

export function useMessages(options: UseMessagesOptions) {
  const { conversationId, currentUserId } = options;
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const conversationsQuery = useQuery({
    queryKey: ['conversations', currentUserId],
    queryFn: fetchConversations,
  });

  const messagesQuery = useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => fetchMessages(conversationId!),
    enabled: !!conversationId,
  });

  const sendMessageMutation = useMutation({
    mutationFn: sendMessage,
    onSuccess: (newMessage) => {
      queryClient.invalidateQueries({ queryKey: ['messages', newMessage.conversationId] });
      queryClient.invalidateQueries({ queryKey: ['conversations', currentUserId] });
    },
  });

  const markAsReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', conversationId] });
      queryClient.invalidateQueries({ queryKey: ['conversations', currentUserId] });
    },
  });

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/messages`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      wsRef.current = ws;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_message') {
        queryClient.invalidateQueries({ queryKey: ['messages', data.conversationId] });
        queryClient.invalidateQueries({ queryKey: ['conversations', currentUserId] });
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [currentUserId, queryClient]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connectWebSocket]);

  const totalUnreadCount = conversationsQuery.data?.reduce(
    (sum, conv) => sum + conv.unreadCount,
    0
  ) ?? 0;

  return {
    conversations: conversationsQuery.data ?? [],
    messages: messagesQuery.data ?? [],
    isLoadingConversations: conversationsQuery.isLoading,
    isLoadingMessages: messagesQuery.isLoading,
    error: conversationsQuery.error || messagesQuery.error,
    sendMessage: sendMessageMutation.mutate,
    isSending: sendMessageMutation.isPending,
    markAsRead: markAsReadMutation.mutate,
    totalUnreadCount,
    isConnected,
    currentConversation: conversationsQuery.data?.find((c) => c.id === conversationId),
  };
}
