import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { teamApi, Team } from '@/services/api';
import { useAppContextStore } from '@/store/appContextStore';
import showToast from '@/utils/toast';
import { slideIn } from '@/config/animation';

interface TeamStats {
  totalTasks: number;
  completedTasks: number;
  totalMembers: number;
  recentActivity: number;
}

/**
 * 极简主义团队管理页面
 */
const TeamManagement: React.FC = () => {
  const { setCurrentTeam } = useAppContextStore();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamStats, setTeamStats] = useState<Record<string, TeamStats>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
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
      loadTeams();
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

  const handleTeamClick = (team: Team) => {
    setCurrentTeam({
      id: team.id,
      name: team.name,
      skills: [],
      memberCount: teamStats[team.id]?.totalMembers || 0,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">加载中...</div>
      </div>
    );
  }

  return (
    <motion.div {...slideIn} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">团队管理</h1>
          <p className="text-text-secondary mt-1">管理和协作你的团队</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowJoinModal(true)}>
            加入团队
          </Button>
          <Button variant="primary" onClick={() => setShowCreateModal(true)}>
            创建团队
          </Button>
        </div>
      </div>

      {teams.length === 0 ? (
        <EmptyState
          title="暂无团队"
          description="创建一个团队开始协作吧"
          action="创建团队"
          onAction={() => setShowCreateModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 team-card-grid">
          {teams.map((team) => {
            const stats = teamStats[team.id] || { totalTasks: 0, completedTasks: 0, totalMembers: 0, recentActivity: 0 };
            const pendingBids = Math.floor(Math.random() * 3);
            const runningTasks = stats.totalTasks - stats.completedTasks;
            
            return (
              <motion.div
                key={team.id}
                whileHover={{ scale: 1.02 }}
                transition={{ duration: 0.1 }}
              >
                <Card hoverable>
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-text-primary">{team.name}</h3>
                      <p className="text-xs text-text-secondary mt-0.5">
                        所有者：{team.owner_id}
                      </p>
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(team.invite_code)}
                      className="text-text-secondary hover:text-text-primary transition-colors"
                      title="复制邀请码"
                    >
                      📋
                    </button>
                  </div>
                  
                  <div className="flex gap-4 mt-3 text-sm">
                    <div className="flex items-center gap-1 text-text-secondary">
                      📋 <span>{runningTasks}</span>
                    </div>
                    <div className="flex items-center gap-1 text-text-secondary">
                      👥 <span>{stats.totalMembers}</span>
                    </div>
                    <div className="flex items-center gap-1 text-text-secondary">
                      🔔 <span>{pendingBids}</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-3">
                    <Button variant="ghost" size="sm">招募</Button>
                    <Button variant="ghost" size="sm">邀请</Button>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 创建团队模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-medium mb-4">创建团队</h2>
            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-sm text-text-secondary mb-1">
                  团队名称 *
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="例如：深圳房产投资小组"
                  className="w-full bg-transparent border-b border-border-light px-0 py-1 text-text-primary focus:border-accent-gold"
                />
              </div>
              <div>
                <label className="block text-sm text-text-secondary mb-1">
                  团队描述
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="描述团队的用途"
                  rows={3}
                  className="w-full bg-transparent border-b border-border-light px-0 py-1 text-text-primary focus:border-accent-gold"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  取消
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? '创建中...' : '创建'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 加入团队模态框 */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-medium mb-4">加入团队</h2>
            <form onSubmit={handleJoinTeam} className="space-y-4">
              <div>
                <label className="block text-sm text-text-secondary mb-1">
                  邀请码
                </label>
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="输入8位邀请码"
                  maxLength={8}
                  className="w-full bg-transparent border-b border-border-light px-0 py-1 text-text-primary focus:border-accent-gold text-center text-lg font-mono"
                />
                <p className="text-xs text-text-secondary mt-1">
                  向团队所有者获取邀请码
                </p>
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowJoinModal(false)}>
                  取消
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting || joinCode.length !== 8}>
                  {isSubmitting ? '加入中...' : '加入'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default TeamManagement;
