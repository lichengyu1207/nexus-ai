import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TalentMarketplace from '../index';
import { TalentCard } from '../components/TalentCard';
import { TalentList } from '../components/TalentList';
import { TalentFilters } from '../components/TalentFilters';
import { RecruitmentForm } from '../components/RecruitmentForm';
import { InviteModal } from '../components/InviteModal';
import type { Talent, TalentFilters } from '../types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockTalents: Talent[] = [
  {
    id: '1',
    type: 'agent',
    name: '估值智能体',
    title: '房产估值专家',
    skills: ['房产估值', '数据分析', '报告生成'],
    rating: 4.8,
    reviewCount: 156,
    price: 200,
    verified: true,
    availability: 'fulltime',
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    type: 'human',
    name: '张三',
    title: '资深房产分析师',
    skills: ['市场调研', '风险评估', '投资顾问'],
    rating: 4.5,
    reviewCount: 89,
    price: 350,
    verified: true,
    availability: 'parttime',
    location: '北京',
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    type: 'agent',
    name: '数据挖掘助手',
    title: '数据分析与可视化',
    skills: ['数据分析', 'Python', '可视化'],
    rating: 4.2,
    reviewCount: 45,
    price: 150,
    verified: false,
    availability: 'ondemand',
    createdAt: new Date().toISOString(),
  },
];

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('TalentCard', () => {
  const mockOnClick = vi.fn();
  const mockOnInvite = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders talent information correctly', () => {
    render(
      <TalentCard
        talent={mockTalents[0]}
        onClick={mockOnClick}
        onInvite={mockOnInvite}
      />
    );

    expect(screen.getByText('估值智能体')).toBeInTheDocument();
    expect(screen.getByText('房产估值专家')).toBeInTheDocument();
    expect(screen.getByText('智能体')).toBeInTheDocument();
    expect(screen.getByText('房产估值')).toBeInTheDocument();
  });

  it('shows verified badge for verified talents', () => {
    const { container } = render(
      <TalentCard talent={mockTalents[0]} onClick={mockOnClick} onInvite={mockOnInvite} />
    );

    expect(container.querySelector('.text-blue-400')).toBeInTheDocument();
  });

  it('displays rating stars', () => {
    render(
      <TalentCard talent={mockTalents[0]} onClick={mockOnClick} onInvite={mockOnInvite} />
    );

    expect(screen.getByText('(4.8)')).toBeInTheDocument();
  });

  it('calls onClick when card is clicked', () => {
    render(
      <TalentCard talent={mockTalents[0]} onClick={mockOnClick} onInvite={mockOnInvite} />
    );

    const card = screen.getByText('估值智能体').closest('div');
    if (card) {
      fireEvent.click(card);
    }

    expect(mockOnClick).toHaveBeenCalled();
  });

  it('calls onInvite when invite button is clicked', () => {
    render(
      <TalentCard talent={mockTalents[0]} onClick={mockOnClick} onInvite={mockOnInvite} />
    );

    const inviteButton = screen.getByText('发送邀约');
    fireEvent.click(inviteButton);

    expect(mockOnInvite).toHaveBeenCalled();
    expect(mockOnClick).not.toHaveBeenCalled();
  });
});

describe('TalentList', () => {
  const mockOnTalentClick = vi.fn();
  const mockOnInvite = vi.fn();
  const mockOnLoadMore = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner when loading', () => {
    render(
      <TalentList
        talents={[]}
        isLoading={true}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onTalentClick={mockOnTalentClick}
        onInvite={mockOnInvite}
      />
    );

    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('shows empty state when no talents', () => {
    render(
      <TalentList
        talents={[]}
        isLoading={false}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onTalentClick={mockOnTalentClick}
        onInvite={mockOnInvite}
      />
    );

    expect(screen.getByText('暂无匹配的人才')).toBeInTheDocument();
  });

  it('renders talents correctly', () => {
    render(
      <TalentList
        talents={mockTalents}
        isLoading={false}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onTalentClick={mockOnTalentClick}
        onInvite={mockOnInvite}
      />
    );

    expect(screen.getByText('估值智能体')).toBeInTheDocument();
    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('数据挖掘助手')).toBeInTheDocument();
  });
});

