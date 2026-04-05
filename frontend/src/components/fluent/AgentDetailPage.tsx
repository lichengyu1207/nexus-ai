import React from 'react';
import { motion } from 'framer-motion';
import {
  Star,
  Zap,
  Shield,
  Brain,
  Target,
  Clock,
  CheckCircle2,
  TrendingUp,
  Award,
  BookOpen,
} from 'lucide-react';
import FluentCard from './FluentCard';
import ProgressBar from './ProgressBar';
import FluentButton from './FluentButton';

interface AgentDetailPageProps {
  agent: {
    id: string;
    name: string;
    avatar?: string;
    level: number;
    experience: number;
    maxExperience: number;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
    department: string;
    title: string;
    description: string;
    attributes: {
      intelligence: number;
      efficiency: number;
      creativity: number;
      reliability: number;
    };
    skills: Array<{
      id: string;
      name: string;
      description: string;
      icon: string;
      level: number;
      cooldown?: string;
    }>;
    workLog: Array<{
      id: string;
      action: string;
      timestamp: string;
      status: 'success' | 'pending' | 'failed';
      details?: string;
    }>;
    stats: {
      tasksCompleted: number;
      successRate: number;
      avgResponseTime: string;
    };
  };
  onRecruit?: () => void;
  onEdit?: () => void;
}

const rarityConfig = {
  common: { color: 'from-gray-400 to-gray-600', glow: 'shadow-gray-400/30', label: '普通', stars: 1 },
  rare: { color: 'from-blue-400 to-blue-600', glow: 'shadow-blue-400/30', label: '稀有', stars: 2 },
  epic: { color: 'from-purple-400 to-purple-600', glow: 'shadow-purple-400/30', label: '史诗', stars: 3 },
  legendary: { color: 'from-fluent-gold-400 to-fluent-gold-600', glow: 'shadow-fluent-gold-400/30', label: '传说', stars: 4 },
};

const attributeIcons: Record<string, React.ReactNode> = {
  intelligence: <Brain className="w-5 h-5" />,
  efficiency: <Zap className="w-5 h-5" />,
  creativity: <Star className="w-5 h-5" />,
  reliability: <Shield className="w-5 h-5" />,
};

const attributeLabels: Record<string, string> = {
  intelligence: '智力',
  efficiency: '效率',
  creativity: '创造力',
  reliability: '可靠性',
};

