import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReasoningChain from './ReasoningChain';
import { useReasoningChain } from './useReasoningChain';
import type { ReasoningStep } from './types';

jest.mock('./useReasoningChain');
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

const mockSteps: ReasoningStep[] = [
  {
    step: '兵部攻击模拟',
    content: '根据当前网络拓扑，检测到开放端口 22，尝试暴力破解...',
    timestamp: '2026-03-27T10:05:23Z',
    feedbackGiven: false,
  },
  {
    step: '户部收益计算',
    content: '基于攻击成功率 85%，预期收益为 1250 万...',
    timestamp: '2026-03-27T10:05:45Z',
    feedbackGiven: false,
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('ReasoningChain', () => {
  beforeEach(() => {
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: mockSteps,
      isLoading: false,
      error: null,
      submitFeedback: jest.fn(),
    });
  });

  it('renders loading state', () => {
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: [],
      isLoading: true,
      error: null,
      submitFeedback: jest.fn(),
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: [],
      isLoading: false,
      error: new Error('Network error'),
      submitFeedback: jest.fn(),
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    expect(screen.getByText('加载失败')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: [],
      isLoading: false,
      error: null,
      submitFeedback: jest.fn(),
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    expect(screen.getByText('暂无推理链数据')).toBeInTheDocument();
  });

  it('renders steps correctly', () => {
    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    expect(screen.getByText('兵部攻击模拟')).toBeInTheDocument();
    expect(screen.getByText('户部收益计算')).toBeInTheDocument();
    expect(screen.getByText(/根据当前网络拓扑/)).toBeInTheDocument();
    expect(screen.getByText(/基于攻击成功率/)).toBeInTheDocument();
    expect(screen.getByText('推理链 (2 步)')).toBeInTheDocument();
  });

  it('calls submitFeedback when helpful button clicked', async () => {
    const mockSubmitFeedback = jest.fn();
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: mockSteps,
      isLoading: false,
      error: null,
      submitFeedback: mockSubmitFeedback,
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    const helpfulButtons = screen.getAllByLabelText('标记为有用');
    fireEvent.click(helpfulButtons[0]);
    
    expect(mockSubmitFeedback).toHaveBeenCalledWith({
      stepIndex: 0,
      feedback: 'helpful',
    });
  });

  it('calls submitFeedback when not helpful button clicked', async () => {
    const mockSubmitFeedback = jest.fn();
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: mockSteps,
      isLoading: false,
      error: null,
      submitFeedback: mockSubmitFeedback,
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    const notHelpfulButtons = screen.getAllByLabelText('标记为无用');
    fireEvent.click(notHelpfulButtons[1]);
    
    expect(mockSubmitFeedback).toHaveBeenCalledWith({
      stepIndex: 1,
      feedback: 'not_helpful',
    });
  });

  it('disables feedback buttons when feedbackGiven is true', () => {
    const stepsWithFeedback: ReasoningStep[] = [
      { ...mockSteps[0], feedbackGiven: true },
    ];
    (useReasoningChain as jest.Mock).mockReturnValue({
      steps: stepsWithFeedback,
      isLoading: false,
      error: null,
      submitFeedback: jest.fn(),
    });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    const helpfulButton = screen.getByLabelText('标记为有用');
    expect(helpfulButton).toBeDisabled();
  });

  it('copies reasoning chain to clipboard', async () => {
    const mockClipboard = {
      writeText: jest.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });

    render(<ReasoningChain taskId="task_001" />, { wrapper: createWrapper() });
    
    const copyButton = screen.getByText('复制推理链');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(mockClipboard.writeText).toHaveBeenCalled();
    });
  });

  it('matches snapshot', () => {
    const { container } = render(<ReasoningChain taskId="task_001" />, {
      wrapper: createWrapper(),
    });
    expect(container.firstChild).toMatchSnapshot();
  });
});
