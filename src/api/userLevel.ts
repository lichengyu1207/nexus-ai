import api from '../services/api';

export interface UserLevelInfo {
  technical: LevelInfo;
  management: LevelInfo;
}

export interface LevelInfo {
  current_level: number;
  level_name: string;
  level_title: string;
  progress: number;
  next_level: number | null;
  next_level_name: string | null;
  required_tasks: number;
  completed_tasks: number;
  权益: LevelBenefit[];
}

export interface LevelBenefit {
  id: string;
  name: string;
  description: string;
  level: number;
  type: 'discount' | 'feature' | 'service' | 'exclusive';
  value?: number;
}

export interface LevelRequirement {
  level: number;
  tasks_required: number;
  level_name: string;
  level_title: string;
}

// 技术序列（P序列）
const TECHNICAL_LEVELS: LevelRequirement[] = [
  { level: 1, tasks_required: 0, level_name: 'P1', level_title: '初入者' },
  { level: 2, tasks_required: 1, level_name: 'P2', level_title: '探索者' },
  { level: 3, tasks_required: 5, level_name: 'P3', level_title: '助理' },
  { level: 4, tasks_required: 10, level_name: 'P4', level_title: '初级专员' },
  { level: 5, tasks_required: 20, level_name: 'P5', level_title: '高级工程师' },
  { level: 6, tasks_required: 50, level_name: 'P6', level_title: '资深工程师' },
  { level: 7, tasks_required: 100, level_name: 'P7', level_title: '技术专家' },
  { level: 8, tasks_required: 200, level_name: 'P8', level_title: '高级专家' },
  { level: 9, tasks_required: 500, level_name: 'P9', level_title: '高级专家' },
  { level: 10, tasks_required: 1000, level_name: 'P10', level_title: '研究员' },
  { level: 11, tasks_required: 2000, level_name: 'P11', level_title: '高级研究员' },
  { level: 12, tasks_required: 5000, level_name: 'P12', level_title: '科学家' },
];

// 管理序列（M序列）
const MANAGEMENT_LEVELS: LevelRequirement[] = [
  { level: 1, tasks_required: 0, level_name: 'M1', level_title: '管理新手' },
  { level: 2, tasks_required: 5, level_name: 'M2', level_title: '初级管理' },
  { level: 3, tasks_required: 20, level_name: 'M3', level_title: '中级管理' },
  { level: 4, tasks_required: 50, level_name: 'M4', level_title: '高级管理' },
  { level: 5, tasks_required: 100, level_name: 'M5', level_title: '总监' },
  { level: 6, tasks_required: 200, level_name: 'M6', level_title: '高级总监' },
  { level: 7, tasks_required: 500, level_name: 'M7', level_title: '副总裁' },
  { level: 8, tasks_required: 1000, level_name: 'M8', level_title: '高级副总裁' },
  { level: 9, tasks_required: 2000, level_name: 'M9', level_title: '首席运营官' },
  { level: 10, tasks_required: 3000, level_name: 'M10', level_title: '首席执行官' },
  { level: 11, tasks_required: 4000, level_name: 'M11', level_title: '董事' },
  { level: 12, tasks_required: 5000, level_name: 'M12', level_title: '董事长' },
];

