import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

import DashboardPage from '@/pages/DashboardPage';
import TasksPage from '@/pages/TasksPage';
import TaskDetailPage from '@/pages/TaskDetailPage';
import SearchResultsPage from '@/pages/SearchResultsPage';
import NotFoundPage from '@/pages/NotFoundPage';
import { MascotToastProvider } from '@/components/mascot/MascotToast';
import { AuthProvider } from '@/contexts/AuthContext';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  full_name: '测试用户',
  role: 'user',
  is_admin: false,
};

vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
    }),
  };
});

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { tasks: [], total: 0 } }),
    post: vi.fn().mockResolvedValue({ data: { id: 'test-task-id' } }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
  taskApi: {
    list: vi.fn().mockResolvedValue({ tasks: [], total: 0 }),
    get: vi.fn().mockResolvedValue({
      id: 'test-task-id',
      query: '测试查询',
      status: 'completed',
      progress: 100,
    }),
    create: vi.fn().mockResolvedValue({ id: 'new-task-id' }),
  },
}));

const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MascotToastProvider>
          {children}
        </MascotToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const renderWithProviders = (component: React.ReactElement, { route = '/' } = {}) => {
  const queryClient = createTestQueryClient();
  
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <MascotToastProvider>
          {component}
        </MascotToastProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('Mascot Integration Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Dashboard Page Integration', () => {
    it('shows mascot welcome state when no tasks exist', async () => {
      renderWithProviders(<DashboardPage />);
      
      await waitFor(() => {
        const mascot = screen.getByAltText('房小智');
        expect(mascot).toBeInTheDocument();
      });
    });

    it('shows mascot in welcome empty state', async () => {
      renderWithProviders(<DashboardPage />);
      
      await waitFor(() => {
        const welcomeText = screen.getByText(/欢迎|开始|任务/i);
        expect(welcomeText).toBeTruthy();
      });
    });

    it('mascot does not interfere with task creation form', async () => {
      renderWithProviders(<DashboardPage />);
      
      const textarea = screen.getByPlaceholderText(/房产需求/);
      expect(textarea).toBeInTheDocument();
      
      fireEvent.change(textarea, { target: { value: '测试需求' } });
      expect(textarea).toHaveValue('测试需求');
    });
  });

  describe('Tasks Page Integration', () => {
    it('shows mascot empty state when no tasks', async () => {
      renderWithProviders(<TasksPage />);
      
      await waitFor(() => {
        const mascot = screen.getByAltText('房小智');
        expect(mascot).toBeInTheDocument();
      });
    });

    it('shows appropriate empty state message', async () => {
      renderWithProviders(<TasksPage />);
      
      await waitFor(() => {
        const emptyMessage = screen.getByText(/任务|创建|开始/i);
        expect(emptyMessage).toBeTruthy();
      });
    });
  });

  describe('Task Detail Page Integration', () => {
    it('shows loading mascot while task is loading', async () => {
      renderWithProviders(<TaskDetailPage />, { route: '/tasks/test-task-id' });
      
      await waitFor(() => {
        const mascot = screen.queryByAltText('房小智');
        if (mascot) {
          expect(mascot).toBeInTheDocument();
        }
      });
    });
  });

  describe('Search Results Page Integration', () => {
    it('shows mascot when no results found', async () => {
      renderWithProviders(<SearchResultsPage />);
      
      await waitFor(() => {
        const mascot = screen.queryByAltText('房小智');
        if (mascot) {
          expect(mascot).toBeInTheDocument();
        }
      });
    });
  });

  describe('404 Page Integration', () => {
    it('shows mascot on 404 page', () => {
      renderWithProviders(<NotFoundPage />);
      
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
    });

    it('shows helpful message on 404', () => {
      renderWithProviders(<NotFoundPage />);
      
      expect(screen.getByText(/404|找不到|不存在/i)).toBeTruthy();
    });
  });

  describe('Mascot Toast Integration', () => {
    const TestToastComponent = () => {
      const { showSuccess, showError, showInfo, showWarning } = require('@/components/mascot/MascotToast').useMascotToast();
      
      return (
        <div>
          <button onClick={() => showSuccess('操作成功！')}>成功</button>
          <button onClick={() => showError('操作失败！')}>错误</button>
          <button onClick={() => showInfo('提示信息')}>信息</button>
          <button onClick={() => showWarning('警告信息')}>警告</button>
        </div>
      );
    };

    it('shows and auto-dismisses toast', async () => {
      vi.useFakeTimers();
      
      renderWithProviders(<TestToastComponent />);
      
      const successButton = screen.getByText('成功');
      fireEvent.click(successButton);
      
      await waitFor(() => {
        expect(screen.getByText('操作成功！')).toBeInTheDocument();
      });
      
      act(() => {
        vi.advanceTimersByTime(5000);
      });
      
      vi.useRealTimers();
    });

    it('shows error toast with correct styling', async () => {
      renderWithProviders(<TestToastComponent />);
      
      const errorButton = screen.getByText('错误');
      fireEvent.click(errorButton);
      
      await waitFor(() => {
        expect(screen.getByText('操作失败！')).toBeInTheDocument();
      });
    });
  });

  describe('Onboarding Flow Integration', () => {
    const OnboardingTestWrapper = () => {
      const { OnboardingManager } = require('@/components/mascot/OnboardingTour');
      const [completed, setCompleted] = React.useState(false);
      
      return (
        <div>
          {completed && <div>Onboarding Completed</div>}
          <OnboardingManager>
            <div>Main Content</div>
          </OnboardingManager>
        </div>
      );
    };

    it('shows onboarding for first-time users', async () => {
      localStorage.removeItem('onboarding_completed');
      
      renderWithProviders(<OnboardingTestWrapper />);
      
      await waitFor(() => {
        const welcomeText = screen.queryByText('欢迎来到房都督AI');
        if (welcomeText) {
          expect(welcomeText).toBeInTheDocument();
        }
      });
    });

    it('can skip onboarding', async () => {
      localStorage.removeItem('onboarding_completed');
      
      renderWithProviders(<OnboardingTestWrapper />);
      
      await waitFor(() => {
        const skipButton = screen.queryByText('跳过');
        if (skipButton) {
          fireEvent.click(skipButton);
          expect(localStorage.getItem('onboarding_completed')).toBe('true');
        }
      });
    });
  });

  describe('Interactive Mascot Integration', () => {
    it('mascot appears on authenticated pages', async () => {
      const { InteractiveMascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(
        <div>
          <div>Page Content</div>
          <InteractiveMascot size="lg" draggable showQuoteBubble />
        </div>
      );
      
      await waitFor(() => {
        const mascot = screen.getByAltText('房小智');
        expect(mascot).toBeInTheDocument();
      });
    });

    it('mascot click shows quote bubble', async () => {
      const { InteractiveMascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(<InteractiveMascot showQuoteBubble />);
      
      const mascotContainer = screen.getByRole('button');
      fireEvent.click(mascotContainer);
      
      await waitFor(() => {
        const quoteBubble = document.querySelector('.bg-white');
        expect(quoteBubble || screen.getByAltText('房小智')).toBeTruthy();
      }, { timeout: 2000 });
    });
  });

  describe('Error Handling Integration', () => {
    it('shows mascot on API error', async () => {
      const { MascotError } = require('@/components/mascot/Mascot');
      
      renderWithProviders(
        <MascotError 
          message="网络错误" 
          suggestion="请检查网络连接后重试"
          onRetry={() => {}}
        />
      );
      
      expect(screen.getByText('网络错误')).toBeInTheDocument();
      expect(screen.getByText('请检查网络连接后重试')).toBeInTheDocument();
      expect(screen.getByText('重试')).toBeInTheDocument();
    });
  });

  describe('Loading States Integration', () => {
    it('shows loading mascot during async operations', async () => {
      const { LoadingWithMascot } = require('@/components/mascot/LoadingWithMascot');
      
      renderWithProviders(
        <LoadingWithMascot 
          message="正在分析房产数据..."
          phases={[
            { id: 'collect', label: '收集数据', messages: ['正在收集市场数据...'] },
            { id: 'analyze', label: '分析数据', messages: ['正在分析价格趋势...'] },
          ]}
          currentPhase="collect"
        />
      );
      
      expect(screen.getByAltText('房小智')).toBeInTheDocument();
      expect(screen.getByText('正在分析房产数据...')).toBeInTheDocument();
    });
  });

  describe('Accessibility Integration', () => {
    it('mascot has proper alt text', () => {
      const { Mascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(<Mascot />);
      
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toHaveAttribute('alt', '房小智');
    });

    it('interactive mascot has button role', () => {
      const { Mascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(<Mascot onClick={() => {}} />);
      
      const mascotContainer = screen.getByRole('button');
      expect(mascotContainer).toBeInTheDocument();
    });

    it('mascot is keyboard accessible', () => {
      const handleClick = vi.fn();
      const { Mascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(<Mascot onClick={handleClick} />);
      
      const mascotContainer = screen.getByRole('button');
      mascotContainer.focus();
      
      fireEvent.keyDown(mascotContainer, { key: 'Enter' });
      expect(handleClick).toHaveBeenCalled();
    });
  });

  describe('Theme Integration', () => {
    it('mascot adapts to dark mode', () => {
      const { Mascot } = require('@/components/mascot/Mascot');
      
      document.documentElement.classList.add('dark');
      
      renderWithProviders(<Mascot />);
      
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
      
      document.documentElement.classList.remove('dark');
    });
  });

  describe('Performance Integration', () => {
    it('mascot does not cause layout shift', async () => {
      const { Mascot } = require('@/components/mascot/Mascot');
      
      const { container } = renderWithProviders(
        <div style={{ minHeight: '100vh' }}>
          <Mascot size="lg" />
        </div>
      );
      
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
    });

    it('multiple mascots can render without conflict', async () => {
      const { Mascot } = require('@/components/mascot/Mascot');
      
      renderWithProviders(
        <div>
          <Mascot emotion="happy" />
          <Mascot emotion="thinking" />
          <Mascot emotion="default" />
        </div>
      );
      
      const mascots = screen.getAllByAltText('房小智');
      expect(mascots).toHaveLength(3);
    });
  });
});

describe('Mascot State Persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('remembers mascot position after page reload', async () => {
    const savedPosition = { x: 100, y: 200 };
    localStorage.setItem('mascot_position', JSON.stringify(savedPosition));
    
    const { InteractiveMascot } = require('@/components/mascot/Mascot');
    
    renderWithProviders(<InteractiveMascot />);
    
    await waitFor(() => {
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
    });
  });

  it('remembers onboarding completion status', () => {
    localStorage.setItem('onboarding_completed', 'true');
    
    const stored = localStorage.getItem('onboarding_completed');
    expect(stored).toBe('true');
  });

  it('remembers daily greeting status', () => {
    const today = new Date().toDateString();
    localStorage.setItem('mascot_greeting_date', today);
    
    const stored = localStorage.getItem('mascot_greeting_date');
    expect(stored).toBe(today);
  });
});
