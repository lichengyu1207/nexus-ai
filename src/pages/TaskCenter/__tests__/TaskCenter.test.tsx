import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import TaskCenter from '../index';
import { TaskFilters } from '../components/TaskFilters';
import { TaskToolbar } from '../components/TaskToolbar';
import { TaskList } from '../components/TaskList';
import { TaskListItem } from '../components/TaskListItem';
import { BatchActionModal } from '../components/BatchActionModal';
import { NewTaskModal } from '../components/NewTaskModal';
import type { Task, TaskFilters as TaskFiltersType, ViewMode } from '../types';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

const mockTask: Task = {
  id: 'task-1',
  name: '测试任务',
  status: 'processing',
  progress: 50,
  startTime: new Date().toISOString(),
  priority: 'high',
  agentsUsed: ['agent-1'],
};

const mockTasks: Task[] = [
  mockTask,
  {
    id: 'task-2',
    name: '已完成任务',
    status: 'completed',
    progress: 100,
    startTime: new Date(Date.now() - 86400000).toISOString(),
    priority: 'medium',
  },
  {
    id: 'task-3',
    name: '失败任务',
    status: 'failed',
    progress: 30,
    startTime: new Date().toISOString(),
    errorMessage: '执行失败',
  },
];

describe('TaskCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders main heading', () => {
    render(<TaskCenter />);
    expect(screen.getByText('任务中心')).toBeInTheDocument();
  });
});

