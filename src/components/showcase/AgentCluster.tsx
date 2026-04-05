import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TaskWebSocket, MessageEvent, StatusEvent, WorkflowEvent, AgentStatusEvent } from '../../api/websocket';
import taskApi, { Task, AgentStatus, RealtimeMessage } from '../../api/task';

interface AgentClusterProps {
  taskId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
  compact?: boolean;
}

interface AgentInfo {
  id: string;
  name: string;
  icon: string;
  color: string;
  role: string;
  status: 'waiting' | 'working' | 'done';
  progress: number;
  message?: string;
  lastActive?: string;
}

const AGENT_CONFIG: Record<string, Omit<AgentInfo, 'status' | 'progress' | 'message' | 'lastActive'>> = {
  supervisor: {
    id: 'supervisor',
    name: '主管代理',
    icon: '🎯',
    color: '#D4AF37',
    role: '任务调度与协调',
  },
  requirement: {
    id: 'requirement',
    name: '需求解析',
    icon: '📋',
    color: '#3B82F6',
    role: '用户意图分析',
  },
  hubu: {
    id: 'hubu',
    name: '户部',
    icon: '💰',
    color: '#10B981',
    role: '房价数据采集',
  },
  analyst: {
    id: 'analyst',
    name: '分析师',
    icon: '📊',
    color: '#8B5CF6',
    role: '市场趋势分析',
  },
  bingbu: {
    id: 'bingbu',
    name: '兵部',
    icon: '🛡️',
    color: '#EF4444',
    role: '风险评估',
  },
  gongbu: {
    id: 'gongbu',
    name: '工部',
    icon: '🏗️',
    color: '#F59E0B',
    role: '城市规划分析',
  },
  libu: {
    id: 'libu',
    name: '吏部',
    icon: '📚',
    color: '#06B6D4',
    role: '教育资源分析',
  },
  report: {
    id: 'report',
    name: '报告生成',
    icon: '📝',
    color: '#EC4899',
    role: '综合报告输出',
  },
};

