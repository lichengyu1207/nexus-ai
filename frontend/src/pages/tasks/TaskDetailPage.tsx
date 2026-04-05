import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Timeline from '../../components/Timeline/Timeline';
import AnalysisProgress from '../../components/Analysis/AnalysisProgress';

interface Task {
  id: string;
  user_id: string;
  query: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  result: any;
  error: string;
  created_at: string;
  updated_at: string;
}

interface Step {
  id: string;
  task_id: string;
  agent_name: string;
  step_name: string;
  step_detail: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string;
}

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    fetchTask();
    fetchSteps();

    if (task?.status === 'processing') {
      const interval = setInterval(fetchSteps, 2000);
      return () => clearInterval(interval);
    }
  }, [taskId, task?.status]);

  const fetchTask = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTask(data);
      } else {
        setError('任务不存在');
      }
    } catch (err) {
      setError('获取任务失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchSteps = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}/steps`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSteps(data.steps || []);
      }
    } catch (err) {
      console.error('Failed to fetch steps:', err);
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
    navigate(`/virtual-office/${taskId}`);
  };

  const handleRetry = async () => {
    const token = localStorage.getItem('token');
    await fetch(`http://localhost:8000/api/tasks/${taskId}/retry`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    fetchTask();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold mb-4 text-fluent-deepOcean-500">{error || '任务不存在'}</h2>
          <Link to="/dashboard/tasks" className="text-fluent-gold-500 hover:text-fluent-gold-600 font-medium">
            返回任务列表
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link to="/dashboard/tasks" className="text-fluent-deepOcean-400 hover:text-fluent-deepOcean-500 transition-colors flex items-center gap-1">
            ← 返回任务列表
          </Link>
        </div>

        <div className="mb-6 acrylic rounded-xl p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-fluent-gold-100 flex items-center justify-center text-xl">
              📋
            </div>
            <div>
              <p className="font-medium text-fluent-deepOcean-500">{task.query}</p>
              <p className="text-xs text-fluent-deepOcean-300">
                任务ID: {task.id} · 创建于 {new Date(task.created_at).toLocaleString('zh-CN')}
              </p>
            </div>
          </div>
        </div>

        <AnalysisProgress
          status={getAnalysisStatus() as any}
          progress={task.progress}
          result={task.result ? {
            summary: typeof task.result === 'string' ? task.result : task.result.summary || '分析已完成',
            details: typeof task.result === 'object' ? task.result : undefined
          } : undefined}
          error={task.error}
          onViewReport={handleViewReport}
          onRetry={handleRetry}
          showAgents={true}
        />

        {steps.length > 0 && (
          <div className="mt-6 acrylic rounded-xl p-4 border border-white/30">
            <h3 className="font-medium text-fluent-deepOcean-500 mb-4">执行步骤</h3>
            <Timeline steps={steps} />
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskDetailPage;
