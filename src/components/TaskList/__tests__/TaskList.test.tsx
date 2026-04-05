import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TaskList from './TaskList';
import { useTaskList } from './useTaskList';
import { useTaskStats } from './useTaskStats';
import type { Task } from './types';

jest.mock('./useTaskList');
jest.mock('./useTaskStats');

const mockTasks: Task[] = [
  {
    id: 'task_001',
    name: '测试任务1',
    status: 'completed',
    progress: 100,
    startTime: '2026-03-27T10:00:00Z',
    resultSummary: '分析完成',
  },
  {
    id: 'task_002',
    name: '测试任务2',
    status: 'processing',
    progress: 50,
    startTime: '2026-03-27T11:00:00Z',
  },
  {
    id: 'task_003',
    name: '测试任务3',
    status: 'failed',
    progress: 30,
    startTime: '2026-03-27T12:00:00Z',
    errorMessage: '网络错误',
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('TaskList', () => {
  beforeEach(() => {
    (useTaskStats as jest.Mock).mockReturnValue({
      data: { total: 3, completed: 1, processing: 1, failed: 1 },
    });
    (useTaskList as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      isFetchingNextPage: false,
      error: null,
      fetchNextPage: jest.fn(),
      hasNextPage: false,
      deleteSelected: jest.fn(),
      selectedIds: [],
      toggleSelect: jest.fn(),
      selectAll: jest.fn(),
      clearSelected: jest.fn(),
    });
  });

  it('renders task list with stats', () => {
    render(<TaskList />, { wrapper: createWrapper() });
    
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('总任务')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders all tasks', () => {
    render(<TaskList />, { wrapper: createWrapper() });
    
    expect(screen.getByText('测试任务1')).toBeInTheDocument();
    expect(screen.getByText('测试任务2')).toBeInTheDocument();
    expect(screen.getByText('测试任务3')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    (useTaskList as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: true,
      isFetchingNextPage: false,
      error: null,
      fetchNextPage: jest.fn(),
      hasNextPage: false,
      deleteSelected: jest.fn(),
      selectedIds: [],
      toggleSelect: jest.fn(),
      selectAll: jest.fn(),
    });

    render(<TaskList />, { wrapper: createWrapper() });
    
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('shows empty state when no tasks', () => {
    (useTaskList as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: false,
      isFetchingNextPage: false,
      error: null,
      fetchNextPage: jest.fn(),
      hasNextPage: false,
      deleteSelected: jest.fn(),
      selectedIds: [],
      toggleSelect: jest.fn(),
      selectAll: jest.fn(),
    });

    render(<TaskList />, { wrapper: createWrapper() });
    
    expect(screen.getByText('暂无任务')).toBeInTheDocument();
  });

  it('shows error state', () => {
    (useTaskList as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: false,
      isFetchingNextPage: false,
      error: new Error('Network error'),
      fetchNextPage: jest.fn(),
      hasNextPage: false,
      deleteSelected: jest.fn(),
      selectedIds: [],
      toggleSelect: jest.fn(),
      selectAll: jest.fn(),
    });

    render(<TaskList />, { wrapper: createWrapper() });
    
    expect(screen.getByText('加载失败，请稍后重试')).toBeInTheDocument();
  });

  it('calls deleteSelected when delete button clicked', async () => {
    const mockDeleteSelected = jest.fn();
    window.confirm = jest.fn(() => true);
    
    (useTaskList as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      isFetchingNextPage: false,
      error: null,
      fetchNextPage: jest.fn(),
      hasNextPage: false,
      deleteSelected: mockDeleteSelected,
      selectedIds: ['task_001'],
      toggleSelect: jest.fn(),
      selectAll: jest.fn(),
    });

    render(<TaskList />, { wrapper: createWrapper() });
    
    const deleteButton = screen.getByText(/删除所选/);
    fireEvent.click(deleteButton);
    
    expect(mockDeleteSelected).toHaveBeenCalled();
  });

  it('matches snapshot', () => {
    const { container } = render(<TaskList />, { wrapper: createWrapper() });
    expect(container.firstChild).toMatchSnapshot();
  });
});
