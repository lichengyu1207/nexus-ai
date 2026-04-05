import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  Users,
  Building2,
  Coins,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import FluentCard from './FluentCard';
import AgentCard from './AgentCard';
import ProgressBar from './ProgressBar';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon, color }) => (
  <FluentCard goldAccent hover className="relative overflow-hidden">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500 mb-1">{title}</p>
        <p className="text-3xl font-bold text-fluent-deepOcean-500">{value}</p>
        {change !== undefined && (
          <div className={`flex items-center gap-1 mt-2 text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {change >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            <span>{Math.abs(change)}% 较昨日</span>
          </div>
        )}
      </div>
      <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
    </div>
    <div className={`absolute bottom-0 left-0 right-0 h-1 ${color.replace('bg-', 'bg-').replace('/20', '')}`} />
  </FluentCard>
);

const DashboardPage: React.FC = () => {
  const stats = [
    {
      title: '活跃智能体',
      value: 12,
      change: 8,
      icon: <Users className="w-6 h-6 text-fluent-gold-500" />,
      color: 'bg-fluent-gold-500/20',
    },
    {
      title: '今日任务',
      value: 47,
      change: 12,
      icon: <CheckCircle2 className="w-6 h-6 text-green-500" />,
      color: 'bg-green-500/20',
    },
    {
      title: '小区数据',
      value: '642',
      change: 5,
      icon: <Building2 className="w-6 h-6 text-blue-500" />,
      color: 'bg-blue-500/20',
    },
    {
      title: '积分余额',
      value: '12,580',
      change: -3,
      icon: <Coins className="w-6 h-6 text-fluent-gold-500" />,
      color: 'bg-fluent-gold-500/20',
    },
  ];

  const agents = [
    {
      id: '1',
      name: '周瑜·大都督',
      avatar: '/agents/zhouyu.png',
      level: 45,
      department: '战略规划部',
      status: 'working' as const,
      currentTask: '分析深圳南山区房价趋势',
      rarity: 'legendary' as const,
    },
    {
      id: '2',
      name: '陆逊·丞相',
      avatar: '/agents/luxun.png',
      level: 38,
      department: '数据分析部',
      status: 'busy' as const,
      currentTask: '生成小区SEO文章',
      rarity: 'epic' as const,
    },
    {
      id: '3',
      name: '诸葛亮·军师',
      avatar: '/agents/zhugeliang.png',
      level: 42,
      department: '智能咨询部',
      status: 'idle' as const,
      rarity: 'legendary' as const,
    },
    {
      id: '4',
      name: '司马懿·谋士',
      avatar: '/agents/sima.png',
      level: 35,
      department: '风险评估部',
      status: 'autonomous' as const,
      currentTask: '监控市场动态',
      rarity: 'epic' as const,
    },
  ];

  const recentTasks = [
    { id: 1, title: '深圳华润城房价分析', status: 'completed', time: '2小时前' },
    { id: 2, title: '广州珠江新城调研', status: 'in_progress', time: '进行中' },
    { id: 3, title: '上海浦东新区报告', status: 'pending', time: '待处理' },
    { id: 4, title: '北京朝阳区数据更新', status: 'completed', time: '5小时前' },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fluent-deepOcean-500">仪表盘</h1>
          <p className="text-gray-500 mt-1">欢迎回来，查看今日运营概况</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>最后更新: {new Date().toLocaleString('zh-CN')}</span>
        </div>
      </div>

      <motion.div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" variants={itemVariants}>
        {stats.map((stat, index) => (
          <motion.div key={index} variants={itemVariants}>
            <StatCard {...stat} />
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div className="lg:col-span-2" variants={itemVariants}>
          <FluentCard goldAccent>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-fluent-deepOcean-500">智能体状态</h2>
              <button className="text-sm text-fluent-gold-500 hover:text-fluent-gold-600">查看全部 →</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          </FluentCard>
        </motion.div>

        <motion.div variants={itemVariants}>
          <FluentCard>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-fluent-deepOcean-500">近期任务</h2>
              <span className="text-xs px-2 py-1 bg-fluent-gold-100 text-fluent-gold-600 rounded-full">
                4 项任务
              </span>
            </div>
            <div className="space-y-3">
              {recentTasks.map((task) => (
                <motion.div
                  key={task.id}
                  className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                  whileHover={{ x: 4 }}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      task.status === 'completed'
                        ? 'bg-green-100 text-green-500'
                        : task.status === 'in_progress'
                        ? 'bg-blue-100 text-blue-500'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {task.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : task.status === 'in_progress' ? (
                      <Clock className="w-4 h-4" />
                    ) : (
                      <AlertCircle className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">{task.title}</p>
                    <p className="text-xs text-gray-400">{task.time}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </FluentCard>
        </motion.div>
      </div>

      <motion.div variants={itemVariants}>
        <FluentCard goldAccent>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-fluent-deepOcean-500">今日任务进度</h2>
            <span className="text-sm text-fluent-gold-500 font-medium">47/60 完成</span>
          </div>
          <ProgressBar value={47} max={60} label="任务完成率" variant="gradient" size="lg" />
          <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-100">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-500">35</p>
              <p className="text-xs text-gray-500">已完成</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-500">8</p>
              <p className="text-xs text-gray-500">进行中</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-400">4</p>
              <p className="text-xs text-gray-500">待处理</p>
            </div>
          </div>
        </FluentCard>
      </motion.div>
    </motion.div>
  );
};

export default DashboardPage;