const LEVEL_BENEFITS: LevelBenefit[] = [
  // P1/M1 初入者/管理新手
  { id: 'p1-1', name: '基础功能访问', description: '可访问平台基础功能', level: 1, type: 'feature' },
  { id: 'p1-2', name: '标准积分获取', description: '标准速率获取积分', level: 1, type: 'service' },
  { id: 'p1-3', name: '基础客服支持', description: '标准客服响应时间', level: 1, type: 'service' },
  
  // P2/M2 探索者/初级管理
  { id: 'p2-1', name: '5%任务折扣', description: '任务费用享受5%折扣', level: 2, type: 'discount', value: 5 },
  { id: 'p2-2', name: '新功能测试', description: '优先参与新功能测试', level: 2, type: 'exclusive' },
  { id: 'p2-3', name: '免费分析报告', description: '每月1次免费分析报告', level: 2, type: 'service' },
  
  // P3/M3 助理/中级管理
  { id: 'p3-1', name: '10%任务折扣', description: '任务费用享受10%折扣', level: 3, type: 'discount', value: 10 },
  { id: 'p3-2', name: '专属任务推荐', description: '根据兴趣推荐任务', level: 3, type: 'feature' },
  { id: 'p3-3', name: '免费分析报告', description: '每月2次免费分析报告', level: 3, type: 'service' },
  { id: 'p3-4', name: '基础数据导出', description: '可导出基础数据', level: 3, type: 'feature' },
  
  // P4/M4 初级专员/高级管理
  { id: 'p4-1', name: '15%任务折扣', description: '任务费用享受15%折扣', level: 4, type: 'discount', value: 15 },
  { id: 'p4-2', name: '优先智能体分配', description: '优先获得智能体服务', level: 4, type: 'service' },
  { id: 'p4-3', name: '免费分析报告', description: '每月3次免费分析报告', level: 4, type: 'service' },
  { id: 'p4-4', name: '高级数据导出', description: '可导出高级数据', level: 4, type: 'feature' },
  { id: 'p4-5', name: '专属客服通道', description: '享受专属客服通道', level: 4, type: 'service' },
  
  // P5/M5 高级工程师/总监
  { id: 'p5-1', name: '20%任务折扣', description: '任务费用享受20%折扣', level: 5, type: 'discount', value: 20 },
  { id: 'p5-2', name: '专属智能体团队', description: '配备专属智能体团队', level: 5, type: 'service' },
  { id: 'p5-3', name: '免费分析报告', description: '每月5次免费分析报告', level: 5, type: 'service' },
  { id: 'p5-4', name: '数据API访问', description: '可访问基础API', level: 5, type: 'feature' },
  { id: 'p5-5', name: '优先参与活动', description: '优先参与平台活动', level: 5, type: 'exclusive' },
  
  // P6/M6 资深工程师/高级总监
  { id: 'p6-1', name: '25%任务折扣', description: '任务费用享受25%折扣', level: 6, type: 'discount', value: 25 },
  { id: 'p6-2', name: '专家级智能体团队', description: '配备专家级智能体团队', level: 6, type: 'service' },
  { id: 'p6-3', name: '免费分析报告', description: '每月10次免费分析报告', level: 6, type: 'service' },
  { id: 'p6-4', name: '高级API访问', description: '可访问高级API', level: 6, type: 'feature' },
  { id: 'p6-5', name: '专属客户经理', description: '配备专属客户经理', level: 6, type: 'service' },
  
  // P7/M7 技术专家/副总裁
  { id: 'p7-1', name: '30%任务折扣', description: '任务费用享受30%折扣', level: 7, type: 'discount', value: 30 },
  { id: 'p7-2', name: '大师级智能体团队', description: '配备大师级智能体团队', level: 7, type: 'service' },
  { id: 'p7-3', name: '无限免费分析报告', description: '无限次免费分析报告', level: 7, type: 'service' },
  { id: 'p7-4', name: '企业级API访问', description: '可访问企业级API', level: 7, type: 'feature' },
  { id: 'p7-5', name: '平台活动优先邀请', description: '优先邀请参与平台活动', level: 7, type: 'exclusive' },
  { id: 'p7-6', name: '专属工作空间', description: '拥有专属工作空间', level: 7, type: 'feature' },
  
  // P8/M8 高级专家/高级副总裁
  { id: 'p8-1', name: '35%任务折扣', description: '任务费用享受35%折扣', level: 8, type: 'discount', value: 35 },
  { id: 'p8-2', name: '精英级智能体团队', description: '配备精英级智能体团队', level: 8, type: 'service' },
  { id: 'p8-3', name: '定制化智能体训练', description: '可定制智能体训练', level: 8, type: 'exclusive' },
  { id: 'p8-4', name: '平台决策参与权', description: '参与平台决策讨论', level: 8, type: 'exclusive' },
  { id: 'p8-5', name: '专属活动策划', description: '享受专属活动策划', level: 8, type: 'service' },
  { id: 'p8-6', name: '高级数据分析工具', description: '使用高级数据分析工具', level: 8, type: 'feature' },
  
  // P9/M9 高级专家/首席运营官
  { id: 'p9-1', name: '40%任务折扣', description: '任务费用享受40%折扣', level: 9, type: 'discount', value: 40 },
  { id: 'p9-2', name: '传奇级智能体团队', description: '配备传奇级智能体团队', level: 9, type: 'service' },
  { id: 'p9-3', name: '专属智能体定制', description: '完全定制专属智能体', level: 9, type: 'exclusive' },
  { id: 'p9-4', name: '平台战略咨询权', description: '参与平台战略咨询', level: 9, type: 'exclusive' },
  { id: 'p9-5', name: '专属活动冠名权', description: '获得活动冠名权', level: 9, type: 'exclusive' },
  { id: 'p9-6', name: '企业级数据分析套件', description: '使用企业级数据分析套件', level: 9, type: 'feature' },
  
  // P10/M10 研究员/首席执行官
  { id: 'p10-1', name: '45%任务折扣', description: '任务费用享受45%折扣', level: 10, type: 'discount', value: 45 },
  { id: 'p10-2', name: '神话级智能体团队', description: '配备神话级智能体团队', level: 10, type: 'service' },
  { id: 'p10-3', name: '全平台智能体使用权', description: '使用所有智能体', level: 10, type: 'feature' },
  { id: 'p10-4', name: '平台产品设计参与权', description: '参与产品设计讨论', level: 10, type: 'exclusive' },
  { id: 'p10-5', name: '专属技术支持团队', description: '配备专属技术支持团队', level: 10, type: 'service' },
  { id: 'p10-6', name: '企业级解决方案定制', description: '定制企业级解决方案', level: 10, type: 'service' },
  
  // P11/M11 高级研究员/董事
  { id: 'p11-1', name: '50%任务折扣', description: '任务费用享受50%折扣', level: 11, type: 'discount', value: 50 },
  { id: 'p11-2', name: '创世级智能体团队', description: '配备创世级智能体团队', level: 11, type: 'service' },
  { id: 'p11-3', name: '智能体系统定制权', description: '定制智能体系统', level: 11, type: 'exclusive' },
  { id: 'p11-4', name: '平台生态共建权', description: '参与平台生态建设', level: 11, type: 'exclusive' },
  { id: 'p11-5', name: '专属技术顾问团队', description: '配备专属技术顾问团队', level: 11, type: 'service' },
  { id: 'p11-6', name: '行业解决方案定制', description: '定制行业解决方案', level: 11, type: 'service' },
  
  // P12/M12 科学家/董事长
  { id: 'p12-1', name: '60%任务折扣', description: '任务费用享受60%折扣', level: 12, type: 'discount', value: 60 },
  { id: 'p12-2', name: '主宰级智能体团队', description: '配备主宰级智能体团队', level: 12, type: 'service' },
  { id: 'p12-3', name: '全平台功能无限制访问', description: '无限制访问所有功能', level: 12, type: 'feature' },
  { id: 'p12-4', name: '平台战略决策权', description: '参与平台战略决策', level: 12, type: 'exclusive' },
  { id: 'p12-5', name: '专属技术研发团队', description: '配备专属技术研发团队', level: 12, type: 'service' },
  { id: 'p12-6', name: '全球行业解决方案定制', description: '定制全球行业解决方案', level: 12, type: 'service' },
  { id: 'p12-7', name: '终身会员资格', description: '享受终身会员待遇', level: 12, type: 'exclusive' },
];

