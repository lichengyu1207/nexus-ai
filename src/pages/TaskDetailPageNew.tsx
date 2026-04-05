import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeftIcon, 
  TrashIcon, 
  ArrowPathIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import GovernanceFlow from '@/components/workflow/GovernanceFlow';
import DepartmentStatus from '@/components/workflow/DepartmentStatus';
import AnimationTrilogy from '@/components/ui/AnimationTrilogy';
import AnalysisReport from '@/components/ui/AnalysisReport';
import api from '@/services/api';

interface ProvinceStep {
  name: string;
  nameCn: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
}

interface WorkflowStep {
  id: string;
  province: string;
  department?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
  step_name?: string;
}

interface TaskResult {
  summary?: string;
  findings?: string[];
  recommendations?: string[];
  report?: string;
  integral_cost?: number;
  steps_count?: number;
}

interface TaskData {
  id: string;
  query: string;
  status: 'queued' | 'planning' | 'reviewing' | 'executing' | 'completed' | 'failed';
  progress: number;
  style?: string;
  result?: TaskResult;
  error?: string;
  created_at?: string;
  updated_at?: string;
  workflow_steps?: WorkflowStep[];
  current_province?: 'zhongshu' | 'menxia' | 'shangshu';
  current_department?: string;
}

const TaskDetailPageNew: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [taskData, setTaskData] = useState<TaskData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAnimation, setShowAnimation] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);
  
  // Use ref to track previous status in polling closure
  const previousStatusRef = React.useRef<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    let isMounted = true;
    let pollIntervalId: ReturnType<typeof setInterval> | null = null;

    const fetchTask = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.get(`/tasks/${taskId}`);
        if (isMounted) {
          setTaskData(response.data);
          previousStatusRef.current = response.data.status;
        }
      } catch (err: unknown) {
        console.error('Failed to fetch task:', err);
        if (isMounted && err && typeof err === 'object' && 'response' in err) {
          const axiosErr = err as { response?: { status?: number } };
          if (axiosErr.response?.status === 404) {
            setError('任务不存在');
          } else if (axiosErr.response?.status === 401) {
            setError('请先登录');
          } else {
            setError('加载任务失败');
          }
        } else if (isMounted) {
          setError('加载任务失败');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchTask();

    // Polling mechanism for task updates (every 2 seconds for faster updates)
    pollIntervalId = setInterval(async () => {
      if (!taskId || !isMounted) return;
      
      try {
        const response = await api.get(`/tasks/${taskId}`);
        const newTaskData = response.data;
        
        if (!isMounted) return;
        
        // Check if task just completed
        if (previousStatusRef.current !== 'completed' && newTaskData.status === 'completed') {
          setShowAnimation(true);
        }
        
        previousStatusRef.current = newTaskData.status;
        setTaskData(newTaskData);
        
        // Stop polling if task is completed or failed
        if (newTaskData.status === 'completed' || newTaskData.status === 'failed') {
          if (pollIntervalId) {
            clearInterval(pollIntervalId);
            pollIntervalId = null;
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    // SSE connection as backup
    const token = localStorage.getItem('token');
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    let eventSource: EventSource | null = null;
    
    if (token) {
      try {
        eventSource = new EventSource(`${baseURL}/api/sse/tasks/${taskId}/stream?token=${token}`);
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (isMounted) {
              setTaskData((prev: TaskData | null) => ({
                ...prev,
                ...data,
              } as TaskData));
            }
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        };

        eventSource.onerror = () => {
          console.log('SSE connection failed, using polling instead');
          if (eventSource) {
            eventSource.close();
          }
        };
      } catch {
        console.log('SSE not available, using polling');
      }
    }

    return () => {
      isMounted = false;
      if (pollIntervalId) {
        clearInterval(pollIntervalId);
      }
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [taskId]);

  const handleDelete = async () => {
    if (!taskId || !confirm('确定要删除这个任务吗？')) return;
    
    try {
      await api.delete(`/tasks/${taskId}`);
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const handleRetry = async () => {
    if (!taskId) return;
    
    try {
      await api.post(`/tasks/${taskId}/retry`);
      // Refresh task data
      const response = await api.get(`/tasks/${taskId}`);
      setTaskData(response.data);
    } catch (error) {
      console.error('Failed to retry task:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (error || !taskData) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {error || '任务不存在'}
        </h2>
        <p className="text-gray-500 mb-4">该任务可能已被删除或不存在</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >
          返回仪表盘
        </button>
      </div>
    );
  }

  const statusConfig = {
    queued: { icon: ClockIcon, color: 'text-yellow-500', label: '排队中' },
    planning: { icon: ClockIcon, color: 'text-purple-500', label: '中书省规划中' },
    reviewing: { icon: ClockIcon, color: 'text-blue-500', label: '门下省审核中' },
    executing: { icon: ClockIcon, color: 'text-green-500', label: '尚书省执行中' },
    completed: { icon: CheckCircleIcon, color: 'text-green-500', label: '已完成' },
    failed: { icon: ExclamationCircleIcon, color: 'text-red-500', label: '失败' },
  };

  const currentStatus = statusConfig[taskData.status as keyof typeof statusConfig] || statusConfig.queued;
  const StatusIcon = currentStatus.icon;

  // 转换工作流步骤
  const workflowSteps: ProvinceStep[] = [
    { 
      name: 'zhongshu', 
      nameCn: '中书省',
      description: '决策规划 - 制定分析方案',
      status: taskData.status === 'queued' ? 'pending' : 
            taskData.status === 'planning' ? 'running' : 'completed',
      progress: taskData.status === 'queued' ? 0 : 
            taskData.status === 'planning' ? (taskData.progress || 33) : 100
    },
    { 
      name: 'menxia', 
      nameCn: '门下省',
      description: '审核监督 - 合规检查与方案审核',
      status: ['queued', 'planning'].includes(taskData.status) ? 'pending' : 
            taskData.status === 'reviewing' ? 'running' : 'completed',
      progress: ['queued', 'planning'].includes(taskData.status) ? 0 : 
            taskData.status === 'reviewing' ? (taskData.progress || 66) : 100
    },
    { 
      name: 'shangshu', 
      nameCn: '尚书省',
      description: '执行实施 - 六部协同执行任务',
      status: ['queued', 'planning', 'reviewing'].includes(taskData.status) ? 'pending' : 
            taskData.status === 'executing' ? 'running' : 'completed',
      progress: ['queued', 'planning', 'reviewing'].includes(taskData.status) ? 0 : 
            taskData.status === 'executing' ? (taskData.progress || 0) : 100
    },
  ];

  // 从 workflow_steps 中提取六部状态
  const getDepartmentStatus = (deptName: string): { status: 'pending' | 'running' | 'completed' | 'failed'; progress: number; task?: string } => {
    if (!taskData?.workflow_steps || !Array.isArray(taskData.workflow_steps)) {
      return { status: 'pending', progress: 0 };
    }
    
    const deptStep = taskData.workflow_steps.find(
      (step: WorkflowStep) => step.department === deptName || step.province === deptName
    );
    
    if (deptStep) {
      return {
        status: deptStep.status,
        progress: deptStep.progress || 0,
        task: deptStep.step_name,
      };
    }
    
    return { status: 'pending', progress: 0 };
  };

  // 转换六部状态
  const departments: DepartmentStatus[] = [
    { name: 'LIBU', nameCn: '吏部', ...getDepartmentStatus('吏部') },
    { name: 'HUBU', nameCn: '户部', ...getDepartmentStatus('户部') },
    { name: 'LIBU_LI', nameCn: '礼部', ...getDepartmentStatus('礼部') },
    { name: 'BINGBU', nameCn: '兵部', ...getDepartmentStatus('兵部') },
    { name: 'XINGBU', nameCn: '刑部', ...getDepartmentStatus('刑部') },
    { name: 'GONGBU', nameCn: '工部', ...getDepartmentStatus('工部') },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              任务详情
            </h1>
            <p className="text-sm text-gray-500">{taskData.query}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {taskData.status === 'failed' && (
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <ArrowPathIcon className="w-4 h-4" />
              重试
            </button>
          )}
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            <TrashIcon className="w-4 h-4" />
            删除
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusIcon className={`w-6 h-6 ${currentStatus.color}`} />
            <div>
              <span className="font-medium text-gray-900 dark:text-white">
                {currentStatus.label}
              </span>
              {taskData.current_province && (
                <span className="text-sm text-gray-500 ml-2">
                  当前阶段: {taskData.current_province}
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold text-primary-600">{taskData.progress || 0}%</span>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${taskData.progress || 0}%` }}
              className="bg-primary-500 h-2 rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Governance Flow */}
      <GovernanceFlow
        currentProvince={taskData.current_province}
        steps={workflowSteps}
        overallProgress={taskData.progress || 0}
      />

      {/* Department Status */}
      {taskData.status === 'executing' && (
        <DepartmentStatus
          departments={departments}
          activeDepartment={taskData.current_department}
        />
      )}

      {/* Animation Trilogy */}
      <AnimatePresence>
        {showAnimation && (
          <AnimationTrilogy
            duration={6000}
            onComplete={() => {
              setShowAnimation(false);
              setAnimationComplete(true);
            }}
          />
        )}
      </AnimatePresence>

      {/* Result */}
      {taskData.status === 'completed' && taskData.result && animationComplete && (
        <AnalysisReport
          reportData={{
            summary: taskData.result.summary,
            findings: taskData.result.findings,
            recommendations: taskData.result.recommendations,
            report: taskData.result.report,
            integral_cost: taskData.result.integral_cost,
            steps_count: taskData.result.steps_count,
          }}
          taskId={taskId}
        />
      )}

      {/* Error */}
      {taskData.status === 'failed' && taskData.error && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border border-red-200 dark:border-red-800">
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 mb-2">
            错误信息
          </h3>
          <p className="text-red-600 dark:text-red-300">{taskData.error}</p>
        </div>
      )}
    </div>
  );
};

export default TaskDetailPageNew;
