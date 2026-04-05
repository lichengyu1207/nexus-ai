/**
 * 智能体状态订阅服务
 * Agent Status Service
 * 
 * 通过WebSocket实时获取智能体状态
 */

import { create } from 'zustand';

export type AgentStatusType = 'idle' | 'busy' | 'thinking' | 'success' | 'error' | 'sleeping';

export type AgentDepartmentType = 
  | 'li' | 'gong' | 'hu' | 'bing' | 'li_guan' | 'xing'
  | 'attack' | 'defense' | 'memory';

export interface AgentStatus {
  agentId: string;
  status: AgentStatusType;
  department: AgentDepartmentType;
  energy: number;
  taskId?: string;
  lastUpdate: Date;
  message?: string;
}

export interface AgentStatusState {
  agents: Record<string, AgentStatus>;
  isConnected: boolean;
  connectionError: string | null;
  
  updateAgent: (status: AgentStatus) => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  getAgentStatus: (agentId: string) => AgentStatus | undefined;
  getAllAgents: () => AgentStatus[];
  getAgentsByDepartment: (department: AgentDepartmentType) => AgentStatus[];
  getAgentsByStatus: (status: AgentStatusType) => AgentStatus[];
}

export const useAgentStatusStore = create<AgentStatusState>((set, get) => ({
  agents: {},
  isConnected: false,
  connectionError: null,

  updateAgent: (status) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [status.agentId]: {
          ...status,
          lastUpdate: new Date(),
        },
      },
    })),

  setConnected: (connected) =>
    set({ isConnected: connected, connectionError: connected ? null : get().connectionError }),

  setError: (error) =>
    set({ connectionError: error, isConnected: false }),

  getAgentStatus: (agentId) => get().agents[agentId],

  getAllAgents: () => Object.values(get().agents),

  getAgentsByDepartment: (department) =>
    Object.values(get().agents).filter((agent) => agent.department === department),

  getAgentsByStatus: (status) =>
    Object.values(get().agents).filter((agent) => agent.status === status),
}));

export class AgentStatusService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string;
  private isManualClose = false;

  constructor(url: string = '/ws/agent-status') {
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
        console.log('[AgentStatusService] Connected');
        this.reconnectAttempts = 0;
        useAgentStatusStore.getState().setConnected(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('[AgentStatusService] Parse error:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('[AgentStatusService] Disconnected:', event.code, event.reason);
        useAgentStatusStore.getState().setConnected(false);

        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[AgentStatusService] Error:', error);
        useAgentStatusStore.getState().setError('Connection error');
      };
    } catch (error) {
      console.error('[AgentStatusService] Create connection error:', error);
      useAgentStatusStore.getState().setError('Failed to create connection');
    }
  }

  private handleMessage(data: any): void {
    if (data.type === 'status_update' && data.payload) {
      const status: AgentStatus = {
        agentId: data.payload.agent_id,
        status: data.payload.status,
        department: data.payload.department,
        energy: data.payload.energy,
        taskId: data.payload.task_id,
        lastUpdate: new Date(),
        message: data.payload.message,
      };
      useAgentStatusStore.getState().updateAgent(status);
    } else if (data.type === 'batch_update' && Array.isArray(data.payload)) {
      data.payload.forEach((item: any) => {
        const status: AgentStatus = {
          agentId: item.agent_id,
          status: item.status,
          department: item.department,
          energy: item.energy,
          taskId: item.task_id,
          lastUpdate: new Date(),
          message: item.message,
        };
        useAgentStatusStore.getState().updateAgent(status);
      });
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`[AgentStatusService] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
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

  subscribeToAgent(agentId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        agent_id: agentId,
      }));
    }
  }

  unsubscribeFromAgent(agentId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        agent_id: agentId,
      }));
    }
  }

  requestAllStatus(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_all_status',
      }));
    }
  }
}

let serviceInstance: AgentStatusService | null = null;

export const getAgentStatusService = (): AgentStatusService => {
  if (!serviceInstance) {
    serviceInstance = new AgentStatusService();
  }
  return serviceInstance;
};

export const useAgentStatus = (agentId: string): AgentStatus | undefined => {
  return useAgentStatusStore((state) => state.agents[agentId]);
};

export const useAllAgentStatuses = (): AgentStatus[] => {
  return useAgentStatusStore((state) => Object.values(state.agents));
};

export const useAgentConnectionStatus = (): { isConnected: boolean; error: string | null } => {
  return useAgentStatusStore((state) => ({
    isConnected: state.isConnected,
    error: state.connectionError,
  }));
};

export default AgentStatusService;
