import { useState, useCallback } from 'react';
import { Message } from '../types';
import { chatApi } from '../api';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentReportId, setCurrentReportId] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string, agent: 'zhouyu' | 'luxun') => {
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage(content, agent);
      
      const agentMsg: Message = {
        id: response.report_id,
        sender: 'agent',
        content: response.reply,
        timestamp: new Date(),
        agent,
      };
      
      setMessages(prev => [...prev, agentMsg]);
      setCurrentReportId(response.report_id);
      
      return response;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentReportId(null);
  }, []);

  return {
    messages,
    isLoading,
    currentReportId,
    sendMessage,
    clearMessages,
  };
};
