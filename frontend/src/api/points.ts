import api from './client';

export interface SigninStatus {
  today_signed: boolean;
  consecutive_days: number;
  today_reward: number;
  next_day: number;
  signed_dates: string[];
  rewards_table: number[];
}

export interface SigninResult {
  success: boolean;
  reward: number;
  consecutive_days: number;
  message: string;
}

export interface MembershipPrices {
  [key: string]: {
    price: number;
    days: number;
    name: string;
  };
}

export interface MembershipStatus {
  membership_type: string;
  start_date: string | null;
  end_date: string | null;
  remaining_days: number;
  is_active: boolean;
}

export interface InviteStats {
  invite_code: string | null;
  invite_link: string | null;
  invited_count: number;
  total_reward: number;
}

export interface UploadRecord {
  id: string;
  data_type: string;
  status: string;
  review_notes: string | null;
  reward_integral: number | null;
  created_at: string;
  reviewed_at: string | null;
}

export const pointsApi = {
  getSigninStatus: () => 
    api.get<SigninStatus>('/points/signin/status'),
  
  doSignin: () => 
    api.post<SigninResult>('/points/signin'),
  
  getMembershipPrices: () => 
    api.get<MembershipPrices>('/points/membership/prices'),
  
  getMembershipStatus: () => 
    api.get<MembershipStatus>('/points/membership/status'),
  
  exchangeMembership: (membershipType: string) => 
    api.post('/points/membership/exchange', { membership_type: membershipType }),
  
  createInvite: () => 
    api.post<{ invite_code: string; invite_link: string }>('/points/invite/create'),
  
  getInviteStats: () => 
    api.get<InviteStats>('/points/invite/stats'),
  
  uploadData: (dataType: string, dataContent: Record<string, unknown>) => 
    api.post('/points/upload', { data_type: dataType, data_content: dataContent }),
  
  getUploads: (limit = 10, offset = 0) => 
    api.get<{ records: UploadRecord[]; total: number }>(`/points/uploads?limit=${limit}&offset=${offset}`),
  
  markWechatAdded: () => 
    api.post('/points/wechat-added'),
};
