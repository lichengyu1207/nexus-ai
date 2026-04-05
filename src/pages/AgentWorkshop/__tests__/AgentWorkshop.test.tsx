import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentWorkshop } from '../index';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockAgents = [
  {
    id: 'agent-1',
    name: '兵部',
    department: 'liu' as const,
    description: '负责军事相关任务处理',
    currentTasks: 3,
    status: 'healthy' as const,
  },
  {
    id: 'agent-2',
    name: '户部',
    department: 'liu' as const,
    description: '负责财务和人口管理',
    currentTasks: 5,
    status: 'busy' as const,
  },
  {
    id: 'agent-3',
    name: '中书省',
    department: 'san' as const,
    description: '负责决策和指令下达',
    currentTasks: 0,
    status: 'error' as const,
  },
];

const mockWorkflowData = {
  nodes: [
    { id: 'node-1', type: 'start', label: '开始', status: 'completed' as const, position: { x: 0, y: 0 } },
    { id: 'node-2', type: 'agent', label: '处理请求', status: 'running' as const, position: { x: 200, y: 0 } },
    { id: 'node-3', type: 'end', label: '结束', status: 'pending' as const, position: { x: 400, y: 0 } },
  ],
  edges: [
    { id: 'edge-1', source: 'node-1', target: 'node-2', animated: true },
    { id: 'edge-2', source: 'node-2', target: 'node-3', animated: false },
  ],
};

const mockTools = [
  {
    id: 'tool-1',
    name: 'GIS查询',
    description: '地理信息查询工具',
    callCount: 150,
    lastCalled: '2024-01-15T10:30:00Z',
    enabled: true,
  },
  {
    id: 'tool-2',
    name: '估值计算',
    description: '房产估值计算工具',
    callCount: 89,
    lastCalled: '2024-01-15T09:15:00Z',
    enabled: false,
  },
];

const mockLogs = {
  logs: [
    {
      id: 'log-1',
      taskId: 'task-12345',
      startTime: '2024-01-15T10:00:00Z',
      duration: 2500,
      status: 'success' as const,
      outputSummary: '任务执行成功，返回估值结果',
    },
    {
      id: 'log-2',
      taskId: 'task-67890',
      startTime: '2024-01-15T09:30:00Z',
      duration: 1500,
      status: 'failure' as const,
      outputSummary: '任务执行失败',
      error: '连接超时',
    },
  ],
  total: 2,
  page: 1,
  limit: 20,
  hasMore: false,
};

jest.mock('../hooks/useAgents', () => ({
  useAgents: () => ({
    data: mockAgents,
    isLoading: false,
  }),
  useAgent: (id: string) => ({
    data: mockAgents.find((a) => a.id === id),
    isLoading: false,
  }),
}));

jest.mock('../hooks/useWorkflowData', () => ({
  useWorkflowData: () => ({
    data: mockWorkflowData,
    isLoading: false,
  }),
  useNodeDetail: () => ({
    data: mockWorkflowData.nodes[0],
    isLoading: false,
  }),
}));

jest.mock('../hooks/useTools', () => ({
  useTools: () => ({
    data: mockTools,
    isLoading: false,
  }),
  useUpdateToolPermission: () => ({
    mutate: jest.fn(),
  }),
}));

jest.mock('../hooks/useRunLogs', () => ({
  useRunLogs: () => ({
    data: { pages: [mockLogs] },
    isLoading: false,
    fetchNextPage: jest.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
  }),
}));

describe('AgentWorkshop', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('renders agent list with correct items', () => {
    render(<AgentWorkshop />, { wrapper });

    expect(screen.getByText('智能体工坊')).toBeInTheDocument();
    expect(screen.getByText('兵部')).toBeInTheDocument();
    expect(screen.getByText('户部')).toBeInTheDocument();
    expect(screen.getByText('中书省')).toBeInTheDocument();
  });

  it('shows status indicators correctly', () => {
    render(<AgentWorkshop />, { wrapper });

    const healthyBadge = screen.getByText('健康');
    const busyBadge = screen.getByText('繁忙');
    const errorBadge = screen.getByText('异常');

    expect(healthyBadge).toBeInTheDocument();
    expect(busyBadge).toBeInTheDocument();
    expect(errorBadge).toBeInTheDocument();
  });

  it('groups agents by department', () => {
    render(<AgentWorkshop />, { wrapper });

    expect(screen.getByText('三省')).toBeInTheDocument();
    expect(screen.getByText('六部')).toBeInTheDocument();
  });

  it('shows empty state when no agent is selected', () => {
    render(<AgentWorkshop />, { wrapper });

    expect(screen.getByText('选择一个智能体')).toBeInTheDocument();
    expect(screen.getByText('从左侧列表中选择一个智能体查看详情')).toBeInTheDocument();
  });

  it('selects agent and shows detail view', async () => {
    render(<AgentWorkshop />, { wrapper });

    const agentCard = screen.getByRole('button', { name: /智能体: 兵部/ });
    fireEvent.click(agentCard);

    await waitFor(() => {
      expect(screen.getByText('工作流')).toBeInTheDocument();
      expect(screen.getByText('工具权限')).toBeInTheDocument();
      expect(screen.getByText('运行日志')).toBeInTheDocument();
    });
  });

  it('switches between tabs', async () => {
    render(<AgentWorkshop />, { wrapper });

    const agentCard = screen.getByRole('button', { name: /智能体: 兵部/ });
    fireEvent.click(agentCard);

    await waitFor(() => {
      expect(screen.getByText('工作流')).toBeInTheDocument();
    });

    const toolsTab = screen.getByRole('button', { name: /工具权限/ });
    fireEvent.click(toolsTab);

    await waitFor(() => {
      expect(screen.getByText('GIS查询')).toBeInTheDocument();
      expect(screen.getByText('估值计算')).toBeInTheDocument();
    });

    const logsTab = screen.getByRole('button', { name: /运行日志/ });
    fireEvent.click(logsTab);

    await waitFor(() => {
      expect(screen.getByText('任务执行成功，返回估值结果')).toBeInTheDocument();
    });
  });

  it('filters agents by search term', () => {
    render(<AgentWorkshop />, { wrapper });

    const searchInput = screen.getByPlaceholderText('搜索智能体...');
    fireEvent.change(searchInput, { target: { value: '兵部' } });

    expect(screen.getByText('兵部')).toBeInTheDocument();
    expect(screen.queryByText('户部')).not.toBeInTheDocument();
  });

  it('filters agents by status', () => {
    render(<AgentWorkshop />, { wrapper });

    const statusSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(statusSelect, { target: { value: 'healthy' } });

    expect(screen.getByText('兵部')).toBeInTheDocument();
    expect(screen.queryByText('中书省')).not.toBeInTheDocument();
  });

  it('filters agents by department', () => {
    render(<AgentWorkshop />, { wrapper });

    const departmentSelect = screen.getAllByRole('combobox')[1];
    fireEvent.change(departmentSelect, { target: { value: 'san' } });

    expect(screen.getByText('中书省')).toBeInTheDocument();
    expect(screen.queryByText('兵部')).not.toBeInTheDocument();
  });

  it('shows task count for each agent', () => {
    render(<AgentWorkshop />, { wrapper });

    expect(screen.getByText('3 任务')).toBeInTheDocument();
    expect(screen.getByText('5 任务')).toBeInTheDocument();
    expect(screen.getByText('0 任务')).toBeInTheDocument();
  });

  it('displays agent count summary', () => {
    render(<AgentWorkshop />, { wrapper });

    expect(screen.getByText(/共.*个智能体/)).toBeInTheDocument();
  });
});
