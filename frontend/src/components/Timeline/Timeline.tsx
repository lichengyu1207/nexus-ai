import React, { useEffect, useState, useRef } from 'react';

interface Step {
  id: string;
  task_id: string;
  step_name: string;
  step_order: number;
  agent_name: string;
  status: string;
  detail?: string;
  input_data: Record<string, any> | null;
  output_data: Record<string, any> | null;
  created_at: string;
  completed_at: string | null;
}

interface TimelineProps {
  taskId: string;
  className?: string;
}

const Timeline: React.FC<TimelineProps> = ({ taskId, className = '' }) => {
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const fetchSteps = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:8000/api/tasks/${taskId}/steps`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setSteps(data.steps || []);
        }
      } catch (err) {
        console.error('Failed to fetch steps:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSteps();

    // SSE connection for real-time updates
    const connectSSE = () => {
      const token = localStorage.getItem('token');
      const eventSource = new EventSource(
        `http://localhost:8000/api/tasks/${taskId}/stream?token=${token}`
      );
      
      eventSourceRef.current = eventSource;

      eventSource.addEventListener('step', (event) => {
        try {
          const step = JSON.parse(event.data);
          setSteps(prev => {
            const existing = prev.findIndex(s => s.id === step.id);
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = step;
              return updated.sort((a, b) => a.step_order - b.step_order);
            }
            return [...prev, step].sort((a, b) => a.step_order - b.step_order);
          });
        } catch (err) {
          console.error('Failed to parse step event:', err);
        }
      });

      eventSource.addEventListener('complete', () => {
        eventSource.close();
      });

      eventSource.onerror = () => {
        console.log('SSE connection error, reconnecting...');
        eventSource.close();
        setTimeout(connectSSE, 3000);
      };
    };

    connectSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [taskId]);

  // Group steps by agent
  const stepsByAgent = steps.reduce((acc, step) => {
    if (!acc[step.agent_name]) {
      acc[step.agent_name] = [];
    }
    acc[step.agent_name].push(step);
    return acc;
  }, {} as Record<string, Step[]>);

  const getAgentDisplayName = (agentName: string): string => {
    const names: Record<string, string> = {
      'supervisor': '主管代理',
      'requirement': '需求分析师',
      'collector': '数据采集师',
      'analyst': '市场分析师'
    };
    return names[agentName] || agentName;
  };

  const getAgentIcon = (agentName: string): string => {
    const icons: Record<string, string> = {
      'supervisor': '🧠',
      'requirement': '📋',
      'collector': '📊',
      'analyst': '📈'
    };
    return icons[agentName] || '🤖';
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'pending': 'bg-gray-200',
      'in_progress': 'bg-blue-500 animate-pulse',
      'running': 'bg-blue-500 animate-pulse',
      'completed': 'bg-green-500',
      'failed': 'bg-red-500'
    };
    return colors[status] || 'bg-gray-200';
  };

  const getStatusText = (status: string): string => {
    const texts: Record<string, string> = {
      'pending': '等待中',
      'in_progress': '进行中',
      'running': '运行中',
      'completed': '已完成',
      'failed': '失败'
    };
    return texts[status] || status;
  };

  if (loading) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="text-red-500 text-center">{error}</div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-4">执行进度</h3>
      
      {Object.entries(stepsByAgent).map(([agent, agentSteps]) => (
        <div key={agent} className="border rounded-lg p-4 bg-white shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-2xl">{getAgentIcon(agent)}</span>
            <h4 className="font-medium text-gray-700">{getAgentDisplayName(agent)}</h4>
          </div>
          
          <div className="ml-8 space-y-3">
            {agentSteps.map((step, index) => (
              <div key={step.id} className="relative">
                {index < agentSteps.length - 1 && (
                  <div className="absolute left-3 top-8 w-0.5 h-full bg-gray-200"></div>
                )}
                
                <div className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-full ${getStatusColor(step.status)} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                    {step.status === 'completed' && (
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {step.status === 'running' && (
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800">{step.step_name}</span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        step.status === 'completed' ? 'bg-green-100 text-green-700' :
                        step.status === 'in_progress' || step.status === 'running' ? 'bg-blue-100 text-blue-700' :
                        step.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {getStatusText(step.status)}
                      </span>
                    </div>
                    
                    {(step.output_data?.detail || step.detail) && (
                      <p className="text-sm text-gray-600 mt-1">{step.output_data?.detail || step.detail}</p>
                    )}
                    
                    {step.output_data?.message && (
                      <p className="text-sm text-gray-600 mt-1">{step.output_data.message}</p>
                    )}
                    
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(step.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      {steps.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          暂无执行步骤
        </div>
      )}
    </div>
  );
};

export default Timeline;
