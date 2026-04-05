import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemorySystem } from '../index';

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

const mockMemories = [
  {
    id: 'mem-1',
    title: '房产估值流程',
    content: '这是关于房产估值的标准流程文档...',
    type: 'procedural' as const,
    importance: 5,
    tags: ['估值', '流程'],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
    createdBy: 'agent-1',
    version: 1,
    associations: {
      memories: ['mem-2'],
      tasks: ['task-1'],
      agents: ['agent-1'],
    },
  },
  {
    id: 'mem-2',
    title: '北京朝阳区房价趋势',
    content: '2024年第一季度朝阳区房价数据分析...',
    type: 'semantic' as const,
    importance: 4,
    tags: ['北京', '房价', '数据'],
    createdAt: '2024-01-14T09:00:00Z',
    updatedAt: '2024-01-14T09:00:00Z',
    createdBy: 'agent-2',
    version: 1,
    associations: {
      memories: ['mem-1'],
      tasks: [],
      agents: ['agent-2'],
    },
  },
  {
    id: 'mem-3',
    title: '用户查询记录',
    content: '用户于2024年1月15日查询了海淀区学区房...',
    type: 'episodic' as const,
    importance: 3,
    tags: ['用户', '查询'],
    createdAt: '2024-01-13T08:00:00Z',
    updatedAt: '2024-01-13T08:00:00Z',
    createdBy: 'agent-3',
    version: 1,
    associations: {
      memories: [],
      tasks: ['task-2'],
      agents: ['agent-3'],
    },
  },
];

jest.mock('../hooks/useMemories', () => ({
  useMemories: () => ({
    data: {
      pages: [
        {
          items: mockMemories,
          total: 3,
          page: 1,
          limit: 20,
          hasMore: false,
        },
      ],
    },
    isLoading: false,
    fetchNextPage: jest.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
  }),
}));

jest.mock('../hooks/useMemoryDetail', () => ({
  useMemoryDetail: (id: string) => ({
    data: mockMemories.find((m) => m.id === id),
    isLoading: false,
  }),
  useMemoryVersions: () => ({
    data: [],
  }),
}));

jest.mock('../hooks/useUpdateImportance', () => ({
  useUpdateImportance: () => ({
    mutate: jest.fn(),
  }),
}));

describe('MemorySystem', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('renders memory system with sidebar', () => {
    render(<MemorySystem />, { wrapper });

    expect(screen.getByText('记忆系统')).toBeInTheDocument();
    expect(screen.getByText('海马体 · 长期知识存储')).toBeInTheDocument();
  });

  it('displays memory cards in card mode', async () => {
    render(<MemorySystem />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('房产估值流程')).toBeInTheDocument();
      expect(screen.getByText('北京朝阳区房价趋势')).toBeInTheDocument();
      expect(screen.getByText('用户查询记录')).toBeInTheDocument();
    });
  });

  it('shows memory type labels correctly', async () => {
    render(<MemorySystem />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('程序性')).toBeInTheDocument();
      expect(screen.getByText('语义')).toBeInTheDocument();
      expect(screen.getByText('情景')).toBeInTheDocument();
    });
  });

  it('displays total memory count', async () => {
    render(<MemorySystem />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('3 条记忆')).toBeInTheDocument();
    });
  });

  it('opens detail drawer when clicking memory card', async () => {
    render(<MemorySystem />, { wrapper });

    const memoryCard = await screen.findByText('房产估值流程');
    fireEvent.click(memoryCard);

    await waitFor(() => {
      expect(screen.getByText('记忆详情')).toBeInTheDocument();
    });
  });

  it('filters by memory type in sidebar', async () => {
    render(<MemorySystem />, { wrapper });

    const proceduralCheckbox = screen.getByLabelText('程序性记忆').closest('label');
    if (proceduralCheckbox) {
      fireEvent.click(proceduralCheckbox);
    }

    await waitFor(() => {
      expect(proceduralCheckbox).toHaveClass('bg-primary/10');
    });
  });

  it('switches between card and graph mode', async () => {
    render(<MemorySystem />, { wrapper });

    const graphButton = screen.getByLabelText('图谱模式');
    fireEvent.click(graphButton);

    await waitFor(() => {
      expect(graphButton).toHaveClass('bg-primary/20');
    });

    const cardButton = screen.getByLabelText('卡片模式');
    fireEvent.click(cardButton);

    await waitFor(() => {
      expect(cardButton).toHaveClass('bg-primary/20');
    });
  });

  it('changes sort order', async () => {
    render(<MemorySystem />, { wrapper });

    const sortSelect = screen.getByRole('combobox');
    fireEvent.change(sortSelect, { target: { value: 'importance' } });

    await waitFor(() => {
      expect(sortSelect).toHaveValue('importance');
    });
  });

  it('displays quick filter buttons', () => {
    render(<MemorySystem />, { wrapper });

    expect(screen.getByText('最近使用')).toBeInTheDocument();
    expect(screen.getByText('高频引用')).toBeInTheDocument();
    expect(screen.getByText('我的收藏')).toBeInTheDocument();
  });

  it('shows star ratings on memory cards', async () => {
    render(<MemorySystem />, { wrapper });

    const stars = screen.getAllByText('★');
    expect(stars.length).toBeGreaterThan(0);
  });

  it('displays tags on memory cards', async () => {
    render(<MemorySystem />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('#估值')).toBeInTheDocument();
      expect(screen.getByText('#流程')).toBeInTheDocument();
    });
  });
});