const AgentCluster: React.FC<AgentClusterProps> = ({
  taskId,
  onComplete,
  onError,
  compact = false,
}) => {
  const [agents, setAgents] = useState<AgentInfo[]>(() =>
    Object.values(AGENT_CONFIG).map((config) => ({
      ...config,
      status: 'waiting',
      progress: 0,
    }))
  );
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [taskProgress, setTaskProgress] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const wsRef = useRef<TaskWebSocket | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const updateAgentStatus = useCallback((agentId: string, updates: Partial<AgentInfo>) => {
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === agentId ? { ...agent, ...updates } : agent
      )
    );
  }, []);

  const handleAgentEvent = useCallback((event: AgentStatusEvent) => {
    updateAgentStatus(event.agentId, {
      status: event.status,
      progress: event.progress ?? 0,
      message: event.currentTask,
      lastActive: event.timestamp,
    });

    if (event.status === 'done') {
      setCompletedCount((prev) => prev + 1);
    }
  }, [updateAgentStatus]);

  const handleMessageEvent = useCallback((event: MessageEvent) => {
    const message: RealtimeMessage = {
      id: event.id,
      agentId: event.agentId,
      agentName: event.agentName,
      content: event.content,
      timestamp: event.timestamp,
      type: event.messageType,
    };

    setMessages((prev) => [...prev.slice(-49), message]);

    updateAgentStatus(event.agentId, {
      message: event.content,
      lastActive: event.timestamp,
    });
  }, [updateAgentStatus]);

  const handleStatusEvent = useCallback((event: StatusEvent) => {
    setTaskProgress(event.progress);

    if (event.status === 'completed') {
      onComplete?.();
    } else if (event.status === 'failed') {
      onError?.('任务处理失败');
    }
  }, [onComplete, onError]);

  const handleWorkflowEvent = useCallback((event: WorkflowEvent) => {
    updateAgentStatus(event.agent, {
      status: event.status === 'completed' ? 'done' : event.status === 'processing' ? 'working' : 'waiting',
      progress: event.progress ?? 0,
      message: event.action,
      lastActive: event.timestamp,
    });
  }, [updateAgentStatus]);

  useEffect(() => {
    wsRef.current = new TaskWebSocket({
      taskId,
      onAgent: handleAgentEvent,
      onMessage: handleMessageEvent,
      onStatus: handleStatusEvent,
      onWorkflow: handleWorkflowEvent,
      onConnected: () => setIsConnected(true),
      onError: (error) => {
        console.error('WebSocket error:', error);
        onError?.(error.message);
      },
      onDisconnect: () => setIsConnected(false),
    });

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, [taskId, handleAgentEvent, handleMessageEvent, handleStatusEvent, handleWorkflowEvent, onError]);

  useEffect(() => {
    if (!isConnected) {
      pollingRef.current = setInterval(async () => {
        try {
          const status = await taskApi.getTaskStatus(taskId);
          setTaskProgress(status.progress);

          status.agents.forEach((agent) => {
            updateAgentStatus(agent.id, {
              status: agent.status,
              progress: agent.progress ?? 0,
              message: agent.currentTask,
              lastActive: agent.lastActive,
            });
          });

          if (status.status === 'completed') {
            onComplete?.();
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 3000);

      return () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
      };
    }
  }, [isConnected, taskId, updateAgentStatus, onComplete]);

  const activeAgents = agents.filter((a) => a.status === 'working');
  const doneAgents = agents.filter((a) => a.status === 'done');

  return (
    <div style={{
      padding: compact ? '16px' : '24px',
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
      }}>
        <h3 style={{
          color: '#D4AF37',
          fontSize: compact ? '16px' : '20px',
          fontWeight: 600,
          margin: 0,
        }}>
          六部智能体协同分析
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}>
            <motion.div
              animate={{
                scale: isConnected ? [1, 1.2, 1] : 1,
                background: isConnected ? '#10B981' : '#EF4444',
              }}
              transition={{ duration: 1, repeat: isConnected ? Infinity : 0 }}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
              }}
            />
            <span style={{
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '12px',
            }}>
              {isConnected ? '实时连接' : '轮询模式'}
            </span>
          </div>
          <div style={{
            padding: '4px 12px',
            background: 'rgba(212, 175, 55, 0.1)',
            borderRadius: '12px',
            border: '1px solid rgba(212, 175, 55, 0.3)',
          }}>
            <span style={{
              color: '#D4AF37',
              fontSize: '13px',
              fontWeight: 500,
            }}>
              {completedCount}/{agents.length} 完成
            </span>
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: compact ? 'repeat(3, 1fr)' : 'repeat(4, 1fr)',
        gap: '12px',
        marginBottom: '20px',
      }}>
        <AnimatePresence>
          {agents.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              style={{
                position: 'relative',
                padding: '16px',
                background: agent.status === 'done'
                  ? `linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))`
                  : agent.status === 'working'
                  ? `linear-gradient(135deg, ${agent.color}20, ${agent.color}10)`
                  : 'rgba(255, 255, 255, 0.03)',
                borderRadius: '12px',
                border: `2px solid ${agent.status === 'working' ? agent.color : 'rgba(255, 255, 255, 0.1)'}`,
                overflow: 'hidden',
              }}
            >
              {agent.status === 'working' && (
                <motion.div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: `linear-gradient(90deg, transparent, ${agent.color}40, transparent)`,
                  }}
                  animate={{ x: ['-100%', '100%'] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <motion.span
                  style={{ fontSize: '24px' }}
                  animate={agent.status === 'working' ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 0.5, repeat: agent.status === 'working' ? Infinity : 0 }}
                >
                  {agent.icon}
                </motion.span>
                <div style={{ flex: 1 }}>
                  <div style={{
                    color: '#fff',
                    fontSize: '13px',
                    fontWeight: 600,
                  }}>
                    {agent.name}
                  </div>
                  <div style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '11px',
                  }}>
                    {agent.role}
                  </div>
                </div>
                {agent.status === 'done' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    style={{
                      width: '20px',
                      height: '20px',
                      background: '#10B981',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  >
                    ✓
                  </motion.div>
                )}
                {agent.status === 'working' && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{
                      width: '16px',
                      height: '16px',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      borderTopColor: agent.color,
                      borderRadius: '50%',
                    }}
                  />
                )}
              </div>

              {agent.message && agent.status === 'working' && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    fontSize: '11px',
                    color: agent.color,
                    padding: '6px 8px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '6px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {agent.message}
                </motion.div>
              )}

              {agent.status === 'working' && (
                <div style={{
                  marginTop: '8px',
                  height: '3px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <motion.div
                    style={{
                      height: '100%',
                      background: agent.color,
                    }}
                    animate={{ width: `${agent.progress}%` }}
                  />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div style={{
        height: '4px',
        background: 'rgba(255, 255, 255, 0.1)',
        borderRadius: '2px',
        overflow: 'hidden',
        marginBottom: '16px',
      }}>
        <motion.div
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, #D4AF37, #F59E0B)',
          }}
          animate={{ width: `${taskProgress}%` }}
        />
      </div>

      {messages.length > 0 && !compact && (
        <div style={{
          maxHeight: '150px',
          overflow: 'auto',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
        }}>
          {messages.slice(-10).map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 0',
                borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
              }}
            >
              <span style={{
                fontSize: '11px',
                color: AGENT_CONFIG[msg.agentId]?.color || '#fff',
                minWidth: '60px',
              }}>
                {msg.agentName || AGENT_CONFIG[msg.agentId]?.name || msg.agentId}
              </span>
              <span style={{
                flex: 1,
                fontSize: '12px',
                color: 'rgba(255, 255, 255, 0.7)',
              }}>
                {msg.content}
              </span>
              <span style={{
                fontSize: '10px',
                color: 'rgba(255, 255, 255, 0.4)',
              }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentCluster;
