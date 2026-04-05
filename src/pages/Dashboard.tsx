import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import LevelCard from '@/components/LevelCard';
import { taskApi } from '@/services/api';
import { slideIn } from '@/config/animation';

interface Task {
  id: string;
  query: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  progress: number;
  owner_name: string;
  created_at: string;
}

interface DashboardStats {
  totalTasks: number;
  completedTasks: number;
  runningTasks: number;
  failedTasks: number;
  completionRate: number;
  activeAgents: number;
  teamCount: number;
}

interface AISummary {
  greeting: string;
  insights: string[];
  recommendations: string[];
}

/**
 * 极简主义仪表盘页面
 */
const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // 模拟数据，实际应从API获取
      const mockStats: DashboardStats = {
        totalTasks: 12,
        completedTasks: 8,
        runningTasks: 3,
        failedTasks: 1,
        completionRate: 67,
        activeAgents: 5,
        teamCount: 2,
      };

      const mockTasks: Task[] = [
        {
          id: '1',
          query: '深圳福田区房价分析',
          status: 'completed',
          progress: 100,
          owner_name: '张三',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          query: '上海浦东新区投资价值评估',
          status: 'running',
          progress: 65,
          owner_name: '李四',
          created_at: new Date().toISOString(),
        },
        {
          id: '3',
          query: '北京朝阳区学区房调研',
          status: 'running',
          progress: 30,
          owner_name: '王五',
          created_at: new Date().toISOString(),
        },
      ];

      const mockAISummary: AISummary = {
        greeting: '下午好，张管理员。你的团队本周完成 8 个任务，超越 85% 的团队。',
        insights: [
          '兵部智能体负载较高，建议分配部分任务到户部。',
          '团队任务完成率较上周提升 15%。',
          '智能咨询模块响应速度提升 20%。',
        ],
        recommendations: [
          '考虑招募更多户部智能体以平衡负载。',
          '查看任务中心的待处理任务。',
          '检查团队管理中的成员活跃度。',
        ],
      };

      setStats(mockStats);
      setRecentTasks(mockTasks);
      setAiSummary(mockAISummary);
    } catch (error) {
      console.error('加载仪表盘数据失败:', error);
    } finally {
      setIsLoading(false);
    }
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
      {/* 英雄区：AI 摘要 */}
      {aiSummary && (
        <Card>
          <div className="flex items-start gap-4">
            <div className="text-2xl">🤖</div>
            <div className="flex-1">
              <h2 className="text-lg font-medium text-text-primary">{aiSummary.greeting}</h2>
              <div className="mt-2 space-y-2">
                {aiSummary.insights.map((insight, index) => (
                  <p key={index} className="text-sm text-text-secondary">• {insight}</p>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                {aiSummary.recommendations.map((recommendation, index) => (
                  <Button key={index} variant="ghost" size="sm">
                    {recommendation}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">总任务数</p>
                <p className="text-2xl font-bold text-text-primary mt-1">{stats.totalTasks}</p>
              </div>
              <div className="text-2xl">📋</div>
            </div>
            <ProgressBar 
              value={stats.completionRate} 
              status="success"
              className="mt-3"
            />
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">已完成</p>
                <p className="text-2xl font-bold text-status-success mt-1">{stats.completedTasks}</p>
              </div>
              <div className="text-2xl">✅</div>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              完成率: {stats.completionRate}%
            </p>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">进行中</p>
                <p className="text-2xl font-bold text-status-info mt-1">{stats.runningTasks}</p>
              </div>
              <div className="text-2xl">🔄</div>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              活跃智能体: {stats.activeAgents}
            </p>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">团队数</p>
                <p className="text-2xl font-bold text-accent-gold mt-1">{stats.teamCount}</p>
              </div>
              <div className="text-2xl">👥</div>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              团队协作中
            </p>
          </Card>
        </div>
      )}

      {/* 用户等级卡片 */}
      <LevelCard completedTasks={stats?.completedTasks || 0} />

      {/* 最近任务 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-text-primary">最近任务</h2>
          <Button variant="ghost" size="sm">查看全部</Button>
        </div>
        {recentTasks.length === 0 ? (
          <EmptyState
            title="暂无任务"
            description="开始创建你的第一个任务"
            action="创建任务"
            onAction={() => console.log('创建任务')}
          />
        ) : (
          <div className="space-y-2">
            {recentTasks.map((task) => (
              <Card key={task.id} hoverable>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text-primary">{task.query}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${task.status === 'completed' ? 'bg-status-success/20 text-status-success' : task.status === 'running' ? 'bg-status-info/20 text-status-info' : 'bg-status-error/20 text-status-error'}`}>
                        {task.status === 'completed' ? '已完成' : task.status === 'running' ? '进行中' : '失败'}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary mt-1">
                      {task.owner_name} · {new Date(task.created_at).toLocaleString('zh-CN')}
                    </p>
                    {task.status === 'completed' && (
                      <div className="mt-2 flex gap-2">
                        <Button variant="ghost" size="sm" className="text-xs">
                          查看结果
                        </Button>
                        <Button variant="ghost" size="sm" className="text-xs">
                          导出报告
                        </Button>
                      </div>
                    )}
                  </div>
                  <ProgressBar 
                    value={task.progress} 
                    status={task.status === 'completed' ? 'success' : task.status === 'running' ? 'processing' : 'error'}
                    className="w-24 ml-4"
                  />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Dashboard;
