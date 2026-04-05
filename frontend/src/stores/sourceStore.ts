import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SourceState {
  source: string | null;
  ref: string | null;
  setSource: (source: string) => void;
  setRef: (ref: string) => void;
  clearSource: () => void;
}

export const useSourceStore = create<SourceState>()(
  persist(
    (set) => ({
      source: null,
      ref: null,
      
      setSource: (source) => set({ source }),
      
      setRef: (ref) => set({ ref }),
      
      clearSource: () => set({ source: null, ref: null }),
    }),
    {
      name: 'source-storage',
    }
  )
);

export const getSourceLabel = (source: string | null): string => {
  const labels: Record<string, string> = {
    laohai: '老骇粉丝',
    seo: '搜索引擎',
    social: '社交媒体',
    direct: '直接访问',
    referral: '好友推荐',
  };
  return source ? labels[source] || source : '直接访问';
};
