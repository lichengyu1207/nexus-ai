import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../index';

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

describe('Dashboard', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('renders loading state initially', () => {
    render(
      <wrapper>
        <Dashboard />
      </wrapper>
    );

    expect(screen.getByText(/加载/i)).toBeInTheDocument();
  });

  it('renders dashboard content after loading', async () => {
    queryClient.setQueryData(['dashboard'], {
      health: 85,
      quickStats: {
        totalAgents: 6,
        activeTasks: 3,
        completedToday: 12,
      },
      recentTasks: [
        {
          id: 'task-1',
          name: '测试任务',
          progress: 0.5,
          currentAgent: '兵部',
          estimatedEnd: '10分钟',
        },
      ],
      crossEndEvents: [],
      agentTopology: {
        nodes: [],
        links: [],
      },
    });

    render(
      <wrapper>
        <Dashboard />
      </wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('测试任务')).toBeInTheDocument();
    });
  });

  it('renders health indicator', async () => {
    queryClient.setQueryData(['dashboard'], {
      health: 85,
      quickStats: { totalAgents: 6, activeTasks: 3, completedToday: 12 },
      recentTasks: [],
      crossEndEvents: [],
      agentTopology: { nodes: [], links: [] },
    });

    render(
      <wrapper>
        <Dashboard />
      </wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('renders quick action buttons', async () => {
    queryClient.setQueryData(['dashboard'], {
      health: 85,
      quickStats: { totalAgents: 6, activeTasks: 3, completedToday: 12 },
      recentTasks: [],
      crossEndEvents: [],
      agentTopology: { nodes: [], links: [] },
    });

    render(
      <wrapper>
        <Dashboard />
      </wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('新建任务')).toBeInTheDocument();
      expect(screen.getByText('记忆系统')).toBeInTheDocument();
      expect(screen.getByText('智能体工坊')).toBeInTheDocument();
    });
  });
});
