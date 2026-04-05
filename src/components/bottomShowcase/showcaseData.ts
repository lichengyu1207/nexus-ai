export interface ShowcaseItem {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  gradient: string;
  stats?: {
    label: string;
    value: string | number;
  }[];
}

export const showcaseItems: ShowcaseItem[] = [
  {
    id: 'demand',
    title: '需求唤醒',
    description: '智能体理解您的意图，拆解任务',
    icon: '💡',
    color: '#D4AF37',
    gradient: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
    stats: [
      { label: '意图识别率', value: '98.5%' },
      { label: '平均响应', value: '0.3s' },
    ],
  },
  {
    id: 'swarm',
    title: '蜂群调度',
    description: '智能体动态注册、发现、共识',
    icon: '🐝',
    color: '#8A2BE2',
    gradient: 'linear-gradient(135deg, #8A2BE2, #7C3AED)',
    stats: [
      { label: '在线节点', value: 13 },
      { label: '共识延迟', value: '45ms' },
    ],
  },
  {
    id: 'collaboration',
    title: '集群协作',
    description: '六部智能体各司其职，协同工作',
    icon: '🤝',
    color: '#3B82F6',
    gradient: 'linear-gradient(135deg, #3B82F6, #60A5FA)',
    stats: [
      { label: '活跃智能体', value: 6 },
      { label: '协作效率', value: '+45%' },
    ],
  },
  {
    id: 'memory',
    title: '记忆挖掘',
    description: '海马体记忆主动调用与关联',
    icon: '🧠',
    color: '#8B5CF6',
    gradient: 'linear-gradient(135deg, #8B5CF6, #A78BFA)',
    stats: [
      { label: '记忆总量', value: '1.2M' },
      { label: '关联深度', value: '12层' },
    ],
  },
  {
    id: 'evolution',
    title: '人格进化',
    description: '周瑜/陆逊根据交互调整风格',
    icon: '⚡',
    color: '#10B981',
    gradient: 'linear-gradient(135deg, #10B981, #34D399)',
    stats: [
      { label: '适应度', value: '94.2%' },
      { label: '进化等级', value: 'Lv.8' },
    ],
  },
  {
    id: 'report',
    title: '报告生成',
    description: '数据汇聚成可视化分析报告',
    icon: '📊',
    color: '#EF4444',
    gradient: 'linear-gradient(135deg, #EF4444, #F87171)',
    stats: [
      { label: '报告生成', value: '15s' },
      { label: '准确率', value: '96.8%' },
    ],
  },
];

export const mockShowcaseData = {
  demand: {
    exampleInput: '帮我分析深圳南山区学区房',
    parsedTasks: [
      { id: 1, task: '学区信息查询', agent: '礼部' },
      { id: 2, task: '价格趋势分析', agent: '户部' },
      { id: 3, task: '交通配套评估', agent: '兵部' },
    ],
  },
  collaboration: {
    agents: [
      { id: 'li', name: '吏部', status: 'working', task: '位置地段分析' },
      { id: 'hu', name: '户部', status: 'working', task: '价格预算分析' },
      { id: 'li_guan', name: '礼部', status: 'done', task: '学区教育分析' },
      { id: 'bing', name: '兵部', status: 'working', task: '交通出行分析' },
      { id: 'gong', name: '工部', status: 'idle', task: '开发商品质分析' },
      { id: 'xing', name: '刑部', status: 'idle', task: '政策法规分析' },
    ],
  },
  memory: {
    totalMemories: 1248,
    importantMemories: 86,
    recentConnections: [
      { from: '学区房需求', to: '南山区房源', strength: 0.92 },
      { from: '价格分析', to: '地铁规划', strength: 0.78 },
      { from: '用户偏好', to: '教育资源', strength: 0.85 },
    ],
  },
  evolution: {
    currentPersonality: 'zhouyu' as const,
    adaptationScore: 94.2,
    level: 8,
    unlockedAbilities: ['多轮诱导检测', '情感识别', '风险预警'],
  },
  report: {
    progress: 100,
    title: '深圳南山区学区房分析报告',
    summary: '经过六部智能体协同分析，该区域学区房具有较高的投资价值和居住品质...',
    charts: ['房价趋势', '区域对比', '配套分布'],
  },
};
