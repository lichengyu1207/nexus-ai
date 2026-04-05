import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Badge from '@/components/ui/badge';
import ScrollArea from '@/components/ui/scroll-area';
import Progress from '@/components/ui/progress';
import {
  Bot,
  MessageSquare,
  ArrowRight,
  CheckCircle,
  Clock,
  AlertCircle,
  Activity,
} from 'lucide-react';

interface AgentMessage {
  id: string;
  task_id: string;
  sender: string;
  recipient: string | null;
  type: 'request' | 'response' | 'notify' | 'error';
  content: Record<string, unknown>;
  in_reply_to: string | null;
  timestamp: string;
}

interface WorkflowStep {
  id: string;
  agent: string;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  details?: Record<string, unknown>;
}

interface AgentFlowProps {
  taskId: string;
  onMessage?: (message: AgentMessage) => void;
  onComplete?: (result: unknown) => void;
}

const AGENT_CONFIG: Record<string, { name: string; color: string; icon: string }> = {
  supervisor: { name: '主管代理', color: 'bg-purple-500', icon: '👑' },
  requirement: { name: '需求解析', color: 'bg-blue-500', icon: '📝' },
  collector: { name: '数据采集', color: 'bg-green-500', icon: '🔍' },
  analyst: { name: '分析代理', color: 'bg-orange-500', icon: '📊' },
  scheduler: { name: '调度器', color: 'bg-gray-500', icon: '⚙️' },
};

const AgentFlowVisualization: React.FC<AgentFlowProps> = ({
  taskId,
  onMessage,
  onComplete,
}) => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'completed' | 'error'>('connecting');
  const [progress, setProgress] = useState(0);

  const processMessage = useCallback((message: AgentMessage) => {
    setMessages(prev => [...prev, message]);

    if (message.content && typeof message.content === 'object' && 'action' in message.content) {
      const step: WorkflowStep = {
        id: message.id,
        agent: message.sender,
        action: String(message.content.action),
        status: message.type === 'error' ? 'failed' :
                message.type === 'response' ? 'completed' : 'running',
        timestamp: message.timestamp,
        details: message.content as Record<string, unknown>,
      };

      setWorkflowSteps(prev => {
        const existing = prev.findIndex(s =>
          s.agent === step.agent && s.action === step.action
        );
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = step;
          return updated;
        }
        return [...prev, step];
      });
    }

    if (message.content && 'action' in message.content && message.content.action === 'report') {
      setStatus('completed');
      setProgress(100);
      onComplete?.(message.content);
    }

    onMessage?.(message);
  }, [onMessage, onComplete]);

  useEffect(() => {
    if (!taskId) return;

    const eventSource = new EventSource(`/api/sse/tasks/${taskId}/stream`);

    eventSource.onopen = () => {
      setIsConnected(true);
      setStatus('connected');
    };

    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        processMessage(data);
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    });

    eventSource.addEventListener('status', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === 'completed') {
          setStatus('completed');
          setProgress(100);
        }
      } catch (e) {
        console.error('Failed to parse status event:', e);
      }
    });

    eventSource.addEventListener('workflow', (event) => {
      try {
        const data = JSON.parse(event.data);
        const step: WorkflowStep = {
          id: `${data.agent}-${data.action}`,
          agent: data.agent,
          action: data.action,
          status: data.status,
          timestamp: data.timestamp,
          details: data.details,
        };

        setWorkflowSteps(prev => {
          const existing = prev.findIndex(s => s.id === step.id);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = step;
            return updated;
          }
          return [...prev, step];
        });

        if (data.status === 'completed') {
          setProgress(prev => Math.min(prev + 25, 100));
        }
      } catch (e) {
        console.error('Failed to parse workflow event:', e);
      }
    });

    eventSource.onerror = () => {
      setIsConnected(false);
      setStatus('error');
    };

    return () => {
      eventSource.close();
    };
  }, [taskId, processMessage]);

  const getAgentConfig = (agentName: string) => {
    return AGENT_CONFIG[agentName] || {
      name: agentName,
      color: 'bg-gray-500',
      icon: '🤖',
    };
  };

  const getStatusIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'running':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Bot className="w-5 h-5" />
              代理协作流程
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant={isConnected ? 'default' : 'secondary'}>
                {isConnected ? '已连接' : '未连接'}
              </Badge>
              <Badge variant={
                status === 'completed' ? 'default' :
                status === 'error' ? 'destructive' : 'secondary'
              }>
                {status === 'completed' ? '已完成' :
                 status === 'error' ? '错误' :
                 status === 'connected' ? '处理中' : '连接中'}
              </Badge>
            </div>
          </div>
          <Progress value={progress} className="h-2 mt-2" />
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">工作流步骤</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {workflowSteps.map((step) => {
                  const config = getAgentConfig(step.agent);
                  return (
                    <div
                      key={step.id}
                      className="flex items-center gap-3 p-2 rounded-lg bg-gray-50"
                    >
                      <span className="text-lg">{config.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{config.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {step.action}
                          </Badge>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(step.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {getStatusIcon(step.status)}
                    </div>
                  );
                })}
                {workflowSteps.length === 0 && (
                  <div className="text-center text-gray-400 py-8">
                    等待代理开始工作...
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              消息流
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {messages.map((msg) => {
                  const senderConfig = getAgentConfig(msg.sender);
                  const recipientConfig = msg.recipient ? getAgentConfig(msg.recipient) : null;

                  return (
                    <div
                      key={msg.id}
                      className="p-2 rounded-lg bg-gray-50 text-xs"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span>{senderConfig.icon}</span>
                        <span className="font-medium">{senderConfig.name}</span>
                        {recipientConfig && (
                          <>
                            <ArrowRight className="w-3 h-3" />
                            <span>{recipientConfig.icon}</span>
                            <span className="font-medium">{recipientConfig.name}</span>
                          </>
                        )}
                        <Badge
                          variant={msg.type === 'error' ? 'destructive' : 'outline'}
                          className="ml-auto text-[10px]"
                        >
                          {msg.type}
                        </Badge>
                      </div>
                      <div className="text-gray-500 pl-6">
                        {'action' in msg.content && Boolean(msg.content.action) && (
                          <span className="font-medium">[{String(msg.content.action)}] </span>
                        )}
                        {'query' in msg.content && typeof msg.content.query === 'string' && Boolean(msg.content.query) && (
                          <span className="truncate block">{msg.content.query}</span>
                        )}
                        {'parsed' in msg.content && Boolean(msg.content.parsed) && typeof msg.content.parsed === 'object' && (
                          <span className="text-green-600">
                            {String((msg.content.parsed as Record<string, unknown>).city || '')} {String((msg.content.parsed as Record<string, unknown>).district || '')}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
                {messages.length === 0 && (
                  <div className="text-center text-gray-400 py-8">
                    等待消息...
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AgentFlowVisualization;