const calculateLevelInfo = (completedTasks: number, levelRequirements: LevelRequirement[]): LevelInfo => {
  // 计算当前等级
  let currentLevel = 1;
  let nextLevel = null;
  let nextLevelName = null;
  let requiredTasks = 0;
  
  for (let i = levelRequirements.length - 1; i >= 0; i--) {
    const requirement = levelRequirements[i];
    if (completedTasks >= requirement.tasks_required) {
      currentLevel = requirement.level;
      requiredTasks = requirement.tasks_required;
      break;
    }
  }
  
  // 计算下一级
  if (currentLevel < 12) {
    nextLevel = currentLevel + 1;
    const nextRequirement = levelRequirements.find(req => req.level === nextLevel);
    nextLevelName = nextRequirement?.level_name || null;
  }
  
  // 计算进度
  const currentRequirement = levelRequirements.find(req => req.level === currentLevel);
  const nextRequirement = levelRequirements.find(req => req.level === nextLevel);
  
  let progress = 0;
  if (nextRequirement) {
    const tasksNeeded = nextRequirement.tasks_required - currentRequirement!.tasks_required;
    const tasksCompleted = completedTasks - currentRequirement!.tasks_required;
    progress = Math.min(100, Math.round((tasksCompleted / tasksNeeded) * 100));
  } else {
    progress = 100; // 最高等级
  }
  
  // 获取当前等级的权益
  const benefits = LEVEL_BENEFITS.filter(benefit => benefit.level === currentLevel);
  
  const levelInfo = levelRequirements.find(req => req.level === currentLevel);
  
  return {
    current_level: currentLevel,
    level_name: levelInfo?.level_name || 'P1',
    level_title: levelInfo?.level_title || '初入者',
    progress,
    next_level: nextLevel,
    next_level_name: nextLevelName,
    required_tasks: currentRequirement?.tasks_required || 0,
    completed_tasks,
    权益: benefits,
  };
};

export const userLevelApi = {
  async getUserLevelInfo(completedTasks: number): Promise<UserLevelInfo> {
    return {
      technical: calculateLevelInfo(completedTasks, TECHNICAL_LEVELS),
      management: calculateLevelInfo(completedTasks, MANAGEMENT_LEVELS)
    };
  },
  
  getLevelBenefits(level: number): LevelBenefit[] {
    return LEVEL_BENEFITS.filter(benefit => benefit.level === level);
  },
  
  getAllLevelRequirements(): { technical: LevelRequirement[]; management: LevelRequirement[] } {
    return {
      technical: TECHNICAL_LEVELS,
      management: MANAGEMENT_LEVELS
    };
  },
};

export default userLevelApi;