import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import {
  Mascot,
  MascotWithAnimation,
  MascotEmptyState,
  MascotLoading,
  MascotSuccess,
  MascotError,
  MascotWelcome,
  MascotHelper,
  InteractiveMascot,
} from '@/components/mascot/Mascot';
import { MascotToastProvider, useMascotToast } from '@/components/mascot/MascotToast';
import { EmptyStateWithMascot } from '@/components/mascot/EmptyStateWithMascot';
import { LoadingWithMascot } from '@/components/mascot/LoadingWithMascot';
import { OnboardingTour, OnboardingManager } from '@/components/mascot/OnboardingTour';
import { ActiveReminder, IdleReminder, DailyGreeting } from '@/components/mascot/ActiveReminder';

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <MascotToastProvider>
        {component}
      </MascotToastProvider>
    </BrowserRouter>
  );
};

describe('Mascot', () => {
  it('renders with default props', () => {
    renderWithRouter(<Mascot />);
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });

  it('renders with different emotions', () => {
    const emotions = ['default', 'thinking', 'happy', 'confused', 'surprised', 'comforting'] as const;
    
    emotions.forEach((emotion) => {
      const { unmount } = renderWithRouter(<Mascot emotion={emotion} />);
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with different poses', () => {
    const poses = ['standing', 'sitting', 'waving', 'pointing'] as const;
    
    poses.forEach((pose) => {
      const { unmount } = renderWithRouter(<Mascot pose={pose} />);
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
      unmount();
    });
  });

  it('renders with different sizes', () => {
    const sizes = ['sm', 'md', 'lg', 'xl'] as const;
    
    sizes.forEach((size) => {
      const { unmount } = renderWithRouter(<Mascot size={size} />);
      const mascot = screen.getByAltText('房小智');
      expect(mascot).toBeInTheDocument();
      unmount();
    });
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    renderWithRouter(<Mascot onClick={handleClick} />);
    
    const mascotContainer = screen.getByRole('button');
    fireEvent.click(mascotContainer);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not have button role when onClick is not provided', () => {
    renderWithRouter(<Mascot />);
    const mascotContainer = screen.queryByRole('button');
    expect(mascotContainer).not.toBeInTheDocument();
  });

  it('shows fallback when image fails to load', async () => {
    renderWithRouter(<Mascot emotion="default" />);
    const mascot = screen.getByAltText('房小智');
    
    fireEvent.error(mascot);
    
    await waitFor(() => {
      expect(screen.getByText('🏠')).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    renderWithRouter(<Mascot className="custom-class" />);
    const container = screen.getByAltText('房小智').parentElement;
    expect(container).toHaveClass('custom-class');
  });
});

describe('MascotWithAnimation', () => {
  it('renders with breathe animation', () => {
    renderWithRouter(<MascotWithAnimation animationType="breathe" />);
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });

  it('renders with float animation', () => {
    renderWithRouter(<MascotWithAnimation animationType="float" />);
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });

  it('renders with no animation', () => {
    renderWithRouter(<MascotWithAnimation animationType="none" />);
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });
});

describe('MascotEmptyState', () => {
  it('renders with title', () => {
    renderWithRouter(<MascotEmptyState title="暂无数据" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('renders with description', () => {
    renderWithRouter(
      <MascotEmptyState title="暂无数据" description="还没有任何记录" />
    );
    expect(screen.getByText('还没有任何记录')).toBeInTheDocument();
  });

  it('renders with action button', () => {
    const handleAction = vi.fn();
    renderWithRouter(
      <MascotEmptyState
        title="暂无数据"
        action={<button onClick={handleAction}>添加</button>}
      />
    );
    
    const button = screen.getByText('添加');
    fireEvent.click(button);
    expect(handleAction).toHaveBeenCalled();
  });
});

describe('MascotLoading', () => {
  it('renders with default message', () => {
    renderWithRouter(<MascotLoading />);
    expect(screen.getByText('正在处理...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    renderWithRouter(<MascotLoading message="正在分析..." />);
    expect(screen.getByText('正在分析...')).toBeInTheDocument();
  });
});

describe('MascotSuccess', () => {
  it('renders with default message', () => {
    renderWithRouter(<MascotSuccess />);
    expect(screen.getByText('操作成功！')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    renderWithRouter(<MascotSuccess message="任务完成！" />);
    expect(screen.getByText('任务完成！')).toBeInTheDocument();
  });

  it('calls onComplete after duration', async () => {
    vi.useFakeTimers();
    const handleComplete = vi.fn();
    
    renderWithRouter(<MascotSuccess onComplete={handleComplete} duration={1000} />);
    
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    
    expect(handleComplete).toHaveBeenCalled();
    vi.useRealTimers();
  });
});

describe('MascotError', () => {
  it('renders with default message', () => {
    renderWithRouter(<MascotError />);
    expect(screen.getByText('出错了')).toBeInTheDocument();
  });

  it('renders with custom message and suggestion', () => {
    renderWithRouter(
      <MascotError message="网络错误" suggestion="请检查网络连接" />
    );
    expect(screen.getByText('网络错误')).toBeInTheDocument();
    expect(screen.getByText('请检查网络连接')).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const handleRetry = vi.fn();
    renderWithRouter(<MascotError onRetry={handleRetry} />);
    
    const retryButton = screen.getByText('重试');
    fireEvent.click(retryButton);
    expect(handleRetry).toHaveBeenCalled();
  });
});

describe('MascotWelcome', () => {
  it('renders welcome message', () => {
    renderWithRouter(<MascotWelcome />);
    expect(screen.getByText(/你好/)).toBeInTheDocument();
  });

  it('renders with username', () => {
    renderWithRouter(<MascotWelcome username="测试用户" />);
    expect(screen.getByText(/测试用户/)).toBeInTheDocument();
  });

  it('renders start button when onStart is provided', () => {
    const handleStart = vi.fn();
    renderWithRouter(<MascotWelcome onStart={handleStart} />);
    
    const startButton = screen.getByText('开始使用');
    fireEvent.click(startButton);
    expect(handleStart).toHaveBeenCalled();
  });
});

describe('MascotHelper', () => {
  it('renders with tip', () => {
    renderWithRouter(<MascotHelper tip="这是一个提示" />);
    expect(screen.getByText('这是一个提示')).toBeInTheDocument();
  });

  it('calls onDismiss when close button is clicked', () => {
    const handleDismiss = vi.fn();
    renderWithRouter(<MascotHelper tip="这是一个提示" onDismiss={handleDismiss} />);
    
    const closeButton = screen.getByLabelText('关闭');
    fireEvent.click(closeButton);
    expect(handleDismiss).toHaveBeenCalled();
  });

  it('dismisses when mascot is clicked', () => {
    const handleDismiss = vi.fn();
    renderWithRouter(<MascotHelper tip="这是一个提示" onDismiss={handleDismiss} />);
    
    const mascot = screen.getByAltText('房小智');
    fireEvent.click(mascot);
    expect(handleDismiss).toHaveBeenCalled();
  });
});

describe('InteractiveMascot', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders interactive mascot', () => {
    renderWithRouter(<InteractiveMascot />);
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });

  it('shows quote bubble on click', async () => {
    renderWithRouter(<InteractiveMascot showQuoteBubble />);
    
    const mascotContainer = screen.getByRole('button');
    fireEvent.click(mascotContainer);
    
    await waitFor(() => {
      const quoteBubble = document.querySelector('.bg-white.dark\\:bg-gray-800');
      expect(quoteBubble).toBeTruthy();
    }, { timeout: 2000 });
  });

  it('triggers easter egg on triple click', async () => {
    vi.useFakeTimers();
    renderWithRouter(<InteractiveMascot showQuoteBubble />);
    
    const mascotContainer = screen.getByRole('button');
    
    act(() => {
      fireEvent.click(mascotContainer);
      fireEvent.click(mascotContainer);
      fireEvent.click(mascotContainer);
    });
    
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    
    await waitFor(() => {
      const sparkle = screen.getByText('✨');
      expect(sparkle).toBeInTheDocument();
    }, { timeout: 3000 });
    
    vi.useRealTimers();
  });

  it('saves position to localStorage after drag', async () => {
    renderWithRouter(<InteractiveMascot draggable />);
    
    const mascot = screen.getByAltText('房小智');
    expect(mascot).toBeInTheDocument();
  });
});

describe('EmptyStateWithMascot', () => {
  it('renders welcome type', () => {
    renderWithRouter(<EmptyStateWithMascot type="welcome" />);
    expect(screen.getByText(/欢迎/)).toBeInTheDocument();
  });

  it('renders no-tasks type', () => {
    renderWithRouter(<EmptyStateWithMascot type="no-tasks" />);
    expect(screen.getByText(/任务/)).toBeInTheDocument();
  });

  it('renders no-results type', () => {
    renderWithRouter(<EmptyStateWithMascot type="no-results" />);
    expect(screen.getByText(/结果/)).toBeInTheDocument();
  });

  it('calls onAction when action button is clicked', () => {
    const handleAction = vi.fn();
    renderWithRouter(
      <EmptyStateWithMascot type="welcome" actionText="开始" onAction={handleAction} />
    );
    
    const button = screen.getByText('开始');
    fireEvent.click(button);
    expect(handleAction).toHaveBeenCalled();
  });
});

describe('LoadingWithMascot', () => {
  it('renders with default props', () => {
    renderWithRouter(<LoadingWithMascot />);
    expect(screen.getByAltText('房小智')).toBeInTheDocument();
  });

  it('renders with phases', () => {
    const phases = [
      { id: 'phase1', label: '阶段一', messages: ['消息1', '消息2'] },
      { id: 'phase2', label: '阶段二', messages: ['消息3'] },
    ];
    
    renderWithRouter(<LoadingWithMascot phases={phases} currentPhase="phase1" />);
    expect(screen.getByAltText('房小智')).toBeInTheDocument();
  });
});

describe('MascotToast', () => {
  const TestComponent = () => {
    const { showSuccess, showError, showInfo } = useMascotToast();
    
    return (
      <div>
        <button onClick={() => showSuccess('成功消息')}>成功</button>
        <button onClick={() => showError('错误消息')}>错误</button>
        <button onClick={() => showInfo('信息消息')}>信息</button>
      </div>
    );
  };

  it('shows success toast', async () => {
    renderWithProviders(<TestComponent />);
    
    const successButton = screen.getByText('成功');
    fireEvent.click(successButton);
    
    await waitFor(() => {
      expect(screen.getByText('成功消息')).toBeInTheDocument();
    });
  });

  it('shows error toast', async () => {
    renderWithProviders(<TestComponent />);
    
    const errorButton = screen.getByText('错误');
    fireEvent.click(errorButton);
    
    await waitFor(() => {
      expect(screen.getByText('错误消息')).toBeInTheDocument();
    });
  });

  it('shows info toast', async () => {
    renderWithProviders(<TestComponent />);
    
    const infoButton = screen.getByText('信息');
    fireEvent.click(infoButton);
    
    await waitFor(() => {
      expect(screen.getByText('信息消息')).toBeInTheDocument();
    });
  });
});

describe('OnboardingTour', () => {
  it('renders when open', () => {
    renderWithRouter(
      <OnboardingTour isOpen={true} onComplete={vi.fn()} onSkip={vi.fn()} />
    );
    expect(screen.getByText('欢迎来到房都督AI')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    renderWithRouter(
      <OnboardingTour isOpen={false} onComplete={vi.fn()} onSkip={vi.fn()} />
    );
    expect(screen.queryByText('欢迎来到房都督AI')).not.toBeInTheDocument();
  });

  it('calls onSkip when skip button is clicked', () => {
    const handleSkip = vi.fn();
    renderWithRouter(
      <OnboardingTour isOpen={true} onComplete={vi.fn()} onSkip={handleSkip} />
    );
    
    const skipButton = screen.getByText('跳过');
    fireEvent.click(skipButton);
    expect(handleSkip).toHaveBeenCalled();
  });

  it('navigates to next step', () => {
    renderWithRouter(
      <OnboardingTour isOpen={true} onComplete={vi.fn()} onSkip={vi.fn()} />
    );
    
    const nextButton = screen.getByText('下一步');
    fireEvent.click(nextButton);
    
    expect(screen.getByText('开始分析')).toBeInTheDocument();
  });

  it('calls onComplete on last step', () => {
    const handleComplete = vi.fn();
    renderWithRouter(
      <OnboardingTour isOpen={true} onComplete={handleComplete} onSkip={vi.fn()} />
    );
    
    const nextButtons = screen.getAllByText(/下一步|完成/);
    nextButtons.forEach((button) => {
      fireEvent.click(button);
    });
    
    expect(handleComplete).toHaveBeenCalled();
  });
});

describe('ActiveReminder', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders idle reminder', async () => {
    vi.useFakeTimers();
    
    renderWithRouter(<IdleReminder enabled={true} idleTimeout={1000} />);
    
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    
    await waitFor(() => {
      const reminder = screen.getByText(/需要帮助吗/);
      expect(reminder).toBeTruthy();
    }, { timeout: 3000 });
    
    vi.useRealTimers();
  });

  it('renders daily greeting', async () => {
    localStorage.removeItem('mascot_greeting_date');
    
    renderWithRouter(<DailyGreeting enabled={true} />);
    
    await waitFor(() => {
      const greeting = screen.getByText(/好/);
      expect(greeting).toBeTruthy();
    });
  });
});

describe('OnboardingManager', () => {
  beforeEach(() => {
    localStorage.removeItem('onboarding_completed');
  });

  it('shows onboarding for new users', async () => {
    renderWithRouter(
      <OnboardingManager>
        <div>Content</div>
      </OnboardingManager>
    );
    
    await waitFor(() => {
      expect(screen.getByText('欢迎来到房都督AI')).toBeInTheDocument();
    });
  });

  it('does not show onboarding for returning users', async () => {
    localStorage.setItem('onboarding_completed', 'true');
    
    renderWithRouter(
      <OnboardingManager>
        <div>Content</div>
      </OnboardingManager>
    );
    
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(screen.queryByText('欢迎来到房都督AI')).not.toBeInTheDocument();
  });
});
