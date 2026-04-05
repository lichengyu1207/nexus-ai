/**
 * 用户来源追踪工具函数
 * 识别用户来源并存储到 localStorage
 * 采用首次触点归因模型（First-Touch Attribution）
 */

export type UserSourceType = 'direct' | 'laohai' | 'seo' | 'social' | 'ads' | 'invite' | 'referral';

export interface UTMParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

const SOURCE_STORAGE_KEY = 'user_source';
const UTM_STORAGE_KEY = 'utm_params';
const FIRST_VISIT_KEY = 'first_visit_time';

/**
 * 检测用户来源（内部函数）
 * 优先级：URL参数 > referrer > 默认
 */
const detectSourceInternal = (): UserSourceType => {
  const params = new URLSearchParams(window.location.search);
  
  // 1. 检查 URL 参数中的 source
  const sourceParam = params.get('source')?.toLowerCase();
  if (sourceParam) {
    const sourceMapping: Record<string, UserSourceType> = {
      'laohai': 'laohai',
      'zhihu': 'laohai',
      'weixin': 'laohai',
      'wechat': 'laohai',
      'weibo': 'laohai',
      'bilibili': 'laohai',
      'seo': 'seo',
      'search': 'seo',
      'google': 'seo',
      'baidu': 'seo',
      'ads': 'ads',
      'ad': 'ads',
      'invite': 'invite',
      'ref': 'referral',
    };
    return sourceMapping[sourceParam] || 'direct';
  }
  
  // 2. 检查 referrer
  const referrer = document.referrer?.toLowerCase() || '';
  if (referrer.includes('google.com') || referrer.includes('baidu.com') || 
      referrer.includes('bing.com') || referrer.includes('sogou.com')) {
    return 'seo';
  }
  if (referrer.includes('zhihu.com') || referrer.includes('weixin.qq.com') || 
      referrer.includes('weibo.com') || referrer.includes('bilibili.com')) {
    return 'social';
  }
  
  // 3. 默认
  return 'direct';
};

/**
 * 检测并存储来源（首次触点归因）
 * 如果已有来源，直接返回存储值，不再更新
 */
export const detectAndStoreSource = (): UserSourceType => {
  // 如果已经存储过来源，直接返回存储值（首次触点归因）
  const stored = localStorage.getItem(SOURCE_STORAGE_KEY);
  if (stored) {
    return stored as UserSourceType;
  }
  
  // 首次访问，识别来源
  const source = detectSourceInternal();
  
  // 存储首次来源和首次访问时间
  localStorage.setItem(SOURCE_STORAGE_KEY, source);
  localStorage.setItem(FIRST_VISIT_KEY, Date.now().toString());
  
  return source;
};

/**
 * 获取首次访问时间
 */
export const getFirstVisitTime = (): number | null => {
  const time = localStorage.getItem(FIRST_VISIT_KEY);
  return time ? parseInt(time, 10) : null;
};

/**
 * 检查是否为新用户（首次访问）
 */
export const isFirstVisit = (): boolean => {
  return !localStorage.getItem(SOURCE_STORAGE_KEY);
};

/**
 * 提取 UTM 参数
 */
export const extractUTMParams = (): UTMParams => {
  const params = new URLSearchParams(window.location.search);
  return {
    utm_source: params.get('utm_source') || undefined,
    utm_medium: params.get('utm_medium') || undefined,
    utm_campaign: params.get('utm_campaign') || undefined,
    utm_term: params.get('utm_term') || undefined,
    utm_content: params.get('utm_content') || undefined,
  };
};

/**
 * 存储用户来源（仅在首次访问时调用）
 * 注意：此函数已由 detectAndStoreSource 内部调用，一般不需要手动调用
 */
export const storeSource = (source: UserSourceType): void => {
  // 仅在无来源时存储（首次触点归因）
  if (!localStorage.getItem(SOURCE_STORAGE_KEY)) {
    localStorage.setItem(SOURCE_STORAGE_KEY, source);
    localStorage.setItem(FIRST_VISIT_KEY, Date.now().toString());
  }
};

