import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface UIState {
  theme: Theme;
  sidebarCollapsed: boolean;
  mascotEnabled: boolean;
  mascotPosition: { x: number; y: number };
  language: string;
  
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleMascot: () => void;
  setMascotPosition: (position: { x: number; y: number }) => void;
  setLanguage: (language: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarCollapsed: false,
      mascotEnabled: true,
      mascotPosition: { x: 0, y: 0 },
      language: 'zh-CN',
      
      setTheme: (theme) => set({ theme }),
      
      toggleSidebar: () => set((state) => ({ 
        sidebarCollapsed: !state.sidebarCollapsed 
      })),
      
      setSidebarCollapsed: (collapsed) => set({ 
        sidebarCollapsed: collapsed 
      }),
      
      toggleMascot: () => set((state) => ({ 
        mascotEnabled: !state.mascotEnabled 
      })),
      
      setMascotPosition: (position) => set({ 
        mascotPosition: position 
      }),
      
      setLanguage: (language) => set({ language }),
    }),
    {
      name: 'ui-storage',
    }
  )
);
