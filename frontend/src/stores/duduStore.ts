import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

export type EmotionType = 'happy' | 'thinking' | 'surprised' | 'sad' | 'angry' | 'excited' | 'cute' | 'idle';
export type ActionType = 'wave' | 'spin' | 'gong' | 'point' | 'head_hold' | 'confetti' | 'yawn' | 'idle' | 'heart' | 'clap' | 'alert';

export interface EmotionState {
  pleasure: number;
  activity: number;
  intimacy: number;
}

export interface LevelInfo {
  level: number;
  exp: number;
  exp_required: number;
  total_interactions: number;
}

export interface Costume {
  costume_id: string;
  name: string;
  category: string;
  rarity: string;
  unlock_level: number;
  price: number;
  equipped: boolean;
  owned: boolean;
  unlocked: boolean;
}

export interface DuduState {
  user_id: string;
  emotion_state: EmotionState;
  level_info: LevelInfo;
  current_emotion: EmotionType;
  current_action: ActionType;
  current_message: string;
  equipped_costumes: Record<string, string>;
  available_costumes: Costume[];
}

interface DuduStore {
  state: DuduState | null;
  isVisible: boolean;
  position: { x: number; y: number };
  isLoading: boolean;
  error: string | null;
  
  setState: (state: DuduState) => void;
  setEmotion: (emotion: EmotionType) => void;
  setAction: (action: ActionType) => void;
  showMessage: (message: string, duration?: number) => void;
  setVisibility: (visible: boolean) => void;
  setPosition: (position: { x: number; y: number }) => void;
  
  fetchState: (userId: string) => Promise<void>;
  clickDudu: (userId: string) => Promise<{ integralBonus: number; message: string }>;
  feedDudu: (userId: string, foodType?: string, integralCost?: number) => Promise<void>;
  triggerEvent: (userId: string, eventType: string, data?: Record<string, unknown>) => Promise<void>;
  equipCostume: (userId: string, costumeId: string) => Promise<boolean>;
  
  getRandomAction: (userId: string) => Promise<{ emotion: EmotionType; action: ActionType; message: string }>;
}

export const useDuduStore = create<DuduStore>()(
  subscribeWithSelector((set, get) => ({
    state: null,
    isVisible: true,
    position: { x: 20, y: 80 },
    isLoading: false,
    error: null,
    
    setState: (state) => set({ state }),
    
    setEmotion: (emotion) => {
      const currentState = get().state;
      if (currentState) {
        set({ state: { ...currentState, current_emotion: emotion } });
      }
    },
    
    setAction: (action) => {
      const currentState = get().state;
      if (currentState) {
        set({ state: { ...currentState, current_action: action } });
      }
    },
    
    showMessage: (message, duration = 3000) => {
      const currentState = get().state;
      if (currentState) {
        set({ state: { ...currentState, current_message: message } });
        setTimeout(() => {
          const s = get().state;
          if (s && s.current_message === message) {
            set({ state: { ...s, current_message: '' } });
          }
        }, duration);
      }
    },
    
    setVisibility: (visible) => set({ isVisible: visible }),
    
    setPosition: (position) => set({ position }),
    
    fetchState: async (userId: string) => {
      set({ isLoading: true, error: null });
      try {
        const response = await fetch(`/api/dudu/state/${userId}`);
        if (!response.ok) throw new Error('Failed to fetch dudu state');
        const state = await response.json();
        set({ state, isLoading: false });
      } catch (error) {
        set({ error: (error as Error).message, isLoading: false });
      }
    },
    
    clickDudu: async (userId: string) => {
      try {
        const response = await fetch('/api/dudu/click', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId })
        });
        if (!response.ok) throw new Error('Failed to click dudu');
        const data = await response.json();
        if (data.state) {
          set({ state: data.state });
        }
        return { integralBonus: data.integral_bonus || 0, message: data.message || '' };
      } catch (error) {
        console.error('Click dudu error:', error);
        return { integralBonus: 0, message: '' };
      }
    },
    
    feedDudu: async (userId: string, foodType = 'default', integralCost = 10) => {
      try {
        const response = await fetch('/api/dudu/feed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, food_type: foodType, integral_cost: integralCost })
        });
        if (!response.ok) throw new Error('Failed to feed dudu');
        const data = await response.json();
        if (data.state) {
          set({ state: data.state });
        }
      } catch (error) {
        console.error('Feed dudu error:', error);
      }
    },
    
    triggerEvent: async (userId: string, eventType: string, data?: Record<string, unknown>) => {
      try {
        const response = await fetch('/api/dudu/event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, event_type: eventType, data })
        });
        if (!response.ok) throw new Error('Failed to trigger event');
        const result = await response.json();
        if (result.state) {
          set({ state: result.state });
        }
      } catch (error) {
        console.error('Trigger event error:', error);
      }
    },
    
    equipCostume: async (userId: string, costumeId: string) => {
      try {
        const response = await fetch('/api/dudu/equip-costume', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, costume_id: costumeId })
        });
        if (!response.ok) throw new Error('Failed to equip costume');
        const data = await response.json();
        if (data.state) {
          set({ state: data.state });
        }
        return data.success;
      } catch (error) {
        console.error('Equip costume error:', error);
        return false;
      }
    },
    
    getRandomAction: async (userId: string) => {
      try {
        const response = await fetch(`/api/dudu/random-action/${userId}`);
        if (!response.ok) throw new Error('Failed to get random action');
        return await response.json();
      } catch (error) {
        console.error('Get random action error:', error);
        return { emotion: 'idle' as EmotionType, action: 'idle' as ActionType, message: '' };
      }
    }
  }))
);

export const emotionEmojiMap: Record<EmotionType, string> = {
  happy: '😊',
  thinking: '🤔',
  surprised: '😲',
  sad: '😢',
  angry: '😠',
  excited: '🤩',
  cute: '🥺',
  idle: '😐'
};

export const actionLabelMap: Record<ActionType, string> = {
  wave: '挥手',
  spin: '转圈',
  gong: '敲锣',
  point: '指路',
  head_hold: '抱头',
  confetti: '撒花',
  yawn: '打哈欠',
  idle: '待机',
  heart: '比心',
  clap: '拍手',
  alert: '警告'
};

export const rarityColorMap: Record<string, string> = {
  common: '#9e9e9e',
  rare: '#2196f3',
  epic: '#9c27b0',
  legendary: '#ff9800'
};
