import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentDebugConsole from '../index';
import { AgentSelector } from '../components/AgentSelector';
import { LogViewer } from '../components/LogViewer';
import { DebugControlBar } from '../components/DebugControlBar';
import type { Agent, LogEntry } from '../types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: '估值智能体',
    type: 'valuation',
    status: 'running',
    currentTask: '房产估值任务',
    lastActivity: new Date().toISOString(),
    metrics: {
      totalExecutions: 100,
      successRate: 0.95,
      avgExecutionTime: 2.5,
    },
    variables: [],
  },
  {
    id: 'agent-2',
    name: '报告生成智能体',
    type: 'report',
    status: 'stopped',
    lastActivity: new Date(Date.now() - 3600000).toISOString(),
    metrics: {
      totalExecutions: 50,
      successRate: 0.9,
      avgExecutionTime: 5.0,
    },
    variables: [],
  },
];

const mockLogs: LogEntry[] = [
  {
    id: 'log-1',
    timestamp: new Date().toISOString(),
    level: 'info',
    message: '智能体启动成功',
    source: 'system',
  },
  {
    id: 'log-2',
    timestamp: new Date().toISOString(),
    level: 'debug',
    message: '正在处理数据...',
    source: 'processor',
  },
];

describe('AgentDebugConsole', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders agent selector', () => {
    render(
      <wrapper>
        <AgentDebugConsole />
      </wrapper>
    );

    expect(screen.getByText('选择智能体')).toBeInTheDocument();
  });

  it('renders log viewer by default', () => {
    render(
      <wrapper>
        <AgentDebugConsole />
      </wrapper>
    );

    expect(screen.getByText('日志')).toBeInTheDocument();
  });

  it('renders view tabs', () => {
    render(
      <wrapper>
        <AgentDebugConsole />
      </wrapper>
    );

    expect(screen.getByText('调用栈')).toBeInTheDocument();
    expect(screen.getByText('变量')).toBeInTheDocument();
    expect(screen.getByText('火焰图')).toBeInTheDocument();
  });
});

describe('AgentSelector', () => {
  const mockOnSelect = vi.fn();
  const mockOnStart = vi.fn();
  const mockOnStop = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders agents list', () => {
    render(
      <wrapper>
        <AgentSelector
          agents={mockAgents}
          selectedAgentId={null}
          onSelect={mockOnSelect}
          onStart={mockOnStart}
          onStop={mockOnStop}
        />
      </wrapper>
    );

    expect(screen.getByText('选择智能体')).toBeInTheDocument();
  });

  it('shows selected agent', () => {
    render(
      <wrapper>
        <AgentSelector
          agents={mockAgents}
          selectedAgentId="agent-1"
          onSelect={mockOnSelect}
          onStart={mockOnStart}
          onStop={mockOnStop}
        />
      </wrapper>
    );

    expect(screen.getByText('估值智能体')).toBeInTheDocument();
  });
});

describe('LogViewer', () => {
  it('renders logs', () => {
    render(
      <wrapper>
        <LogViewer logs={mockLogs} />
      </wrapper>
    );

    expect(screen.getByText('智能体启动成功')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(
      <wrapper>
        <LogViewer logs={[]} />
      </wrapper>
    );

    expect(screen.getByText('暂无日志')).toBeInTheDocument();
  });

  it('filters by level', () => {
    render(
      <wrapper>
        <LogViewer logs={mockLogs} />
      </wrapper>
    );

    const debugButton = screen.getByText('DEBUG');
    fireEvent.click(debugButton);

    expect(screen.getByText('正在处理数据...')).toBeInTheDocument();
  });
});

describe('DebugControlBar', () => {
  const mockOnPause = vi.fn();
  const mockOnResume = vi.fn();

  it('renders control buttons', () => {
    render(
      <wrapper>
        <DebugControlBar
          onPause={mockOnPause}
          onResume={mockOnResume}
          isPaused={false}
        />
      </wrapper>
    );

    expect(screen.getByTitle('暂停')).toBeInTheDocument();
    expect(screen.getByTitle('继续')).toBeInTheDocument();
  });

  it('shows paused state', () => {
    render(
      <wrapper>
        <DebugControlBar
          onPause={mockOnPause}
          onResume={mockOnResume}
          isPaused={true}
        />
      </wrapper>
    );

    const resumeButton = screen.getByTitle('恢复');
    expect(resumeButton).toBeInTheDocument();
  });
});