describe('TalentFilters', () => {
  const mockOnFiltersChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders filter sections', () => {
    render(
      <TalentFilters filters={{}} onFiltersChange={mockOnFiltersChange} />
    );

    expect(screen.getByText('筛选条件')).toBeInTheDocument();
    expect(screen.getByText('技能标签')).toBeInTheDocument();
    expect(screen.getByText('领域')).toBeInTheDocument();
  });

  it('toggles skill selection', () => {
    render(
      <TalentFilters filters={{}} onFiltersChange={mockOnFiltersChange} />
    );

    const skillButton = screen.getByText('数据分析');
    fireEvent.click(skillButton);

    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({
        skills: ['数据分析'],
      })
    );
  });

  it('clears all filters', () => {
    render(
      <TalentFilters
        filters={{ skills: ['数据分析'], ratingMin: 4 }}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    const clearButton = screen.getByText('清除全部');
    fireEvent.click(clearButton);

    expect(mockOnFiltersChange).toHaveBeenCalledWith({});
  });

  it('expands and collapses sections', () => {
    render(
      <TalentFilters filters={{}} onFiltersChange={mockOnFiltersChange} />
    );

    const priceHeader = screen.getByText('价格范围').closest('button');
    if (priceHeader) {
      fireEvent.click(priceHeader);
    }

    expect(screen.getByText('¥0-100')).toBeInTheDocument();
  });
});

describe('RecruitmentForm', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders form when open', () => {
    render(
      <RecruitmentForm
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('发布招募')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入招募标题')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <RecruitmentForm
        isOpen={false}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.queryByText('发布招募')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <RecruitmentForm
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const closeButton = screen.getByLabelText('关闭');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('submits form with correct data', async () => {
    render(
      <RecruitmentForm
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const titleInput = screen.getByPlaceholderText('输入招募标题');
    fireEvent.change(titleInput, { target: { value: '测试招募' } });

    const descInput = screen.getByPlaceholderText('描述您的招募需求');
    fireEvent.change(descInput, { target: { value: '这是一个测试招募' } });

    const submitButton = screen.getByText('发布招募');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });
});

describe('InviteModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal when open', () => {
    render(
      <InviteModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        talent={mockTalents[0]}
      />
    );

    expect(screen.getByText('发送邀约')).toBeInTheDocument();
    expect(screen.getByText('估值智能体')).toBeInTheDocument();
  });

  it('shows talent price reference', () => {
    render(
      <InviteModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        talent={mockTalents[0]}
      />
    );

    expect(screen.getByText('¥200/小时')).toBeInTheDocument();
  });

  it('submits invitation with correct data', async () => {
    render(
      <InviteModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        talent={mockTalents[0]}
      />
    );

    const titleInput = screen.getByPlaceholderText('输入项目标题');
    fireEvent.change(titleInput, { target: { value: '测试项目' } });

    const descInput = screen.getByPlaceholderText('描述项目需求');
    fireEvent.change(descInput, { target: { value: '测试项目描述' } });

    const budgetInput = screen.getByPlaceholderText('1');
    fireEvent.change(budgetInput, { target: { value: '1000' } });

    const submitButton = screen.getByText('发送邀约');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '测试项目',
          description: '测试项目描述',
          budget: 1000,
          toTalentId: '1',
        })
      );
    });
  });
});

describe('TalentMarketplace', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();

    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/talents')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              talents: mockTalents,
              total: 3,
              page: 1,
              limit: 20,
              hasMore: false,
            }),
        });
      }
      if (url.includes('/api/recruitments')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              recruitments: [],
              total: 0,
              page: 1,
              limit: 20,
              hasMore: false,
            }),
        });
      }
      if (url.includes('/api/bids')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              bids: [],
              total: 0,
              page: 1,
              limit: 20,
              hasMore: false,
            }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  it('renders main layout', async () => {
    render(<TalentMarketplace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('人才市场')).toBeInTheDocument();
    });
  });

  it('shows navigation tabs', async () => {
    render(<TalentMarketplace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('人才库')).toBeInTheDocument();
      expect(screen.getByText('技能市场')).toBeInTheDocument();
      expect(screen.getByText('我的招募')).toBeInTheDocument();
      expect(screen.getByText('我的投标')).toBeInTheDocument();
    });
  });

  it('switches between views', async () => {
    render(<TalentMarketplace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('人才库')).toBeInTheDocument();
    });

    const skillsTab = screen.getByText('技能市场');
    fireEvent.click(skillsTab);

    await waitFor(() => {
      expect(screen.getByText('技能市场功能开发中...')).toBeInTheDocument();
    });
  });

  it('shows talent list', async () => {
    render(<TalentMarketplace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('估值智能体')).toBeInTheDocument();
    });
  });

  it('opens recruitment form when button is clicked', async () => {
    render(<TalentMarketplace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('发布招募')).toBeInTheDocument();
    });

    const createButton = screen.getAllByText('发布招募')[0];
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入招募标题')).toBeInTheDocument();
    });
  });
});
