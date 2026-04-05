import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TaskStatusCard, { Task } from './TaskStatusCard';

const mockTask: Task = {
  id: 'task_001',
  name: '三省六部智能体协同分析',
  status: 'processing',
  progress: 65,
  startTime: '2026-03-27T10:00:00Z',
  estimatedEndTime: '2026-03-27T10:30:00Z',
  inputParams: {
    dataset: '房市历史数据',
    model: 'AttentionResidual',
    epochs: 100,
  },
  agentsUsed: ['兵部', '户部', '礼部'],
  fullProcessLog: [
    '步骤1: 加载数据...',
    '步骤2: 初始化智能体...',
    '步骤3: 兵部执行攻击模拟...',
    '步骤4: 户部计算收益...',
    '步骤5: 生成报告...',
  ],
};

const pendingTask: Task = {
  id: 'task_002',
  name: '待处理任务',
  status: 'pending',
  progress: 0,
  startTime: '2026-03-27T10:00:00Z',
};

const completedTask: Task = {
  id: 'task_003',
  name: '已完成任务',
  status: 'completed',
  progress: 100,
  startTime: '2026-03-27T10:00:00Z',
  resultSummary: '分析完成，发现3个关键问题',
};

const failedTask: Task = {
  id: 'task_004',
  name: '失败任务',
  status: 'failed',
  progress: 45,
  startTime: '2026-03-27T10:00:00Z',
  errorMessage: '数据加载失败：网络超时',
};

describe('TaskStatusCard', () => {
  it('renders pending status card correctly', () => {
    render(<TaskStatusCard task={pendingTask} />);
    
    expect(screen.getByText('待处理任务')).toBeInTheDocument();
    expect(screen.getByText('等待分析')).toBeInTheDocument();
    expect(screen.getByTestId('progress-text')).toHaveTextContent('0%');
  });

  it('renders processing status card with progress', () => {
    render(<TaskStatusCard task={mockTask} />);
    
    expect(screen.getByText('三省六部智能体协同分析')).toBeInTheDocument();
    expect(screen.getByText('分析中')).toBeInTheDocument();
    expect(screen.getByTestId('progress-text')).toHaveTextContent('65%');
    expect(screen.getByTestId('progress-fill')).toBeInTheDocument();
    expect(screen.getByTestId('progress-shimmer')).toBeInTheDocument();
  });

  it('renders completed status with view report button', () => {
    const onViewReport = jest.fn();
    render(<TaskStatusCard task={completedTask} onViewReport={onViewReport} />);
    
    expect(screen.getByText('已完成任务')).toBeInTheDocument();
    expect(screen.getByText('分析完成')).toBeInTheDocument();
    expect(screen.getByText('分析完成，发现3个关键问题')).toBeInTheDocument();
    
    const reportButton = screen.getByRole('button', { name: /查看报告/i });
    expect(reportButton).toBeInTheDocument();
    
    fireEvent.click(reportButton);
    expect(onViewReport).toHaveBeenCalledWith('task_003');
  });

  it('renders failed status with retry button', () => {
    const onRetry = jest.fn();
    render(<TaskStatusCard task={failedTask} onRetry={onRetry} />);
    
    expect(screen.getByText('失败任务')).toBeInTheDocument();
    expect(screen.getByText('分析失败')).toBeInTheDocument();
    expect(screen.getByText('数据加载失败：网络超时')).toBeInTheDocument();
    
    const retryButton = screen.getByRole('button', { name: /重试/i });
    expect(retryButton).toBeInTheDocument();
    
    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalledWith('task_004');
  });

  it('shows tooltip on hover with input params and agents', async () => {
    render(<TaskStatusCard task={mockTask} />);
    
    const card = screen.getByTestId('task-status-card');
    
    await userEvent.hover(card);
    
    await waitFor(() => {
      expect(screen.getByTestId('tooltip-content')).toBeInTheDocument();
    }, { timeout: 500 });
    
    expect(screen.getByText('输入参数：')).toBeInTheDocument();
    expect(screen.getByText('使用的智能体：')).toBeInTheDocument();
  });

  it('expands and collapses detail panel on click', async () => {
    render(<TaskStatusCard task={mockTask} />);
    
    const card = screen.getByRole('button');
    fireEvent.click(card);
    
    await waitFor(() => {
      expect(screen.getByText('分析过程')).toBeInTheDocument();
    });
    
    expect(screen.getByText('步骤1: 加载数据...')).toBeInTheDocument();
    expect(screen.getByText('步骤2: 初始化智能体...')).toBeInTheDocument();
    
    fireEvent.click(card);
    
    await waitFor(() => {
      expect(screen.queryByText('分析过程')).not.toBeInTheDocument();
    });
  });

  it('matches snapshot', () => {
    const { container } = render(<TaskStatusCard task={mockTask} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});

describe('ProgressBar', () => {
  it('renders with correct progress value', () => {
    render(<TaskStatusCard task={mockTask} />);
    
    const progressFill = screen.getByTestId('progress-fill');
    expect(progressFill).toBeInTheDocument();
  });

  it('shows shimmer animation for processing status', () => {
    render(<TaskStatusCard task={mockTask} />);
    
    const shimmer = screen.getByTestId('progress-shimmer');
    expect(shimmer).toBeInTheDocument();
  });

  it('does not show shimmer for non-processing status', () => {
    render(<TaskStatusCard task={pendingTask} />);
    
    expect(screen.queryByTestId('progress-shimmer')).not.toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  it('has correct aria attributes', () => {
    render(<TaskStatusCard task={mockTask} />);
    
    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('aria-expanded', 'false');
    expect(card).toHaveAttribute('aria-label');
  });

  it('can be focused and activated with keyboard', () => {
    const onViewReport = jest.fn();
    render(<TaskStatusCard task={completedTask} onViewReport={onViewReport} />);
    
    const reportButton = screen.getByRole('button', { name: /查看报告/i });
    reportButton.focus();
    expect(reportButton).toHaveFocus();
    
    fireEvent.click(reportButton);
    expect(onViewReport).toHaveBeenCalled();
  });
});
