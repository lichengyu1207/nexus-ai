import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Sparkles,
  Coins,
  Users,
  TrendingUp,
  Brain,
  Building2,
  Shield,
} from 'lucide-react';
import FluentCard from './FluentCard';
import AgentCard from './AgentCard';
import FluentButton from './FluentButton';
import GachaAnimation from './GachaAnimation';

interface MarketAgent {
  id: string;
  name: string;
  avatar?: string;
  level: number;
  department: string;
  status: 'idle' | 'busy' | 'working' | 'autonomous';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  cost: number;
  skills: string[];
}

const rarityFilters = [
  { id: 'all', label: '全部', color: 'bg-gray-100 text-gray-600' },
  { id: 'common', label: '普通', color: 'bg-gray-200 text-gray-700' },
  { id: 'rare', label: '稀有', color: 'bg-blue-100 text-blue-600' },
  { id: 'epic', label: '史诗', color: 'bg-purple-100 text-purple-600' },
  { id: 'legendary', label: '传说', color: 'bg-fluent-gold-100 text-fluent-gold-600' },
];

const departmentFilters = [
  { id: 'all', label: '全部部门', icon: Users },
  { id: 'strategy', label: '战略规划', icon: TrendingUp },
  { id: 'analysis', label: '数据分析', icon: Brain },
  { id: 'consultation', label: '智能咨询', icon: Building2 },
  { id: 'risk', label: '风险评估', icon: Shield },
];

const sampleAgents: MarketAgent[] = [
  {
    id: '1',
    name: '周瑜·大都督',
    avatar: '/agents/zhouyu.png',
    level: 45,
    department: '战略规划部',
    status: 'idle',
    rarity: 'legendary',
    cost: 5000,
    skills: ['战略规划', '市场分析', '团队指挥'],
  },
  {
    id: '2',
    name: '陆逊·丞相',
    avatar: '/agents/luxun.png',
    level: 38,
    department: '数据分析部',
    status: 'idle',
    rarity: 'epic',
    cost: 3000,
    skills: ['数据分析', '风险评估', '报告生成'],
  },
  {
    id: '3',
    name: '诸葛亮·军师',
    avatar: '/agents/zhugeliang.png',
    level: 42,
    department: '智能咨询部',
    status: 'idle',
    rarity: 'legendary',
    cost: 5000,
    skills: ['智能问答', '策略建议', '预测分析'],
  },
  {
    id: '4',
    name: '司马懿·谋士',
    avatar: '/agents/sima.png',
    level: 35,
    department: '风险评估部',
    status: 'idle',
    rarity: 'epic',
    cost: 3000,
    skills: ['风险识别', '趋势预测', '决策支持'],
  },
  {
    id: '5',
    name: '郭嘉·祭酒',
    avatar: '/agents/guojia.png',
    level: 30,
    department: '数据分析部',
    status: 'idle',
    rarity: 'rare',
    cost: 1500,
    skills: ['数据处理', '可视化', '统计建模'],
  },
  {
    id: '6',
    name: '荀彧·尚书令',
    avatar: '/agents/xunyu.png',
    level: 28,
    department: '战略规划部',
    status: 'idle',
    rarity: 'rare',
    cost: 1500,
    skills: ['资源调配', '流程优化', '绩效管理'],
  },
  {
    id: '7',
    name: '贾诩·太尉',
    avatar: '/agents/jiaxu.png',
    level: 25,
    department: '风险评估部',
    status: 'idle',
    rarity: 'common',
    cost: 500,
    skills: ['基础分析'],
  },
  {
    id: '8',
    name: '程昱·尚书',
    avatar: '/agents/chengyu.png',
    level: 22,
    department: '智能咨询部',
    status: 'idle',
    rarity: 'common',
    cost: 500,
    skills: ['基础问答'],
  },
];

const MarketPage: React.FC = () => {
  const [selectedRarity, setSelectedRarity] = useState('all');
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showGacha, setShowGacha] = useState(false);
  const [gachaAgent, setGachaAgent] = useState<MarketAgent | null>(null);

  const filteredAgents = sampleAgents.filter((agent) => {
    const matchesRarity = selectedRarity === 'all' || agent.rarity === selectedRarity;
    const matchesDepartment = selectedDepartment === 'all' || 
      agent.department.includes(departmentFilters.find((d) => d.id === selectedDepartment)?.label || '');
    const matchesSearch = searchQuery === '' || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesRarity && matchesDepartment && matchesSearch;
  });

  const handleRecruit = (agent: MarketAgent) => {
    setGachaAgent(agent);
    setShowGacha(true);
  };

  const handleGachaClose = () => {
    setShowGacha(false);
    setGachaAgent(null);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
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
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fluent-deepOcean-500">人才市场</h1>
          <p className="text-gray-500 mt-1">招募智能体，扩充你的团队</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600">
          <Coins className="w-5 h-5 text-fluent-deepOcean-900" />
          <span className="font-semibold text-fluent-deepOcean-900">12,580 积分</span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants}>
        <FluentCard acrylic>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索智能体名称或技能..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {rarityFilters.map((filter) => (
                <motion.button
                  key={filter.id}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    selectedRarity === filter.id
                      ? 'bg-fluent-gold-500 text-white shadow-gold-glow'
                      : filter.color
                  }`}
                  onClick={() => setSelectedRarity(filter.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {filter.label}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="flex gap-2 mt-4 pt-4 border-t border-white/20">
            {departmentFilters.map((filter) => {
              const Icon = filter.icon;
              return (
                <motion.button
                  key={filter.id}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    selectedDepartment === filter.id
                      ? 'bg-fluent-deepOcean-500 text-white'
                      : 'bg-white/30 text-gray-600 hover:bg-white/50'
                  }`}
                  onClick={() => setSelectedDepartment(filter.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Icon className="w-4 h-4" />
                  {filter.label}
                </motion.button>
              );
            })}
          </div>
        </FluentCard>
      </motion.div>

      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        variants={containerVariants}
      >
        <AnimatePresence mode="popLayout">
          {filteredAgents.map((agent) => (
            <motion.div
              key={agent.id}
              variants={itemVariants}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <FluentCard hover className="h-full flex flex-col">
                <AgentCard agent={agent} />
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex flex-wrap gap-1 mb-3">
                    {agent.skills.map((skill) => (
                      <span
                        key={skill}
                        className="text-xs px-2 py-0.5 bg-fluent-deepOcean-50 text-fluent-deepOcean-500 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <Coins className="w-4 h-4 text-fluent-gold-500" />
                      <span className="font-semibold text-fluent-gold-500">
                        {agent.cost.toLocaleString()}
                      </span>
                    </div>
                    <FluentButton
                      variant="gold"
                      size="sm"
                      onClick={() => handleRecruit(agent)}
                    >
                      <Sparkles className="w-4 h-4 mr-1" />
                      招募
                    </FluentButton>
                  </div>
                </div>
              </FluentCard>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {filteredAgents.length === 0 && (
        <motion.div
          className="text-center py-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">没有找到符合条件的智能体</p>
        </motion.div>
      )}

      <GachaAnimation
        isOpen={showGacha}
        onClose={handleGachaClose}
        agent={gachaAgent ? {
          name: gachaAgent.name,
          avatar: gachaAgent.avatar,
          rarity: gachaAgent.rarity,
          level: gachaAgent.level,
          department: gachaAgent.department,
        } : undefined}
      />
    </motion.div>
  );
};

export default MarketPage;