describe('TaskFilters', () => {
  const mockFilters: TaskFiltersType = { status: [] };
  const mockOnFilterChange = vi.fn();
  const mockOnReset = vi.fn();

  it('renders filter panel', () => {
    render(
      <TaskFilters
        filters={mockFilters}
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    expect(screen.getByText('筛选器')).toBeInTheDocument();
    expect(screen.getByText('状态')).toBeInTheDocument();
    expect(screen.getByText('时间范围')).toBeInTheDocument();
  });

  it('toggles filter panel', () => {
    render(
      <TaskFilters
        filters={mockFilters}
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    const collapseButton = screen.getByLabelText('折叠筛选器');
    fireEvent.click(collapseButton);

    expect(screen.getByLabelText('展开筛选器')).toBeInTheDocument();
  });

  it('calls onReset when reset button is clicked', () => {
    render(
      <TaskFilters
        filters={mockFilters}
        onFilterChange={mockOnFilterChange}
        onReset={mockOnReset}
      />
    );

    const resetButton = screen.getByText('重置');
    fireEvent.click(resetButton);

    expect(mockOnReset).toHaveBeenCalled();
  });
});

describe('TaskToolbar', () => {
  const mockProps = {
    selectedCount: 0,
    onBatchRetry: vi.fn(),
    onBatchDelete: vi.fn(),
    onBatchExport: vi.fn(),
    onCompare: vi.fn(),
    onNewTask: vi.fn(),
    onSearch: vi.fn(),
    onSortChange: vi.fn(),
    viewMode: 'card' as ViewMode,
    onViewModeChange: vi.fn(),
    sortField: 'createdAt' as const,
    sortOrder: 'desc' as const,
    canCompare: false,
  };

  it('renders toolbar buttons', () => {
    render(<TaskToolbar {...mockProps} />);

    expect(screen.getByText('新建任务')).toBeInTheDocument();
    expect(screen.getByText('重试')).toBeInTheDocument();
    expect(screen.getByText('删除')).toBeInTheDocument();
    expect(screen.getByText('导出')).toBeInTheDocument();
    expect(screen.getByText('对比')).toBeInTheDocument();
  });

  it('calls onNewTask when new task button is clicked', () => {
    render(<TaskToolbar {...mockProps} />);

    const newTaskButton = screen.getByText('新建任务');
    fireEvent.click(newTaskButton);

    expect(mockProps.onNewTask).toHaveBeenCalled();
  });

  it('disables batch buttons when no selection', () => {
    render(<TaskToolbar {...mockProps} />);

    const retryButton = screen.getByText('重试').closest('button');
    const deleteButton = screen.getByText('删除').closest('button');

    expect(retryButton).toBeDisabled();
    expect(deleteButton).toBeDisabled();
  });

  it('enables batch buttons when has selection', () => {
    render(<TaskToolbar {...mockProps} selectedCount={2} />);

    const retryButton = screen.getByText('重试').closest('button');
    const deleteButton = screen.getByText('删除').closest('button');

    expect(retryButton).not.toBeDisabled();
    expect(deleteButton).not.toBeDisabled();
  });

  it('toggles view mode', () => {
    const onViewModeChange = vi.fn();
    render(<TaskToolbar {...mockProps} onViewModeChange={onViewModeChange} />);

    const tableViewButton = screen.getByLabelText('表格视图');
    fireEvent.click(tableViewButton);

    expect(onViewModeChange).toHaveBeenCalledWith('table');
  });
});

describe('TaskListItem', () => {
  const mockProps = {
    task: mockTask,
    isSelected: false,
    onSelect: vi.fn(),
    onClick: vi.fn(),
    onRetry: vi.fn(),
    onDelete: vi.fn(),
    viewMode: 'card' as ViewMode,
  };

  it('renders task information', () => {
    render(<TaskListItem {...mockProps} />);

    expect(screen.getByText('测试任务')).toBeInTheDocument();
    expect(screen.getByText('处理中')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    render(<TaskListItem {...mockProps} />);

    const taskItem = screen.getByText('测试任务').closest('div');
    fireEvent.click(taskItem!);

    expect(mockProps.onClick).toHaveBeenCalledWith('task-1');
  });

  it('calls onSelect when checkbox is clicked', () => {
    render(<TaskListItem {...mockProps} />);

    const checkbox = screen.getByLabelText('选择任务 测试任务');
    fireEvent.click(checkbox);

    expect(mockProps.onSelect).toHaveBeenCalledWith('task-1', true);
  });

  it('shows retry button for failed task', () => {
    render(<TaskListItem {...mockProps} task={mockTasks[2]} />);

    expect(screen.getByText('重试')).toBeInTheDocument();
  });
});

describe('TaskList', () => {
  const mockProps = {
    tasks: mockTasks,
    isLoading: false,
    isFetching: false,
    hasNextPage: false,
    fetchNextPage: vi.fn(),
    isFetchingNextPage: false,
    selectedIds: new Set<string>(),
    onSelectTask: vi.fn(),
    onTaskClick: vi.fn(),
    onTaskRetry: vi.fn(),
    onTaskDelete: vi.fn(),
    viewMode: 'card' as ViewMode,
  };

  it('renders task list', () => {
    render(<TaskList {...mockProps} />);

    expect(screen.getByText('测试任务')).toBeInTheDocument();
    expect(screen.getByText('已完成任务')).toBeInTheDocument();
    expect(screen.getByText('失败任务')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<TaskList {...mockProps} isLoading={true} tasks={[]} />);

    expect(screen.getByText('加载任务列表...')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<TaskList {...mockProps} tasks={[]} />);

    expect(screen.getByText('暂无任务')).toBeInTheDocument();
  });
});

describe('BatchActionModal', () => {
  const mockProps = {
    isOpen: true,
    action: 'delete' as const,
    count: 3,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    isPending: false,
  };

  it('renders modal with correct content', () => {
    render(<BatchActionModal {...mockProps} />);

    expect(screen.getByText('批量删除')).toBeInTheDocument();
    expect(screen.getByText('已选择 3 个任务')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    render(<BatchActionModal {...mockProps} />);

    const confirmButton = screen.getByText('确认删除');
    fireEvent.click(confirmButton);

    expect(mockProps.onConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(<BatchActionModal {...mockProps} />);

    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    expect(mockProps.onCancel).toHaveBeenCalled();
  });

  it('does not render when closed', () => {
    render(<BatchActionModal {...mockProps} isOpen={false} />);

    expect(screen.queryByText('批量删除')).not.toBeInTheDocument();
  });
});

describe('NewTaskModal', () => {
  const mockAgents = [
    { id: 'agent-1', name: '估值智能体' },
    { id: 'agent-2', name: '数据分析智能体' },
  ];

  const mockProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
    isPending: false,
    agents: mockAgents,
  };

  it('renders modal with form', () => {
    render(<NewTaskModal {...mockProps} />);

    expect(screen.getByText('新建任务')).toBeInTheDocument();
    expect(screen.getByLabelText('任务名称 *')).toBeInTheDocument();
    expect(screen.getByLabelText('选择智能体 *')).toBeInTheDocument();
  });

  it('calls onClose when cancel is clicked', () => {
    render(<NewTaskModal {...mockProps} />);

    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    expect(mockProps.onClose).toHaveBeenCalled();
  });

  it('disables submit when required fields are empty', () => {
    render(<NewTaskModal {...mockProps} />);

    const submitButton = screen.getByText('创建任务');
    expect(submitButton).toBeDisabled();
  });

  it('enables submit when required fields are filled', () => {
    render(<NewTaskModal {...mockProps} />);

    const nameInput = screen.getByLabelText('任务名称 *');
    fireEvent.change(nameInput, { target: { value: '新任务' } });

    const agentSelect = screen.getByLabelText('选择智能体 *');
    fireEvent.change(agentSelect, { target: { value: 'agent-1' } });

    const submitButton = screen.getByText('创建任务');
    expect(submitButton).not.toBeDisabled();
  });

  it('shows JSON error for invalid params', () => {
    render(<NewTaskModal {...mockProps} />);

    const paramsTextarea = screen.getByLabelText('输入参数 (JSON)');
    fireEvent.change(paramsTextarea, { target: { value: 'invalid json' } });

    expect(screen.getByText('JSON 格式错误')).toBeInTheDocument();
  });
});
