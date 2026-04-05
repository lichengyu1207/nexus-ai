import { create } from 'zustand';
import type { Task } from '../types';

interface TaskLog {
  message: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  timestamp: number;
}

interface TaskWithLogs extends Task {
  logs?: TaskLog[];
}

interface TaskStore {
  tasks: Record<string, TaskWithLogs>;
  taskList: string[];
  loading: boolean;
  error: string | null;

  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (task: Partial<Task> & { id: string }) => void;
  updateTaskProgress: (taskId: string, progress: number, currentStep?: string) => void;
  addTaskLog: (taskId: string, log: TaskLog) => void;
  removeTask: (taskId: string) => void;
  clearTasks: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  getTask: (taskId: string) => TaskWithLogs | undefined;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: {},
  taskList: [],
  loading: false,
  error: null,

  setTasks: (tasks) => {
    const tasksMap: Record<string, TaskWithLogs> = {};
    const taskList: string[] = [];
    tasks.forEach((task) => {
      tasksMap[task.id] = task;
      taskList.push(task.id);
    });
    set({ tasks: tasksMap, taskList });
  },

  addTask: (task) => {
    set((state) => ({
      tasks: {
        ...state.tasks,
        [task.id]: task,
      },
      taskList: [task.id, ...state.taskList],
    }));
  },

  updateTask: (taskUpdate) => {
    set((state) => {
      const existingTask = state.tasks[taskUpdate.id];
      if (!existingTask) {
        return state;
      }

      const updatedTask: TaskWithLogs = {
        ...existingTask,
        ...taskUpdate,
        updatedAt: new Date().toISOString(),
      };

      return {
        tasks: {
          ...state.tasks,
          [taskUpdate.id]: updatedTask,
        },
      };
    });
  },

  updateTaskProgress: (taskId, progress, currentStep) => {
    set((state) => {
      const existingTask = state.tasks[taskId];
      if (!existingTask) {
        return state;
      }

      const updatedTask: TaskWithLogs = {
        ...existingTask,
        progress,
        currentStep: currentStep || existingTask.currentStep,
        updatedAt: new Date().toISOString(),
      };

      return {
        tasks: {
          ...state.tasks,
          [taskId]: updatedTask,
        },
      };
    });
  },

  addTaskLog: (taskId, log) => {
    set((state) => {
      const existingTask = state.tasks[taskId];
      if (!existingTask) {
        return state;
      }

      const logs = existingTask.logs || [];
      const updatedTask: TaskWithLogs = {
        ...existingTask,
        logs: [...logs, log],
      };

      return {
        tasks: {
          ...state.tasks,
          [taskId]: updatedTask,
        },
      };
    });
  },

  removeTask: (taskId) => {
    set((state) => {
      const remainingTasks = { ...state.tasks };
      delete remainingTasks[taskId];
      return {
        tasks: remainingTasks,
        taskList: state.taskList.filter((id) => id !== taskId),
      };
    });
  },

  clearTasks: () => {
    set({ tasks: {}, taskList: [] });
  },

  setLoading: (loading) => {
    set({ loading });
  },

  setError: (error) => {
    set({ error });
  },

  getTask: (taskId) => {
    return get().tasks[taskId];
  },
}));

export default useTaskStore;
