import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ActivityPanel from '../index';
import { FloatingButton } from '../FloatingButton';
import { AgentStatusList } from '../AgentStatusList';
import { TaskQueueList } from '../TaskQueueList';
import { CallLogList } from '../CallLogList';
import { LogDetailModal } from '../LogDetailModal';
import type { AgentStatus, QueueTask, CallLog } from '../types';

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
    {children}
  </QueryClientProvider>
);

const mockAgents: AgentStatus[] = [
  { id: 'agent-1', name: '估值智能体', status: 'healthy', currentTasks: 2 },
  { id: 'agent-2', name: '数据分析智能体', status: 'busy', currentTasks: 5 },
  { id: 'agent-3', name: '报告生成智能体', status: 'error', currentTasks: 0 },
];

const mockTasks: QueueTask[] = [
  { id: 'task-1', name: '房产估值任务', status: 'processing', progress: 60, startTime: new Date().toISOString() },
  { id: 'task-2', name: '数据分析任务', status: 'pending' },
];

const mockLogs: CallLog[] = [
  {
    id: 'log-1',
    timestamp: new Date().toISOString(),
    agentId: 'agent-1',
    agentName: '估值智能体',
    toolId: 'tool-1',
    toolName: '估值计算',
    result: 'success',
    duration: 1500,
  },
  {
    id: 'log-2',
    timestamp: new Date().toISOString(),
    agentId: 'agent-2',
    agentName: '数据分析智能体',
    toolId: 'tool-2',
    toolName: '数据查询',
    result: 'failure',
    duration: 500,
    details: { error: 'Connection timeout' },
  },
];

describe('ActivityPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    localStorage.clear();
  });

  it('renders floating button when closed', () => {
    render(wrapper(<ActivityPanel />));
    expect(screen.getByLabelText('打开智能体活动面板')).toBeInTheDocument();
  });
});

describe('FloatingButton', () => {
  const mockOnClick = vi.fn();

  it('renders button correctly', () => {
    render(<FloatingButton onClick={mockOnClick} hasUnread={false} />);
    expect(screen.getByLabelText('打开智能体活动面板')).toBeInTheDocument();
  });

  it('shows unread badge when hasUnread is true', () => {
    render(<FloatingButton onClick={mockOnClick} hasUnread={true} unreadCount={5} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('shows 99+ when unreadCount exceeds 99', () => {
    render(<FloatingButton onClick={mockOnClick} hasUnread={true} unreadCount={100} />);
    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    render(<FloatingButton onClick={mockOnClick} hasUnread={false} />);
    fireEvent.click(screen.getByLabelText('打开智能体活动面板'));
    expect(mockOnClick).toHaveBeenCalled();
  });
});

describe('AgentStatusList', () => {
  it('renders empty state', () => {
    render(<AgentStatusList agents={[]} />);
    expect(screen.getByText('暂无智能体状态')).toBeInTheDocument();
  });

  it('renders agent list correctly', () => {
    render(<AgentStatusList agents={mockAgents} />);

    expect(screen.getByText('估值智能体')).toBeInTheDocument();
    expect(screen.getByText('数据分析智能体')).toBeInTheDocument();
    expect(screen.getByText('报告生成智能体')).toBeInTheDocument();
  });

  it('shows correct task counts', () => {
    render(<AgentStatusList agents={mockAgents} />);

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});

describe('TaskQueueList', () => {
  it('renders empty state', () => {
    render(<TaskQueueList tasks={[]} />);
    expect(screen.getByText('队列为空')).toBeInTheDocument();
  });

  it('renders task list correctly', () => {
    render(<TaskQueueList tasks={mockTasks} />);

    expect(screen.getByText('房产估值任务')).toBeInTheDocument();
    expect(screen.getByText('数据分析任务')).toBeInTheDocument();
  });

  it('shows status badges', () => {
    render(<TaskQueueList tasks={mockTasks} />);

    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('排队中')).toBeInTheDocument();
  });

  it('shows progress bar for processing tasks', () => {
    render(<TaskQueueList tasks={mockTasks} />);

    expect(screen.getByText('进度')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('shows overflow message when more than 10 tasks', () => {
    const manyTasks: QueueTask[] = Array.from({ length: 15 }, (_, i) => ({
      id: `task-${i}`,
      name: `任务 ${i + 1}`,
      status: 'pending' as const,
    }));

    render(<TaskQueueList tasks={manyTasks} />);

    expect(screen.getByText('还有 5 个任务...')).toBeInTheDocument();
  });
});

describe('CallLogList', () => {
  const mockOnLogClick = vi.fn();

  it('renders empty state', () => {
    render(<CallLogList logs={[]} onLogClick={mockOnLogClick} />);
    expect(screen.getByText('暂无调用日志')).toBeInTheDocument();
  });

  it('renders log list correctly', () => {
    render(<CallLogList logs={mockLogs} onLogClick={mockOnLogClick} />);

    expect(screen.getByText('估值智能体')).toBeInTheDocument();
    expect(screen.getByText('数据分析智能体')).toBeInTheDocument();
  });

  it('shows tool names', () => {
    render(<CallLogList logs={mockLogs} onLogClick={mockOnLogClick} />);

    expect(screen.getByText('估值计算')).toBeInTheDocument();
    expect(screen.getByText('数据查询')).toBeInTheDocument();
  });

  it('calls onLogClick when log is clicked', () => {
    render(<CallLogList logs={mockLogs} onLogClick={mockOnLogClick} />);

    const logItem = screen.getByText('估值智能体').closest('div[class*="cursor-pointer"]');
    fireEvent.click(logItem!);

    expect(mockOnLogClick).toHaveBeenCalledWith(mockLogs[0]);
  });
});

describe('LogDetailModal', () => {
  const mockOnClose = vi.fn();

  it('does not render when closed', () => {
    render(
      <LogDetailModal
        log={null}
        isOpen={false}
        onClose={mockOnClose}
      />
    );

    expect(screen.queryByText('调用详情')).not.toBeInTheDocument();
  });

  it('renders modal when open', () => {
    render(
      <LogDetailModal
        log={mockLogs[0]}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('调用详情')).toBeInTheDocument();
    expect(screen.getByText('估值智能体')).toBeInTheDocument();
    expect(screen.getByText('估值计算')).toBeInTheDocument();
  });

  it('shows success status', () => {
    render(
      <LogDetailModal
        log={mockLogs[0]}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('成功')).toBeInTheDocument();
  });

  it('shows failure status and error', () => {
    render(
      <LogDetailModal
        log={mockLogs[1]}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('失败')).toBeInTheDocument();
    expect(screen.getByText('错误信息')).toBeInTheDocument();
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <LogDetailModal
        log={mockLogs[0]}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByLabelText('关闭'));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes on Escape key', () => {
    render(
      <LogDetailModal
        log={mockLogs[0]}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(mockOnClose).toHaveBeenCalled();
  });
});
