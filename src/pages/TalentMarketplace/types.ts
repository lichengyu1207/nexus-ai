export type TalentType = 'agent' | 'human';

export type Availability = 'fulltime' | 'parttime' | 'ondemand';

export type PriceType = 'per_use' | 'subscription';

export type BudgetType = 'fixed' | 'hourly';

export type RecruitmentStatus = 'open' | 'closed' | 'cancelled';

export type BidStatus = 'pending' | 'accepted' | 'rejected';

export type InvitationStatus = 'pending' | 'accepted' | 'declined';

export type ViewMode = 'talents' | 'skills' | 'my-recruitments' | 'my-bids';

export interface Talent {
  id: string;
  type: TalentType;
  name: string;
  avatar?: string;
  title: string;
  skills: string[];
  rating: number;
  reviewCount: number;
  price: number;
  verified: boolean;
  bio?: string;
  portfolio?: string[];
  availability: Availability;
  location?: string;
  createdAt: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  priceType: PriceType;
  price: number;
  callCount: number;
  rating: number;
  documentation?: string;
  exampleCode?: string;
  tags: string[];
}

export interface Recruitment {
  id: string;
  title: string;
  description: string;
  requiredSkills: string[];
  budgetType: BudgetType;
  budget: number;
  deadline: string;
  status: RecruitmentStatus;
  createdAt: string;
  ownerId: string;
  invitedTalentIds?: string[];
  bids: Bid[];
}

export interface Bid {
  id: string;
  recruitmentId: string;
  talentId: string;
  proposal: string;
  price: number;
  estimatedDays: number;
  status: BidStatus;
  createdAt: string;
}

export interface Invitation {
  id: string;
  fromUserId: string;
  toTalentId: string;
  title: string;
  description: string;
  budget: number;
  deadline: string;
  status: InvitationStatus;
}

export interface Review {
  id: string;
  fromUserId: string;
  toTalentId: string;
  rating: number;
  comment: string;
  projectId?: string;
  createdAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  senderName: string;
  senderAvatar?: string;
  content: string;
  type: 'text' | 'file' | 'system';
  read: boolean;
  createdAt: string;
}

export interface Conversation {
  id: string;
  participants: string[];
  lastMessage?: Message;
  unreadCount: number;
  updatedAt: string;
}

export interface TalentFilters {
  skills?: string[];
  domain?: string;
  priceMin?: number;
  priceMax?: number;
  ratingMin?: number;
  verified?: boolean;
  availability?: Availability;
  location?: string;
  search?: string;
}

export interface TalentListResponse {
  talents: Talent[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface SkillListResponse {
  skills: Skill[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface RecruitmentListResponse {
  recruitments: Recruitment[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export const SKILL_CATEGORIES: Record<string, { label: string; icon: string }> = {
  data_analysis: { label: '数据分析', icon: 'ChartBarIcon' },
  model_training: { label: '模型训练', icon: 'CpuChipIcon' },
  valuation: { label: '房产估值', icon: 'CalculatorIcon' },
  report_generation: { label: '报告生成', icon: 'DocumentTextIcon' },
  api_integration: { label: 'API集成', icon: 'CodeBracketIcon' },
  nlp: { label: '自然语言处理', icon: 'ChatBubbleLeftRightIcon' },
};

export const DOMAINS: Record<string, string> = {
  real_estate: '房地产',
  finance: '金融',
  technology: '科技',
  consulting: '咨询',
  education: '教育',
};

export const AVAILABILITY_CONFIG: Record<Availability, { label: string; color: string }> = {
  fulltime: { label: '全职', color: 'text-green-400' },
  parttime: { label: '兼职', color: 'text-blue-400' },
  ondemand: { label: '按需', color: 'text-amber-400' },
};

export const TALENT_TYPE_CONFIG: Record<TalentType, { label: string; icon: string; color: string }> = {
  agent: { label: '智能体', icon: '🤖', color: 'text-amber-400' },
  human: { label: '人类专家', icon: '👤', color: 'text-blue-400' },
};

export const BUDGET_TYPE_CONFIG: Record<BudgetType, { label: string }> = {
  fixed: { label: '固定价格' },
  hourly: { label: '时薪' },
};

export const BID_STATUS_CONFIG: Record<BidStatus, { label: string; color: string }> = {
  pending: { label: '待审核', color: 'text-amber-400' },
  accepted: { label: '已接受', color: 'text-green-400' },
  rejected: { label: '已拒绝', color: 'text-red-400' },
};

export const RECRUITMENT_STATUS_CONFIG: Record<RecruitmentStatus, { label: string; color: string }> = {
  open: { label: '招募中', color: 'text-green-400' },
  closed: { label: '已关闭', color: 'text-gray-400' },
  cancelled: { label: '已取消', color: 'text-red-400' },
};
