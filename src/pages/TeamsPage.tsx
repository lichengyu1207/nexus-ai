import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UserGroupIcon,
  PlusIcon,
  ClipboardDocumentIcon,
  ArrowRightOnRectangleIcon,
  CogIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ShareIcon,
  MegaphoneIcon,
  UserPlusIcon,
} from '@heroicons/react/24/outline';
import { teamApi, Team } from '@/services/api';
import { useAppContextStore } from '@/store/appContextStore';
import RecruitmentModal from '@/components/RecruitmentModal';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

interface TeamStats {
  totalTasks: number;
  completedTasks: number;
  totalMembers: number;
  recentActivity: number;
}

const TeamsPage: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentTeam } = useAppContextStore();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamStats, setTeamStats] = useState<Record<string, TeamStats>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [showRecruitmentModal, setShowRecruitmentModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [createForm, setCreateForm] = useState({ name: '', description: '' });
  const [joinCode, setJoinCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setIsLoading(true);
    try {
      const data = await teamApi.list();
      setTeams(data);
      
      const statsPromises = data.map(async (team) => {
        try {
          const [members, tasks] = await Promise.all([
            teamApi.getMembers(team.id),
            teamApi.getTasks(team.id),
          ]);
          
          return {
            teamId: team.id,
            stats: {
              totalTasks: tasks.length,
              completedTasks: tasks.filter(t => t.status === 'completed').length,
              totalMembers: members.length,
              recentActivity: tasks.filter(t => {
                const created = new Date(t.created_at || '');
                const weekAgo = new Date();
                weekAgo.setDate(weekAgo.getDate() - 7);
                return created > weekAgo;
              }).length,
            }
          };
        } catch {
          return {
            teamId: team.id,
            stats: { totalTasks: 0, completedTasks: 0, totalMembers: 0, recentActivity: 0 }
          };
        }
      });
      
      const statsResults = await Promise.all(statsPromises);
      const statsMap: Record<string, TeamStats> = {};
      statsResults.forEach(item => {
        statsMap[item.teamId] = item.stats;
      });
      setTeamStats(statsMap);
    } catch (error) {
      showToast.error('加载团队列表失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim()) {
      showToast.error('请输入团队名称');
      return;
    }

    setIsSubmitting(true);
    try {
      const team = await teamApi.create({
        name: createForm.name,
        description: createForm.description || undefined,
      });
      showToast.success('团队创建成功');
      setShowCreateModal(false);
      setCreateForm({ name: '', description: '' });
      navigate(`/teams/${team.id}`);
    } catch (error) {
      showToast.error('创建团队失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJoinTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!joinCode.trim()) {
      showToast.error('请输入邀请码');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await teamApi.join(joinCode.trim().toUpperCase());
      showToast.success(`已成功加入团队: ${result.team_name}`);
      setShowJoinModal(false);
      setJoinCode('');
      loadTeams();
    } catch (error) {
      showToast.error('加入团队失败，请检查邀请码');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenRecruitment = (e: React.MouseEvent, team: Team) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedTeam(team);
    setCurrentTeam({
      id: team.id,
      name: team.name,
      skills: [],
      memberCount: teamStats[team.id]?.totalMembers || 0,
    });
    setShowRecruitmentModal(true);
  };

  const handleTeamClick = (team: Team) => {
    setCurrentTeam({
      id: team.id,
      name: team.name,
      skills: [],
      memberCount: teamStats[team.id]?.totalMembers || 0,
    });
  };

  if (isLoading) {
    return <LoadingCard message="加载团队列表..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">团队协作</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">与团队成员共享分析任务、协作决策</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowJoinModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5" />
            加入团队
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <PlusIcon className="w-5 h-5" />
            创建团队
          </button>
        </div>
      </div>

      <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <UserGroupIcon className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">团队协作能做什么？</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="flex items-start gap-2">
                <ShareIcon className="w-5 h-5 text-primary-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">共享分析任务</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">将房产分析报告分享给团队成员</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <DocumentTextIcon className="w-5 h-5 text-primary-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">协作决策</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">团队成员可查看、评论分析结果</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ArrowTrendingUpIcon className="w-5 h-5 text-primary-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">数据汇总</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">团队分析数据自动汇总统计</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {teams.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-12 text-center">
          <UserGroupIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无团队</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">创建一个团队开始协作吧</p>
          <div className="flex justify-center gap-3 mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              创建团队
            </button>
            <button
              onClick={() => setShowJoinModal(true)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              加入团队
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((team) => {
            const stats = teamStats[team.id] || { totalTasks: 0, completedTasks: 0, totalMembers: 0, recentActivity: 0 };
            const pendingBids = Math.floor(Math.random() * 3);
            const runningTasks = stats.totalTasks - stats.completedTasks;
            
            return (
              <div
                key={team.id}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 hover:shadow-lg transition-all"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 to-primary-800/50 rounded-xl flex items-center justify-center">
                        <span className="text-primary-600 dark:text-primary-400 font-bold text-lg">
                          {team.name.charAt(0)}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                            {team.name}
                          </h3>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            team.user_role === 'owner' 
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' 
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                          }`}>
                            {team.user_role === 'owner' ? '所有者' : '成员'}
                          </span>
                        </div>
                        {team.description && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">
                            {team.description}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigator.clipboard.writeText(team.invite_code);
                          showToast.success('邀请码已复制');
                        }}
                        className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                        title="复制邀请码"
                      >
                        <ClipboardDocumentIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-2 mb-4 px-5">
                    <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.totalMembers}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">成员</p>
                    </div>
                    <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{runningTasks}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">进行中</p>
                    </div>
                    <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <p className="text-lg font-bold text-green-600 dark:text-green-400">{stats.completedTasks}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">已完成</p>
                    </div>
                    <div className="text-center p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg relative">
                      <p className="text-lg font-bold text-amber-600 dark:text-amber-400">{pendingBids}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">待处理</p>
                      {pendingBids > 0 && (
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 px-5 pb-4 border-t border-gray-100 dark:border-gray-700">
                    <button
                      onClick={(e) => handleOpenRecruitment(e, team)}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      <MegaphoneIcon className="w-4 h-4" />
                      发布招募
                    </button>
                    <Link
                      to={`/teams/${team.id}`}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <UserGroupIcon className="w-4 h-4" />
                      查看详情
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">创建团队</h2>
            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  团队名称 *
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="例如：深圳房产投资小组"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  团队描述
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="描述团队的用途，例如：专注于深圳学区房投资分析"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {isSubmitting ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showJoinModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">加入团队</h2>
            <form onSubmit={handleJoinTeam} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  邀请码
                </label>
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="输入8位邀请码"
                  maxLength={8}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 font-mono text-center text-lg tracking-wider"
                />
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  向团队所有者获取邀请码
                </p>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowJoinModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || joinCode.length !== 8}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {isSubmitting ? '加入中...' : '加入'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showRecruitmentModal && selectedTeam && (
        <RecruitmentModal
          isOpen={showRecruitmentModal}
          onClose={() => {
            setShowRecruitmentModal(false);
            setSelectedTeam(null);
          }}
          teamId={selectedTeam.id}
          teamName={selectedTeam.name}
        />
      )}
    </div>
  );
};

export default TeamsPage;