const AgentDetailPage: React.FC<AgentDetailPageProps> = ({ agent, onRecruit, onEdit }) => {
  const rarity = rarityConfig[agent.rarity] || rarityConfig.common;

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
      <motion.div variants={itemVariants}>
        <FluentCard goldAccent className="relative overflow-hidden">
          <div className={`absolute inset-0 bg-gradient-to-br ${rarity.color} opacity-5`} />
          <div className="relative flex flex-col md:flex-row gap-6">
            <div className="flex-shrink-0">
              <motion.div
                className="relative"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', damping: 15 }}
              >
                <div className={`absolute inset-0 rounded-2xl ${rarity.glow} blur-xl`} />
                <img
                  src={agent.avatar || '/default-avatar.png'}
                  alt={agent.name}
                  className="w-32 h-32 md:w-40 md:h-40 rounded-2xl object-cover border-4 border-white shadow-lg relative z-10"
                />
                <motion.div
                  className={`absolute -inset-2 rounded-2xl border-2 bg-gradient-to-br ${rarity.color} opacity-20`}
                  animate={{ scale: [1, 1.05, 1], opacity: [0.2, 0.3, 0.2] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </motion.div>
              <div className="flex justify-center mt-3 gap-0.5">
                {[...Array(rarity.stars)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 text-fluent-gold-500 fill-fluent-gold-500" />
                ))}
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-fluent-deepOcean-500">{agent.name}</h1>
                  <p className="text-fluent-gold-500 font-medium">{agent.title}</p>
                  <p className="text-sm text-gray-500 mt-1">{agent.department}</p>
                </div>
                <div className="flex gap-2">
                  <FluentButton variant="outline" size="sm" onClick={onEdit}>
                    编辑
                  </FluentButton>
                  <FluentButton variant="gold" size="sm" onClick={onRecruit}>
                    招募
                  </FluentButton>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">等级 {agent.level}</span>
                  <span className="text-fluent-gold-500">
                    {agent.experience}/{agent.maxExperience} EXP
                  </span>
                </div>
                <ProgressBar
                  value={agent.experience}
                  max={agent.maxExperience}
                  showPercentage={false}
                  size="sm"
                  variant="gradient"
                />
              </div>

              <p className="mt-4 text-gray-600 text-sm leading-relaxed">{agent.description}</p>

              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-100">
                <div className="text-center">
                  <p className="text-2xl font-bold text-fluent-gold-500">{agent.stats.tasksCompleted}</p>
                  <p className="text-xs text-gray-500">完成任务</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-500">{agent.stats.successRate}%</p>
                  <p className="text-xs text-gray-500">成功率</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-500">{agent.stats.avgResponseTime}</p>
                  <p className="text-xs text-gray-500">平均响应</p>
                </div>
              </div>
            </div>
          </div>
        </FluentCard>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={itemVariants}>
          <FluentCard>
            <h2 className="text-lg font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-fluent-gold-500" />
              属性面板
            </h2>
            <div className="space-y-4">
              {Object.entries(agent.attributes).map(([key, value]) => (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      {attributeIcons[key]}
                      <span>{attributeLabels[key]}</span>
                    </div>
                    <span className="text-sm font-medium text-fluent-gold-500">{value}/100</span>
                  </div>
                  <ProgressBar value={value} max={100} showPercentage={false} size="sm" variant="gold" />
                </div>
              ))}
            </div>
          </FluentCard>
        </motion.div>

        <motion.div variants={itemVariants}>
          <FluentCard>
            <h2 className="text-lg font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-fluent-gold-500" />
              技能卡片
            </h2>
            <div className="space-y-3">
              {agent.skills.map((skill) => (
                <motion.div
                  key={skill.id}
                  className="p-3 rounded-xl bg-gradient-to-r from-fluent-deepOcean-50 to-white border border-gray-100 hover:border-fluent-gold-300 transition-colors cursor-pointer"
                  whileHover={{ x: 4 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-fluent-gold-100 flex items-center justify-center text-xl">
                      {skill.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-fluent-deepOcean-500">{skill.name}</h3>
                        <span className="text-xs px-2 py-0.5 bg-fluent-gold-100 text-fluent-gold-600 rounded-full">
                          Lv.{skill.level}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{skill.description}</p>
                      {skill.cooldown && (
                        <p className="text-xs text-blue-500 mt-1">冷却: {skill.cooldown}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </FluentCard>
        </motion.div>
      </div>

      <motion.div variants={itemVariants}>
        <FluentCard goldAccent>
          <h2 className="text-lg font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-fluent-gold-500" />
            工作日志
          </h2>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-4">
              {agent.workLog.map((log, index) => (
                <motion.div
                  key={log.id}
                  className="relative pl-10"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div
                    className={`absolute left-2.5 w-3 h-3 rounded-full ${
                      log.status === 'success'
                        ? 'bg-green-500'
                        : log.status === 'pending'
                        ? 'bg-blue-500'
                        : 'bg-red-500'
                    } ring-4 ring-white`}
                  />
                  <div className="p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-fluent-deepOcean-500">{log.action}</p>
                      <span className="text-xs text-gray-400">{log.timestamp}</span>
                    </div>
                    {log.details && (
                      <p className="text-sm text-gray-500 mt-1">{log.details}</p>
                    )}
                    <div className="flex items-center gap-1 mt-2">
                      {log.status === 'success' && (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      )}
                      {log.status === 'pending' && (
                        <Clock className="w-4 h-4 text-blue-500" />
                      )}
                      {log.status === 'failed' && (
                        <span className="w-4 h-4 text-red-500">✕</span>
                      )}
                      <span
                        className={`text-xs ${
                          log.status === 'success'
                            ? 'text-green-500'
                            : log.status === 'pending'
                            ? 'text-blue-500'
                            : 'text-red-500'
                        }`}
                      >
                        {log.status === 'success' ? '完成' : log.status === 'pending' ? '进行中' : '失败'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </FluentCard>
      </motion.div>
    </motion.div>
  );
};

export default AgentDetailPage;
