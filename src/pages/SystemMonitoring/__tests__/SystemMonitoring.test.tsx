import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SystemMonitoringPage from '../index';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

vi.mock('../hooks/useMetrics', () => ({
  useMetrics: () => ({
    data: null,
    summaries: [
      { name: 'cpu', value: 45, unit: '%', trend: 'stable', trendValue: 0, status: 'normal' },
      { name: 'memory', value: 65, unit: '%', trend: 'up', trendValue: 5, status: 'normal' },
      { name: 'throughput', value: 120, unit: '个/秒', trend: 'up', trendValue: 10, status: 'normal' },
      { name: 'latency', value: 85, unit: 'ms', trend: 'stable', trendValue: 0, status: 'normal' },
    ],
    isLoading: false,
    refresh: vi.fn(),
  }),
}));

vi.mock('../hooks/useAlertRules', () => ({
  useAlertRules: () => ({
    rules: [
      {
        id: '1',
        name: 'CPU 使用率告警',
        metric: 'agent.cpu.usage',
        condition: '>',
        threshold: 80,
        duration: 60,
        channels: [],
        enabled: true,
        silenceMinutes: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ],
    isLoading: false,
    createRule: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn(),
    toggleRule: vi.fn(),
  }),
}));

vi.mock('../hooks/useAlertHistory', () => ({
  useAlertHistory: () => ({
    events: [
      {
        id: '1',
        ruleId: '1',
        ruleName: 'CPU 使用率告警',
        severity: 'warning',
        status: 'firing',
        triggeredAt: new Date().toISOString(),
        value: 85,
        threshold: 80,
      },
    ],
    isLoading: false,
    refetch: vi.fn(),
  }),
}));

vi.mock('../hooks/useHealthChecks', () => ({
  useHealthChecks: () => ({
    checks: [
      {
        component: 'agent-cluster',
        status: 'healthy',
        latency: 50,
        lastCheck: new Date().toISOString(),
      },
      {
        component: 'database',
        status: 'healthy',
        latency: 10,
        lastCheck: new Date().toISOString(),
      },
    ],
    isLoading: false,
    triggerCheck: vi.fn(),
    isTriggering: false,
    getOverallStatus: () => 'healthy',
  }),
}));

vi.mock('../hooks/useNotificationChannels', () => ({
  useNotificationChannels: () => ({
    channels: [
      {
        id: '1',
        type: 'email',
        name: '运维邮件组',
        config: { recipients: ['ops@example.com'] },
        enabled: true,
      },
    ],
    isLoading: false,
    testChannel: vi.fn(),
    isTesting: false,
  }),
}));

vi.mock('../hooks/useAlertWebSocket', () => ({
  useAlertWebSocket: () => ({
    isConnected: true,
    reconnect: vi.fn(),
    disconnect: vi.fn(),
  }),
}));

describe('SystemMonitoringPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders monitoring page with tabs', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    expect(screen.getByText('监控仪表盘')).toBeInTheDocument();
    expect(screen.getByText('告警规则')).toBeInTheDocument();
    expect(screen.getByText('告警历史')).toBeInTheDocument();
    expect(screen.getByText('健康检查')).toBeInTheDocument();
    expect(screen.getByText('通知渠道')).toBeInTheDocument();
  });

  it('shows dashboard tab by default', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    expect(screen.getByText('CPU 使用率')).toBeInTheDocument();
    expect(screen.getByText('内存使用率')).toBeInTheDocument();
  });

  it('switches to rules tab when clicked', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('告警规则'));
    expect(screen.getByText('创建规则')).toBeInTheDocument();
  });

  it('switches to history tab when clicked', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('告警历史'));
    expect(screen.getByText('CPU 使用率告警')).toBeInTheDocument();
  });

  it('switches to health tab when clicked', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('健康检查'));
    expect(screen.getByText('整体状态:')).toBeInTheDocument();
  });

  it('switches to channels tab when clicked', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('通知渠道'));
    expect(screen.getByText('运维邮件组')).toBeInTheDocument();
  });

  it('shows metric cards on dashboard', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    expect(screen.getByText('任务吞吐量')).toBeInTheDocument();
    expect(screen.getByText('API P99 延迟')).toBeInTheDocument();
  });

  it('shows create rule button on rules tab', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('告警规则'));
    const createButton = screen.getByText('创建规则');
    expect(createButton).toBeInTheDocument();
  });

  it('shows manual check button on health tab', () => {
    render(<SystemMonitoringPage />, { wrapper });
    
    fireEvent.click(screen.getByText('健康检查'));
    expect(screen.getByText('手动检查')).toBeInTheDocument();
  });
});