/**
 * 存储UTM参数
 */
export const storeUTMParams = (params: UTMParams): void => {
  const hasUtm = Object.values(params).some(v => v !== undefined);
  if (hasUtm) {
    localStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(params));
  }
};

/**
 * 获取存储的来源
 */
export const getStoredSource = (): UserSourceType => {
  return (localStorage.getItem(SOURCE_STORAGE_KEY) as UserSourceType) || 'direct';
};

/**
 * 获取存储的UTM参数
 */
export const getStoredUTMParams = (): UTMParams => {
  try {
    const stored = localStorage.getItem(UTM_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
};

/**
 * 清除来源信息（用于测试或用户主动清除）
 */
export const clearSource = (): void => {
  localStorage.removeItem(SOURCE_STORAGE_KEY);
  localStorage.removeItem(UTM_STORAGE_KEY);
  localStorage.removeItem(FIRST_VISIT_KEY);
};

/**
 * 初始化来源追踪
 * 在应用入口调用一次
 */
export const initSourceTracking = (): UserSourceType => {
  return detectAndStoreSource();
};

/**
 * 获取来源显示配置
 */
export const getSourceConfig = (source: UserSourceType) => {
  const configs: Record<UserSourceType, {
    title: string;
    subtitle: string;
    buttonText: string;
    mascotEmotion: 'default' | 'happy' | 'thinking' | 'confused' | 'surprised' | 'comforting';
    mascotMessage: string;
    freeIntegral: number;
    bonusLabel?: string;
  }> = {
    laohai: {
      title: '老骇的朋友，欢迎你！',
      subtitle: '这是为你准备的专属福利',
      buttonText: '领取免费分析',
      mascotEmotion: 'happy',
      mascotMessage: '嗨！老骇的朋友，点我开始分析吧～',
      freeIntegral: 5,
      bonusLabel: '粉丝专属福利',
    },
    seo: {
      title: '找到你关心的房价了',
      subtitle: '输入地址，立即获取专业报告',
      buttonText: '开始分析',
      mascotEmotion: 'thinking',
      mascotMessage: '我猜你在找房价？试试输入地址！',
      freeIntegral: 3,
    },
    social: {
      title: '大家都在用的房产AI',
      subtitle: '从社交平台来的朋友，送你3次免费体验',
      buttonText: '立即体验',
      mascotEmotion: 'happy',
      mascotMessage: '听说你从社交平台来，送你3次免费分析！',
      freeIntegral: 3,
    },
    ads: {
      title: '让AI帮你 看透 房子',
      subtitle: '透明、可信的房产分析平台',
      buttonText: '开始免费分析',
      mascotEmotion: 'default',
      mascotMessage: '欢迎！需要我帮你分析哪里的房子？',
      freeIntegral: 3,
    },
    invite: {
      title: '朋友推荐来的？欢迎！',
      subtitle: '你的朋友也在这里，送你4次免费分析',
      buttonText: '开始体验',
      mascotEmotion: 'happy',
      mascotMessage: '你的朋友推荐你来，快试试吧！',
      freeIntegral: 4,
      bonusLabel: '推荐福利',
    },
    referral: {
      title: '朋友推荐来的？欢迎！',
      subtitle: '你的朋友也在这里，送你4次免费分析',
      buttonText: '开始体验',
      mascotEmotion: 'happy',
      mascotMessage: '你的朋友推荐你来，快试试吧！',
      freeIntegral: 4,
      bonusLabel: '推荐福利',
    },
    direct: {
      title: '让AI帮你 看透 房子',
      subtitle: '透明、可信的房产分析平台',
      buttonText: '开始免费分析',
      mascotEmotion: 'default',
      mascotMessage: '欢迎！需要我帮你分析哪里的房子？',
      freeIntegral: 3,
    },
  };
  
  return configs[source] || configs.direct;
};
