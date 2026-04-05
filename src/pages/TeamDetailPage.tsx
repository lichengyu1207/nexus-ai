import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  UserGroupIcon,
  ClipboardDocumentIcon,
  CogIcon,
  TrashIcon,
  ArrowRightOnRectangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  UserPlusIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  DocumentTextIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { teamApi, Team, TeamMember, TeamTask } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import showToast from '@/utils/toast';
import Spinner, { LoadingCard } from '@/components/Loading';
import InviteMemberModal from '@/components/InviteMemberModal';

type TabType = 'overview' | 'tasks' | 'members' | 'settings';

interface TeamSettings {
  allow_member_invite: boolean;
  require_approval: boolean;
  default_role: string;
}

interface TeamStats {
  totalTasks: number;
  completedTasks: number;
  runningTasks: number;
  failedTasks: number;
  completionRate: number;
  avgCompletionTime: number;
  activeMembers: number;
  tasksThisWeek: number;
  tasksThisMonth: number;
}

interface MemberContribution {
  userId: string;
  userName: string;
  email: string;
  taskCount: number;
  completedCount: number;
}

interface TaskTrend {
  date: string;
  count: number;
  completed: number;
}

const TeamDetailPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [tasks, setTasks] = useState<TeamTask[]>([]);
  const [settings, setSettings] = useState<TeamSettings | null>(null);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [contributions, setContributions] = useState<MemberContribution[]>([]);
  const [trends, setTrends] = useState<TaskTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  
  const [showEditModal, setShowEditModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', description: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (teamId) {
      loadTeamData();
    }
  }, [teamId]);

  const loadTeamData = async () => {
    setIsLoading(true);
    try {
      const [teamData, membersData, tasksData] = await Promise.all([
        teamApi.get(teamId!),
        teamApi.getMembers(teamId!),
        teamApi.getTasks(teamId!, 100),
      ]);
      setTeam(teamData);
      setMembers(membersData);
      setTasks(tasksData);
      setEditForm({ name: teamData.name, description: teamData.description || '' });
      
      calculateStats(tasksData, membersData);
      
      try {
        const settingsResponse = await fetch(`/api/teams/${teamId}/settings`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        if (settingsResponse.ok) {
          setSettings(await settingsResponse.json());
        }
      } catch {}
    } catch (error) {
      showToast.error('加载团队信息失败');
      navigate('/teams');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = (taskList: TeamTask[], memberList: TeamMember[]) => {
    const totalTasks = taskList.length;
    const completedTasks = taskList.filter(t => t.status === 'completed').length;
    const runningTasks = taskList.filter(t => t.status === 'running').length;
    const failedTasks = taskList.filter(t => t.status === 'failed').length;
    const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    const tasksThisWeek = taskList.filter(t => t.created_at && new Date(t.created_at) > weekAgo).length;
    const tasksThisMonth = taskList.filter(t => t.created_at && new Date(t.created_at) > monthAgo).length;
    
    const weekAgoForMembers = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const activeMembers = memberList.filter(m => m.joined_at && new Date(m.joined_at) > weekAgoForMembers).length;
    
    setStats({
      totalTasks,
      completedTasks,
      runningTasks,
      failedTasks,
      completionRate,
      avgCompletionTime: 0,
      activeMembers,
      tasksThisWeek,
      tasksThisMonth,
    });
    
    const contributionMap = new Map<string, MemberContribution>();
    taskList.forEach(task => {
      const userId = task.user_id;
      if (!contributionMap.has(userId)) {
        contributionMap.set(userId, {
          userId,
          userName: task.owner_name || task.owner_email,
          email: task.owner_email,
          taskCount: 0,
          completedCount: 0,
        });
      }
      const contrib = contributionMap.get(userId)!;
      contrib.taskCount++;
      if (task.status === 'completed') {
        contrib.completedCount++;
      }
    });
    setContributions(Array.from(contributionMap.values()).sort((a, b) => b.taskCount - a.taskCount));
    
    const trendMap = new Map<string, TaskTrend>();
    taskList.forEach(task => {
      if (task.created_at) {
        const date = new Date(task.created_at).toISOString().split('T')[0];
        if (!trendMap.has(date)) {
          trendMap.set(date, { date, count: 0, completed: 0 });
        }
        const trend = trendMap.get(date)!;
        trend.count++;
        if (task.status === 'completed') {
          trend.completed++;
        }
      }
    });
    setTrends(Array.from(trendMap.values()).sort((a, b) => a.date.localeCompare(b.date)).slice(-14));
  };

  const handleCopyInviteCode = () => {
    if (team) {
      navigator.clipboard.writeText(team.invite_code);
      showToast.success('邀请码已复制');
    }
  };

  const handleUpdateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editForm.name.trim()) {
      showToast.error('请输入团队名称');
      return;
    }

    setIsSubmitting(true);
    try {
      const updated = await teamApi.update(teamId!, {
        name: editForm.name,
        description: editForm.description || undefined,
      });
      setTeam(updated);
      setShowEditModal(false);
      showToast.success('团队信息已更新');
    } catch (error) {
      showToast.error('更新失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTeam = async () => {
    if (!confirm('确定要删除团队吗？此操作不可撤销。')) return;
    
    try {
      await teamApi.delete(teamId!);
      showToast.success('团队已删除');
      navigate('/teams');
    } catch (error) {
      showToast.error('删除失败');
    }
  };

  const handleLeaveTeam = async () => {
    if (!confirm('确定要离开团队吗？')) return;
    
    try {
      await teamApi.leave(teamId!, user!.id);
      showToast.success('已离开团队');
      navigate('/teams');
    } catch (error) {
      showToast.error('操作失败');
    }
  };

  const handleRemoveMember = async (userId: string, memberName: string) => {
    if (!confirm(`确定要移除成员 ${memberName} 吗？`)) return;
    
    try {
      await teamApi.leave(teamId!, userId);
      setMembers(members.filter(m => m.user_id !== userId));
      showToast.success('成员已移除');
    } catch (error) {
      showToast.error('移除失败');
    }
  };

  const handleUpdateRole = async (userId: string, newRole: string, memberName: string) => {
    if (!confirm(`确定要将 ${memberName} 的角色更改为 ${newRole === 'admin' ? '管理员' : '成员'} 吗？`)) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`/api/teams/${teamId}/members/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ role: newRole }),
      });
      
      setMembers(members.map(m => 
        m.user_id === userId ? { ...m, role: newRole } : m
      ));
      showToast.success('角色已更新');
    } catch {
      showToast.error('更新角色失败');
    }
  };

  const handleUpdateSettings = async (newSettings: Partial<TeamSettings>) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/teams/${teamId}/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newSettings),
      });
      
      if (response.ok) {
        const updated = await response.json();
        setSettings(updated);
        showToast.success('设置已更新');
      }
    } catch {
      showToast.error('更新设置失败');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      case 'running':
        return <ClockIcon className="w-5 h-5 text-blue-500 animate-pulse" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingCard message="加载团队信息..." />;
  }

  if (!team) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">团队不存在</p>
        <Link to="/teams" className="text-primary-600 dark:text-primary-400 hover:underline mt-2 inline-block">
          返回团队列表
        </Link>
      </div>
    );
  }

  const isOwner = team.owner_id === user?.id;
  const currentUserMember = members.find(m => m.user_id === user?.id);
  const isAdmin = isOwner || currentUserMember?.role === 'admin';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/teams" className="text-primary-600 dark:text-primary-400 hover:text-primary-700 text-sm flex items-center gap-1">
            <ArrowLeftIcon className="w-4 h-4" />
            返回团队列表
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{team.name}</h1>
          {team.description && (
            <p className="text-gray-600 dark:text-gray-400 mt-1">{team.description}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isAdmin && (
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <UserPlusIcon className="w-5 h-5" />
              邀请成员
            </button>
          )}
          <button
            onClick={handleCopyInviteCode}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ClipboardDocumentIcon className="w-5 h-5" />
            邀请码: <span className="font-mono font-medium">{team.invite_code}</span>
          </button>
          {isOwner && (
            <button
              onClick={() => setShowEditModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <CogIcon className="w-5 h-5" />
              设置
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="border-b border-gray-100 dark:border-gray-700">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              数据看板
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'tasks'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              共享任务 ({tasks.length})
            </button>
            <button
              onClick={() => setActiveTab('members')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'members'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              成员 ({members.length})
            </button>
            {isAdmin && (
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'settings'
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                设置
              </button>
            )}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500 rounded-lg">
                      <DocumentTextIcon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.totalTasks || 0}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">总任务数</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-500 rounded-lg">
                      <CheckCircleIcon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.completedTasks || 0}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">已完成</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500 rounded-lg">
                      <ArrowTrendingUpIcon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.completionRate || 0}%</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">完成率</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-500 rounded-lg">
                      <UserGroupIcon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{members.length}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">团队成员</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Activity Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CalendarIcon className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">本周活动</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats?.tasksThisWeek || 0}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">新增任务</p>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CalendarIcon className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">本月活动</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats?.tasksThisMonth || 0}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">新增任务</p>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <ClockIcon className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">进行中</span>
                  </div>
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats?.runningTasks || 0}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">正在分析</p>
                </div>
              </div>

              {/* Member Contributions */}
              {contributions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">成员贡献</h3>
                  <div className="space-y-3">
                    {contributions.slice(0, 5).map((contrib, index) => (
                      <div
                        key={contrib.userId}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                            index === 0 ? 'bg-yellow-500' :
                            index === 1 ? 'bg-gray-400' :
                            index === 2 ? 'bg-orange-500' :
                            'bg-gray-300 dark:bg-gray-600'
                          }`}>
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">{contrib.userName}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{contrib.email}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-gray-900 dark:text-white">{contrib.taskCount} 个任务</p>
                          <p className="text-xs text-green-600 dark:text-green-400">{contrib.completedCount} 已完成</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Tasks */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">最近任务</h3>
                  <button
                    onClick={() => setActiveTab('tasks')}
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    查看全部
                  </button>
                </div>
                {tasks.length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-gray-500 dark:text-gray-400">暂无共享任务</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">在任务详情页可以将任务分享到团队</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {tasks.slice(0, 5).map((task) => (
                      <Link
                        key={task.id}
                        to={`/tasks/${task.id}`}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {getStatusIcon(task.status)}
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white line-clamp-1">{task.query}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {task.owner_name || task.owner_email}
                            </p>
                          </div>
                        </div>
                        <span className="text-xs text-gray-400 dark:text-gray-500">{formatDate(task.created_at)}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tasks Tab */}
          {activeTab === 'tasks' && (
            <div>
              {tasks.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 dark:text-gray-400">暂无共享任务</p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">在任务详情页可以将任务分享到团队</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <Link
                      key={task.id}
                      to={`/tasks/${task.id}`}
                      className="block p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(task.status)}
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white line-clamp-1">{task.query}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {task.owner_name || task.owner_email} · {formatDate(task.created_at)}
                            </p>
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          task.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                          task.status === 'running' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' :
                          task.status === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                          'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}>
                          {task.status === 'completed' ? '已完成' :
                           task.status === 'running' ? '进行中' :
                           task.status === 'failed' ? '失败' : '等待中'}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Members Tab */}
          {activeTab === 'members' && (
            <div className="space-y-3">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                      <UserGroupIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {member.full_name || member.email}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      member.role === 'owner' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' :
                      member.role === 'admin' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' :
                      'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}>
                      {member.role === 'owner' ? '所有者' : member.role === 'admin' ? '管理员' : '成员'}
                    </span>
                    {isAdmin && member.role !== 'owner' && (
                      <div className="flex items-center gap-1">
                        <select
                          value={member.role}
                          onChange={(e) => handleUpdateRole(member.user_id, e.target.value, member.full_name || member.email)}
                          className="text-xs px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                        >
                          <option value="admin">管理员</option>
                          <option value="member">成员</option>
                        </select>
                        <button
                          onClick={() => handleRemoveMember(member.user_id, member.full_name || member.email)}
                          className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && isAdmin && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">团队信息</h3>
                <form onSubmit={handleUpdateTeam} className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      团队名称
                    </label>
                    <input
                      type="text"
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      团队描述
                    </label>
                    <textarea
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isSubmitting ? <Spinner size="sm" /> : '保存更改'}
                  </button>
                </form>
              </div>

              <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">权限设置</h3>
                <div className="space-y-4 max-w-md">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings?.allow_member_invite ?? true}
                      onChange={(e) => handleUpdateSettings({ allow_member_invite: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-primary-600"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">允许成员邀请</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">普通成员可以生成邀请链接</p>
                    </div>
                  </label>
                  
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings?.require_approval ?? false}
                      onChange={(e) => handleUpdateSettings({ require_approval: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-primary-600"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">需要审批</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">新成员需要管理员审批才能加入</p>
                    </div>
                  </label>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                      新成员默认角色
                    </label>
                    <select
                      value={settings?.default_role || 'member'}
                      onChange={(e) => handleUpdateSettings({ default_role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="member">成员</option>
                      <option value="admin">管理员</option>
                    </select>
                  </div>
                </div>
              </div>

              {isOwner && (
                <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-4">危险操作</h3>
                  <button
                    onClick={handleDeleteTeam}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    删除团队
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Leave Team Button (for non-owners) */}
      {!isOwner && activeTab !== 'settings' && (
        <div className="flex justify-end">
          <button
            onClick={handleLeaveTeam}
            className="flex items-center gap-2 px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5" />
            离开团队
          </button>
        </div>
      )}

      {/* Invite Modal */}
      <InviteMemberModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        teamId={teamId!}
        teamName={team.name}
      />

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">编辑团队</h2>
            <form onSubmit={handleUpdateTeam} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  团队名称
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  团队描述
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {isSubmitting ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamDetailPage;
