/**
 * 记忆事件监听服务
 * Memory Event Service
 * 
 * 监听记忆系统的变化事件
 */

import { create } from 'zustand';

export type MemoryEventType = 
  | 'memory_retrieved' 
  | 'memory_stored' 
  | 'memory_consolidated'
  | 'memory_updated'
  | 'memory_deleted';

export interface MemoryEvent {
  id: string;
  type: MemoryEventType;
  memoryId: string;
  agentId?: string;
  timestamp: Date;
  data: Record<string, any>;
}

export interface RetrievedEvent extends MemoryEvent {
  type: 'memory_retrieved';
  data: {
    query: string;
    relevanceScore: number;
    relatedMemoryIds: string[];
  };
}

export interface StoredEvent extends MemoryEvent {
  type: 'memory_stored';
  data: {
    summary: string;
    importance: number;
    memoryType: string;
  };
}

export interface ConsolidatedEvent extends MemoryEvent {
  type: 'memory_consolidated';
  data: {
    sourceMemoryIds: string[];
    targetMemoryId: string;
    consolidationType: string;
  };
}

export interface MemoryEventState {
  events: MemoryEvent[];
  recentEvents: MemoryEvent[];
  isConnected: boolean;
  connectionError: string | null;
  
  addEvent: (event: MemoryEvent) => void;
  clearEvents: () => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  getEventsByType: (type: MemoryEventType) => MemoryEvent[];
  getEventsByAgent: (agentId: string) => MemoryEvent[];
}

const MAX_RECENT_EVENTS = 50;

export const useMemoryEventStore = create<MemoryEventState>((set, get) => ({
  events: [],
  recentEvents: [],
  isConnected: false,
  connectionError: null,

  addEvent: (event) =>
    set((state) => {
      const newEvents = [...state.events, event];
      const recentEvents = newEvents.slice(-MAX_RECENT_EVENTS);
      return { events: newEvents, recentEvents };
    }),

  clearEvents: () =>
    set({ events: [], recentEvents: [] }),

  setConnected: (connected) =>
    set({ isConnected: connected, connectionError: connected ? null : get().connectionError }),

  setError: (error) =>
    set({ connectionError: error, isConnected: false }),

  getEventsByType: (type) =>
    get().events.filter((event) => event.type === type),

  getEventsByAgent: (agentId) =>
    get().events.filter((event) => event.agentId === agentId),
}));

type MemoryEventCallback = (event: MemoryEvent) => void;

export class MemoryEventService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string;
  private isManualClose = false;
  private callbacks: Map<string, Set<MemoryEventCallback>> = new Map();

  constructor(url: string = '/ws/memory-events') {
    this.url = url;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isManualClose = false;
    this.createConnection();
  }

  private createConnection(): void {
    try {
      const wsUrl = this.url.startsWith('ws')
        ? this.url
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${this.url}`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[MemoryEventService] Connected');
        this.reconnectAttempts = 0;
        useMemoryEventStore.getState().setConnected(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('[MemoryEventService] Parse error:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('[MemoryEventService] Disconnected:', event.code, event.reason);
        useMemoryEventStore.getState().setConnected(false);

        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[MemoryEventService] Error:', error);
        useMemoryEventStore.getState().setError('Connection error');
      };
    } catch (error) {
      console.error('[MemoryEventService] Create connection error:', error);
      useMemoryEventStore.getState().setError('Failed to create connection');
    }
  }

  private handleMessage(data: any): void {
    const event: MemoryEvent = {
      id: data.id || `${Date.now()}-${Math.random()}`,
      type: data.type,
      memoryId: data.memory_id,
      agentId: data.agent_id,
      timestamp: new Date(data.timestamp || Date.now()),
      data: data.data || {},
    };

    useMemoryEventStore.getState().addEvent(event);

    const typeCallbacks = this.callbacks.get(event.type);
    if (typeCallbacks) {
      typeCallbacks.forEach((callback) => callback(event));
    }

    const allCallbacks = this.callbacks.get('*');
    if (allCallbacks) {
      allCallbacks.forEach((callback) => callback(event));
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[MemoryEventService] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (!this.isManualClose) {
        this.createConnection();
      }
    }, delay);
  }

  disconnect(): void {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(eventType: MemoryEventType | '*', callback: MemoryEventCallback): () => void {
    const key = eventType;
    if (!this.callbacks.has(key)) {
      this.callbacks.set(key, new Set());
    }
    this.callbacks.get(key)!.add(callback);

    return () => {
      this.callbacks.get(key)?.delete(callback);
    };
  }

  subscribeToMemoryType(memoryType: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_memory_type',
        memory_type: memoryType,
      }));
    }
  }

  requestRecentEvents(count: number = 20): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_recent_events',
        count,
      }));
    }
  }
}

let serviceInstance: MemoryEventService | null = null;

export const getMemoryEventService = (): MemoryEventService => {
  if (!serviceInstance) {
    serviceInstance = new MemoryEventService();
  }
  return serviceInstance;
};

export const useMemoryEvents = (): MemoryEvent[] => {
  return useMemoryEventStore((state) => state.recentEvents);
};

export const useMemoryEventsByType = (type: MemoryEventType): MemoryEvent[] => {
  return useMemoryEventStore((state) => state.getEventsByType(type));
};

export const useMemoryConnectionStatus = (): { isConnected: boolean; error: string | null } => {
  return useMemoryEventStore((state) => ({
    isConnected: state.isConnected,
    error: state.connectionError,
  }));
};

export const useSubscribeToMemoryEvent = (
  eventType: MemoryEventType | '*',
  callback: MemoryEventCallback
): void => {
  const service = getMemoryEventService();
  
  React.useEffect(() => {
    const unsubscribe = service.subscribe(eventType, callback);
    return unsubscribe;
  }, [eventType, callback, service]);
};

import React from 'react';

export default MemoryEventService;
