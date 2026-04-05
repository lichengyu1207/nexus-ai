import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TeamContext {
  id: string;
  name: string;
  skills: string[];
  memberCount: number;
}

interface TaskContext {
  id: string;
  title: string;
  status: string;
  teamId?: string;
}

interface RecruitmentContext {
  id: string;
  teamId: string;
  title: string;
  requiredSkills: string[];
}

interface AppContextStore {
  currentTeam: TeamContext | null;
  currentTask: TaskContext | null;
  currentRecruitment: RecruitmentContext | null;
  
  setCurrentTeam: (team: TeamContext | null) => void;
  setCurrentTask: (task: TaskContext | null) => void;
  setCurrentRecruitment: (recruitment: RecruitmentContext | null) => void;
  
  updateTeamSkills: (skills: string[]) => void;
  updateTaskStatus: (status: string) => void;
  
  clearContext: () => void;
}

export const useAppContextStore = create<AppContextStore>()(
  persist(
    (set) => ({
      currentTeam: null,
      currentTask: null,
      currentRecruitment: null,
      
      setCurrentTeam: (team) => set({ currentTeam: team }),
      setCurrentTask: (task) => set({ currentTask: task }),
      setCurrentRecruitment: (recruitment) => set({ currentRecruitment: recruitment }),
      
      updateTeamSkills: (skills) => set((state) => ({
        currentTeam: state.currentTeam
          ? { ...state.currentTeam, skills }
          : null
      })),
      
      updateTaskStatus: (status) => set((state) => ({
        currentTask: state.currentTask
          ? { ...state.currentTask, status }
          : null
      })),
      
      clearContext: () => set({
        currentTeam: null,
        currentTask: null,
        currentRecruitment: null
      })
    }),
    {
      name: 'app-context-storage',
      partialize: (state) => ({
        currentTeam: state.currentTeam,
        currentTask: state.currentTask
      })
    }
  )
);

export const useCurrentTeam = () => useAppContextStore((state) => state.currentTeam);
export const useCurrentTask = () => useAppContextStore((state) => state.currentTask);
export const useCurrentRecruitment = () => useAppContextStore((state) => state.currentRecruitment);
