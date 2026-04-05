import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AnalysisProgress from '../components/Analysis/AnalysisProgress';

interface TaskDetail {
  id: string;
  type: 'analysis' | 'consult' | 'auto' | 'batch';
  description: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input: string;
  result?: {
    summary?: string;
    report_url?: string;
    details?: Record<string, unknown>;
  };
  error?: string;
  created_at: string;
  updated_at: string;
}

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) return;
    
    fetchTaskDetail();
    const interval = setInterval(fetchTaskDetail, 3000);
    return () => clearInterval(interval);
  }, [taskId]);

  const fetchTaskDetail = async () => {
    if (!taskId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/dashboard/tasks/${taskId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTask(data);
      }
    } catch (error) {
      console.error('Failed to fetch task detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAnalysisStatus = () => {
    if (!task) return 'idle';
    switch (task.status) {
      case 'pending': return 'initializing';
      case 'processing': return 'analyzing';
      case 'completed': return 'completed';
      case 'failed': return 'error';
      default: return 'idle';
    }
  };

  const handleViewReport = () => {
    if (task?.result?.report_url) {
      window.open(task.result.report_url, '_blank');
    } else {
      navigate(`/report/${taskId}`);
    }
  };

  const handleRetry = () => {
    fetchTaskDetail();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-fluent-deepOcean-300 mb-4">任务不存在</p>
          <button 
            onClick={() => navigate('/dashboard')}
            className="text-fluent-gold-500 hover:text-fluent-gold-600 font-medium"
          >
            返回仪表盘
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-fluent-deepOcean-500">任务详情</h1>
            <p className="text-fluent-deepOcean-300 text-sm mt-1">
              任务ID: {taskId}
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-fluent-deepOcean-400 hover:text-fluent-deepOcean-500 transition-colors"
          >
            返回仪表盘
          </button>
        </div>

        <div className="mb-6 acrylic rounded-xl p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-fluent-gold-100 flex items-center justify-center text-xl">
              {task.type === 'analysis' ? '🏠' : task.type === 'consult' ? '💬' : '📊'}
            </div>
            <div>
              <p className="font-medium text-fluent-deepOcean-500">{task.description}</p>
              <p className="text-xs text-fluent-deepOcean-300">
                创建于 {new Date(task.created_at).toLocaleString('zh-CN')}
              </p>
            </div>
          </div>
        </div>

        <AnalysisProgress
          status={getAnalysisStatus() as any}
          progress={task.progress}
          result={task.result}
          error={task.error}
          onViewReport={handleViewReport}
          onRetry={handleRetry}
          showAgents={true}
        />

        {task.input && (
          <div className="mt-6 acrylic rounded-xl p-4 border border-white/30">
            <h3 className="font-medium text-fluent-deepOcean-500 mb-2">输入内容</h3>
            <p className="text-fluent-deepOcean-400 text-sm whitespace-pre-wrap">
              {task.input}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskDetailPage;
