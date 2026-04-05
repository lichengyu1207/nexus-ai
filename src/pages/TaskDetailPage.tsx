import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ClockIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ArrowPathIcon,
  WifiIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentListIcon,
  EyeIcon,
  ShareIcon,
  UserGroupIcon,
  CheckCircleIcon,
  ChatBubbleLeftRightIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';
import { taskApi, Task, TaskStep, teamApi, Team, commentApi } from '@/services/api';
import { useAppContextStore } from '@/store/appContextStore';
import AgentCard from '@/components/AgentCard';
import ReportViewer from '@/components/ReportViewer';
import CommentPanel from '@/components/comments/CommentPanel';
import SaveMemoryModal from '@/components/SaveMemoryModal';
import TaskDistributePanel from '@/components/TaskDistributePanel';
import useTaskStream from '@/hooks/useTaskStream';
import useReportProgress from '@/hooks/useReportProgress';
import { TaskLoadingWithMascot, EmptyStateWithMascot, useMascotToast } from '@/components/mascot';
import showToast from '@/utils/toast';

type TabType = 'workflow' | 'report' | 'comments';

const sectionLabels: Record<string, string> = {
  summary: '执行摘要',
  key_findings: '核心发现',
  detailed_analysis: '详细分析',
  investment_advice: '投资建议',
  risk_warning: '风险提示',
  data_sources: '数据来源',
};

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { showReportComplete } = useMascotToast();
  const [task, setTask] = useState<Task | null>(null);
  const [steps, setSteps] = useState<TaskStep[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('workflow');
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [hasShownCompleteToast, setHasShownCompleteToast] = useState(false);
  
  const [showShareModal, setShowShareModal] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [sharedTeams, setSharedTeams] = useState<string[]>([]);
  const [commentCount, setCommentCount] = useState(0);
  const [showMemoryModal, setShowMemoryModal] = useState(false);
  const { setCurrentTask, currentTeam } = useAppContextStore();

  const loadTask = useCallback(async () => {
    if (!taskId) return;
    try {
      const data = await taskApi.get(taskId);
      setTask(data);
      setCurrentTask({
        id: data.id,
        title: data.query.slice(0, 50),
        status: data.status,
      });
      return data;
    } catch (error) {
      console.error('加载任务失败:', error);
      return null;
    }
  }, [taskId, setCurrentTask]);

  const loadSteps = useCallback(async () => {
    if (!taskId) return;
    try {
      const data = await taskApi.getSteps(taskId);
      setSteps(data);
    } catch (error) {
      console.error('加载步骤失败:', error);
    }
  }, [taskId]);

  const loadReport = useCallback(async () => {
    if (!taskId || !task) return;
    if (task.status !== 'completed') return;
    
    setReportLoading(true);
    setReportError(null);
    
    try {
      const data = await taskApi.getReport(taskId);
      setReport(data.report);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setReportError(err.response?.data?.detail || '加载报告失败');
    } finally {
      setReportLoading(false);
    }
  }, [taskId, task]);

  const loadTeams = useCallback(async () => {
    try {
      const data = await teamApi.list();
      setTeams(data);
      
      if (task) {
        const shared = data.filter((t: Team) => {
            return t.shared_tasks?.some((st: { task_id: string }) => st.task_id === taskId);
          }).map(t => t.id);
          setSharedTeams(shared);
        }
      }
    } catch (error) {
      console.error('加载团队失败:', error);
    }
  }, [task]);

  const loadCommentCount = useCallback(async () => {
    if (!taskId || task?.status !== 'completed') return;
    try {
      const result = await commentApi.list(taskId, 1, 0);
      setCommentCount(result.total);
    } catch (error) {
      console.error('加载评论数量失败:', error);
    }
  }, [taskId, task?.status]);

  const handleShareTask = async () => {
    if (!selectedTeamId || !taskId) return;
    
    setIsSharing(true);
    try {
      await teamApi.shareTask(selectedTeamId, taskId);
      showToast.success('任务已分享到团队');
      setSharedTeams([...sharedTeams, selectedTeamId]);
      setShowShareModal(false);
    } catch (error) {
      showToast.error('分享失败，请重试');
    } finally {
      setIsSharing(false);
    }
  };

  const handleStreamComplete = useCallback(() => {
    loadTask();
    loadSteps();
  }, [loadTask, loadSteps]);

  const handleStreamStatus = useCallback((status: { status: string; details?: { progress?: number } }) => {
    if (task && status.details?.progress !== undefined) {
      setTask(prev => prev ? { ...prev, progress: status.details!.progress!, status: status.status } : prev);
    }
  }, [task]);

  const { 
    isConnected, 
    status: streamStatus, 
    messages, 
    workflowSteps,
    error: streamError,
  } = useTaskStream({
    taskId,
    onStatus: handleStreamStatus,
    onComplete: handleStreamComplete,
    fallbackPolling: true,
    pollingInterval: 3000,
  });

  const {
    isGenerating,
    currentSection,
    currentAgent,
    isAgentHighlighted,
    getAgentHighlight,
  } = useReportProgress({
    taskId,
    onHighlight: (highlight) => {
      console.log('Timeline highlight:', highlight);
    },
  });

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      const taskData = await loadTask();
      await loadSteps();
      await loadTeams();
      setIsLoading(false);
      
      if (taskData && taskData.status === 'completed') {
        setActiveTab('report');
        loadCommentCount();
      }
    };
    
    init();
  }, [taskId]);

  useEffect(() => {
    if (task?.status === 'completed' && activeTab === 'report' && !report) {
      loadReport();
    }
  }, [task, activeTab, report, loadReport]);

  useEffect(() => {
    if (task?.status === 'completed' && !hasShownCompleteToast) {
      showReportComplete();
      setHasShownCompleteToast(true);
    }
  }, [task?.status, hasShownCompleteToast, showReportComplete]);

  const getAgentSteps = (agentName: string) => {
    const agentSteps = steps.filter(step => step.agent_name === agentName);
    const streamSteps = workflowSteps.filter(s => s.agent === agentName);
    
    const allSteps = [
      ...agentSteps.map(step => ({
        name: step.step_name,
        status: step.status,
        detail: step.error_message || undefined,
      })),
      ...streamSteps.map(s => ({
        name: s.action,
        status: s.status,
        detail: undefined,
      })),
    ];
    
    return [...new Map(allSteps.map(s => [s.name, s])).values()];
  };

  const getAgentStatus = (agentName: string) => {
    const agentSteps = steps.filter(step => step.agent_name === agentName);
    const streamSteps = workflowSteps.filter(s => s.agent === agentName);
    
    if (agentSteps.length === 0 && streamSteps.length === 0) return 'pending';
    if (agentSteps.some(s => s.status === 'failed') || streamSteps.some(s => s.status === 'failed')) return 'failed';
    if (agentSteps.some(s => s.status === 'running') || streamSteps.some(s => s.status === 'running')) return 'running';
    if (agentSteps.every(s => s.status === 'completed') && streamSteps.every(s => s.status === 'completed')) return 'completed';
    return 'pending';
  };

  const getAgentTimes = (agentName: string) => {
    const agentSteps = steps.filter(step => step.agent_name === agentName);
    if (agentSteps.length === 0) return { startedAt: null, completedAt: null };
    
    const startedSteps = agentSteps.filter(s => s.started_at);
    const completedSteps = agentSteps.filter(s => s.completed_at);
    
    const startedAt = startedSteps.length > 0 
      ? startedSteps.reduce((min, s) => 
          new Date(s.started_at!) < new Date(min!) ? s.started_at : min, startedSteps[0].started_at)
      : null;
    
    const completedAt = completedSteps.length > 0 
      ? completedSteps.reduce((max, s) => 
          new Date(s.completed_at!) > new Date(max!) ? s.completed_at : max, completedSteps[0].completed_at)
      : null;
    
    return { startedAt, completedAt };
  };

  const agents = ['supervisor', 'requirement', 'collector', 'analyst'];

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { bg: string; text: string; label: string }> = {
      completed: { bg: 'bg-green-100', text: 'text-green-700', label: '已完成' },
      failed: { bg: 'bg-red-100', text: 'text-red-700', label: '失败' },
      running: { bg: 'bg-blue-100', text: 'text-blue-700', label: '进行中' },
      pending: { bg: 'bg-gray-100', text: 'text-gray-700', label: '等待中' },
    };
    const config = configs[status] || configs.pending;
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getConnectionIndicator = () => {
    if (streamStatus === 'connected' && isConnected) {
      return (
        <span className="flex items-center gap-2 text-sm text-green-600">
          <WifiIcon className="w-4 h-4" />
          实时连接
        </span>
      );
    }
    if (streamStatus === 'connecting') {
      return (
        <span className="flex items-center gap-2 text-sm text-yellow-600">
          <ArrowPathIcon className="w-4 h-4 animate-spin" />
          连接中...
        </span>
      );
    }
    if (streamError) {
      return (
        <span className="flex items-center gap-2 text-sm text-orange-600">
          <ExclamationTriangleIcon className="w-4 h-4" />
          轮询模式
        </span>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <TaskLoadingWithMascot
          status="pending"
          taskName="加载任务详情"
        />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <EmptyStateWithMascot
          type="error"
          title="任务不存在"
          description="该任务可能已被删除或ID不正确"
          message="找不到这个任务，让我帮你找找其他的～"
          actionText="返回任务列表"
          actionHref="/tasks"
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/tasks" className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1">
            <ArrowLeftIcon className="w-4 h-4" />
            返回任务列表
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">任务详情</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {task.id}</p>
        </div>
        <div className="flex items-center gap-3">
          {task.status === 'completed' && (
            <>
              <button
                onClick={() => setShowMemoryModal(true)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
              >
                <BookmarkIcon className="w-4 h-4" />
                存入记忆
              </button>
              <button
                onClick={() => setShowShareModal(true)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
              >
                <ShareIcon className="w-4 h-4" />
                分享到团队
              </button>
              <Link
                to={`/tasks/${taskId}/report`}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
              >
                <EyeIcon className="w-4 h-4" />
                查看报告
              </Link>
            </>
          )}
          {getConnectionIndicator()}
          {getStatusBadge(task.status)}
        </div>
      </div>

      {/* Task Info Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-3">查询内容</h2>
        <p className="text-gray-700 dark:text-gray-300 text-lg">{task.query}</p>
        <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <ChartBarIcon className="w-4 h-4" />
            风格: <span className="font-medium text-gray-700 dark:text-gray-300">{task.style === 'conservative' ? '保守型' : task.style === 'aggressive' ? '激进型' : '平衡型'}</span>
          </span>
          <span className="flex items-center gap-1">
            <ClockIcon className="w-4 h-4" />
            创建: {formatDate(task.created_at)}
          </span>
          {task.completed_at && (
            <span className="flex items-center gap-1">
              完成: {formatDate(task.completed_at)}
            </span>
          )}
        </div>
        
        {task.status === 'running' && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">整体进度</span>
              <span className="font-medium text-primary-600">{task.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
              <TaskLoadingWithMascot
                status="running"
                progress={task.progress}
                taskName={task.query.slice(0, 50) + (task.query.length > 50 ? '...' : '')}
                onComplete={() => setActiveTab('report')}
                size="lg"
              />
            </div>
          </div>
        )}
      </div>

      {/* Shared Teams Indicator */}
      {sharedTeams.length > 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
            <div>
              <p className="font-medium text-green-700 dark:text-green-300">已分享到团队</p>
              <p className="text-sm text-green-600 dark:text-green-400">
                {teams.filter(t => sharedTeams.includes(t.id)).map(t => t.name).join('、 ')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="border-b border-gray-100 dark:border-gray-700">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('workflow')}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'workflow'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <ArrowPathIcon className="w-4 h-4" />
              工作流程
            </button>
            <button
              onClick={() => setActiveTab('report')}
              disabled={task.status !== 'completed'}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'report'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              } ${task.status !== 'completed' ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <ClipboardDocumentListIcon className="w-4 h-4" />
              分析报告
              {task.status === 'completed' && (
                <span className="ml-1 px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 text-xs rounded-full">
                  已完成
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('comments')}
              disabled={task.status !== 'completed'}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'comments'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              } ${task.status !== 'completed' ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <ChatBubbleLeftRightIcon className="w-4 h-4" />
              团队讨论
              {commentCount > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs rounded-full">
                  {commentCount}
                </span>
              )}
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Workflow Tab */}
          {activeTab === 'workflow' && (
            <div className="space-y-6">
              {/* Report Generation Indicator */}
              {isGenerating && (
                <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4 flex items-center gap-3">
                  <ArrowPathIcon className="w-5 h-5 text-primary-600 dark:text-primary-400 animate-spin" />
                  <div>
                    <p className="font-medium text-primary-700 dark:text-primary-300">报告生成中</p>
                    <p className="text-sm text-primary-600 dark:text-primary-400">
                      正在生成: {currentSection ? sectionLabels[currentSection] || currentSection : '...'}
                    </p>
                  </div>
                </div>
              )}
              
              {/* Agents Grid */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">代理执行状态</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {agents.map(agentName => {
                    const { startedAt, completedAt } = getAgentTimes(agentName);
                    const highlighted = isAgentHighlighted(agentName);
                    const highlight = getAgentHighlight(agentName);
                    
                    return (
                      <AgentCard
                        key={agentName}
                        name={agentName}
                        status={getAgentStatus(agentName) as 'pending' | 'running' | 'completed' | 'failed'}
                        startedAt={startedAt}
                        completedAt={completedAt}
                        steps={getAgentSteps(agentName)}
                        isHighlighted={highlighted}
                        highlightSection={highlight ? sectionLabels[highlight.section] || highlight.section : null}
                        onHighlightClick={highlighted ? () => setActiveTab('report') : undefined}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Real-time Messages from SSE */}
              {messages.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="p-4 border-b border-gray-100 dark:border-gray-700">
                    <h3 className="font-semibold text-gray-900 dark:text-white">实时消息流</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">SSE推送的代理通信记录</p>
                  </div>
                  <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[400px] overflow-y-auto">
                    {messages.map((msg, index) => (
                      <div key={msg.id || index} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <div className="flex items-center gap-2 text-sm mb-2">
                          <span className="font-medium text-purple-600 dark:text-purple-400">{msg.sender}</span>
                          <span className="text-gray-400">→</span>
                          <span className="font-medium text-blue-600 dark:text-blue-400">{msg.recipient || '广播'}</span>
                          <span className={`ml-auto px-2 py-0.5 rounded text-xs ${
                            msg.type === 'error' ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' :
                            msg.type === 'response' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
                            msg.type === 'request' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' :
                            'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                          }`}>
                            {msg.type}
                          </span>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
                          {'action' in msg.content && Boolean(msg.content.action) && (
                            <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">[{String(msg.content.action)}]</div>
                          )}
                          {'query' in msg.content && typeof msg.content.query === 'string' && Boolean(msg.content.query) && (
                            <div className="text-gray-600 dark:text-gray-400">{msg.content.query}</div>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          {formatDate(msg.timestamp)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Report Tab */}
          {activeTab === 'report' && (
            <div className="space-y-6">
              {reportLoading ? (
                <div className="flex items-center justify-center py-12">
                  <ArrowPathIcon className="w-8 h-8 text-primary-600 dark:text-primary-400 animate-spin" />
                  <span className="ml-3 text-gray-500 dark:text-gray-400">加载报告中...</span>
                </div>
              ) : reportError ? (
                <div className="text-center py-12">
                  <ExclamationTriangleIcon className="w-12 h-12 text-yellow-500 mx-auto" />
                  <p className="mt-4 text-gray-600 dark:text-gray-400">{reportError}</p>
                  <button
                    onClick={loadReport}
                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    重新加载
                  </button>
                </div>
              ) : report ? (
                <ReportViewer report={(report.content || report) as Parameters<typeof ReportViewer>[0]['report']} />
              ) : (
                <div className="text-center py-12">
                  <DocumentTextIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto" />
                  <p className="mt-4 text-gray-500 dark:text-gray-400">暂无报告</p>
                </div>
              )}
              
              {task.status === 'completed' && taskId && (
                <TaskDistributePanel
                  taskId={taskId}
                  taskTitle={task.query}
                  taskType={task.style}
                />
              )}
            </div>
          )}

          {/* Comments Tab */}
          {activeTab === 'comments' && (
            <div>
              {task.status === 'completed' && taskId ? (
                <CommentPanel 
                  reportId={taskId} 
                  currentUserId={task.user_id}
                />
              ) : (
                <div className="text-center py-12">
                  <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto" />
                  <p className="mt-4 text-gray-500 dark:text-gray-400">任务完成后才能讨论</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Failed State */}
      {task.status === 'failed' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">任务执行失败</h3>
          <p className="text-red-600 dark:text-red-400 text-sm mt-1">请检查任务参数或联系技术支持</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors"
          >
            创建新任务
          </button>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-4">
              <UserGroupIcon className="w-6 h-6 text-primary-600" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">分享到团队</h2>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              选择一个团队，成员将能够查看此分析报告
            </p>
            
            {teams.length === 0 ? (
              <div className="text-center py-8">
                <UserGroupIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto" />
                <p className="text-gray-500 dark:text-gray-400 mt-2">暂无团队</p>
                <Link
                  to="/teams"
                  className="mt-3 text-primary-600 hover:text-primary-700 text-sm"
                >
                  创建团队
                </Link>
              </div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {teams.map(team => {
                  const isShared = sharedTeams.includes(team.id);
                  return (
                    <button
                      key={team.id}
                      onClick={() => {
                        setSelectedTeamId(isShared ? null : team.id);
                      }}
                      disabled={isShared}
                      className={`w-full p-3 rounded-lg text-left transition-colors ${
                        isShared
                          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                          : selectedTeamId === team.id
                          ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                          : 'bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{team.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {team.member_count || 0} 成员
                          </p>
                        </div>
                        {isShared ? (
                          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                            <CheckCircleIcon className="w-4 h-4" />
                            已分享
                          </span>
                        ) : (
                          <input
                            type="radio"
                            checked={selectedTeamId === team.id}
                            onChange={() => {}}
                            className="w-4 h-4 text-primary-600"
                          />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={() => setShowShareModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                取消
              </button>
              <button
                onClick={handleShareTask}
                disabled={!selectedTeamId || isSharing}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {isSharing ? '分享中...' : '确认分享'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showMemoryModal && task && taskId && (
        <SaveMemoryModal
          isOpen={showMemoryModal}
          onClose={() => setShowMemoryModal(false)}
          taskId={taskId}
          taskTitle={task.query}
          teamId={currentTeam?.id}
        />
      )}
    </div>
  );
};

export default TaskDetailPage;
