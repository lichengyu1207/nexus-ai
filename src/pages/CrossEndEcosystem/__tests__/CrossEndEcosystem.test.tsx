import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CrossEndEcosystem from '../index';
import { EndTabs } from '../components/EndTabs';
import { EndStatisticsCards } from '../components/EndStatisticsCards';
import { CollaborationTimeline } from '../components/CollaborationTimeline';
import { NewMessageInput } from '../components/NewMessageInput';
import { EventDetailModal } from '../components/EventDetailModal';
import type { End, CollaborationEvent } from '../types';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

const mockEnds: End[] = [
  { id: 'university', name: 'university', displayName: '院校端', unreadCount: 3 },
  { id: 'enterprise', name: 'enterprise', displayName: '企业端', unreadCount: 0 },
];

const mockEvent: CollaborationEvent = {
  id: '1',
  timestamp: new Date().toISOString(),
  title: '测试事件',
  description: '这是一个测试事件描述',
  fromEnd: 'university',
  toEnd: 'enterprise',
  status: 'pending',
  actionable: true,
  relatedTaskId: 'task-1',
};

describe('CrossEndEcosystem', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders main heading', () => {
    render(<CrossEndEcosystem />);
    expect(screen.getByText('五端协同生态')).toBeInTheDocument();
  });

  it('renders all end tabs', () => {
    render(<CrossEndEcosystem />);
    expect(screen.getByText('院校端')).toBeInTheDocument();
    expect(screen.getByText('企业端')).toBeInTheDocument();
    expect(screen.getByText('政府端')).toBeInTheDocument();
    expect(screen.getByText('协会端')).toBeInTheDocument();
    expect(screen.getByText('公众端')).toBeInTheDocument();
  });
});

describe('EndTabs', () => {
  const mockOnSelectEnd = vi.fn();

  it('renders all tabs correctly', () => {
    render(
      <EndTabs
        ends={mockEnds}
        selectedEndId="university"
        onSelectEnd={mockOnSelectEnd}
      />
    );

    expect(screen.getByText('院校端')).toBeInTheDocument();
    expect(screen.getByText('企业端')).toBeInTheDocument();
  });

  it('shows unread count badge', () => {
    render(
      <EndTabs
        ends={mockEnds}
        selectedEndId="university"
        onSelectEnd={mockOnSelectEnd}
      />
    );

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('calls onSelectEnd when tab is clicked', () => {
    render(
      <EndTabs
        ends={mockEnds}
        selectedEndId="university"
        onSelectEnd={mockOnSelectEnd}
      />
    );

    fireEvent.click(screen.getByText('企业端'));
    expect(mockOnSelectEnd).toHaveBeenCalledWith('enterprise');
  });

  it('applies selected styles to active tab', () => {
    render(
      <EndTabs
        ends={mockEnds}
        selectedEndId="university"
        onSelectEnd={mockOnSelectEnd}
      />
    );

    const selectedTab = screen.getByRole('tab', { selected: true });
    expect(selectedTab).toHaveTextContent('院校端');
  });
});

describe('EndStatisticsCards', () => {
  it('renders loading state', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));

    render(wrapper(<EndStatisticsCards endId="university" />));

    const skeletons = screen.getAllByRole('generic').filter(
      (el) => el.className.includes('animate-pulse')
    );
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders statistics after loading', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        taskCount: 10,
        activeUsers: 5,
        messageCount: 20,
      }),
    });

    render(wrapper(<EndStatisticsCards endId="university" />));

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
    });
  });
});

describe('CollaborationTimeline', () => {
  it('renders filter dropdown', () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    render(wrapper(<CollaborationTimeline endId="university" />));

    expect(screen.getByText('协同事件时间线')).toBeInTheDocument();
  });

  it('renders empty state when no events', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    render(wrapper(<CollaborationTimeline endId="university" />));

    await waitFor(() => {
      expect(screen.getByText('暂无协同事件')).toBeInTheDocument();
    });
  });

  it('renders events list', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([mockEvent]),
    });

    render(wrapper(<CollaborationTimeline endId="university" />));

    await waitFor(() => {
      expect(screen.getByText('测试事件')).toBeInTheDocument();
    });
  });
});

describe('NewMessageInput', () => {
  it('renders input field', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument();
  });

  it('calls onSend when send button is clicked', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: '测试消息' } });
    
    const sendButton = screen.getByText('发送');
    fireEvent.click(sendButton);

    expect(mockOnSend).toHaveBeenCalledWith('测试消息', undefined);
  });

  it('sends message on Enter key', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockOnSend).toHaveBeenCalledWith('测试消息', undefined);
  });

  it('does not send on Shift+Enter', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', shiftKey: true });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('shows quick actions when button is clicked', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    const quickActionButton = screen.getByLabelText('快捷操作');
    fireEvent.click(quickActionButton);

    expect(screen.getByText('请求数据')).toBeInTheDocument();
    expect(screen.getByText('分配任务')).toBeInTheDocument();
    expect(screen.getByText('确认回复')).toBeInTheDocument();
  });

  it('fills template when quick action is clicked', () => {
    const mockOnSend = vi.fn();
    render(<NewMessageInput onSend={mockOnSend} />);

    const quickActionButton = screen.getByLabelText('快捷操作');
    fireEvent.click(quickActionButton);

    const requestDataButton = screen.getByText('请求数据');
    fireEvent.click(requestDataButton);

    const input = screen.getByPlaceholderText('输入消息...');
    expect(input).toHaveValue('您好，请提供相关数据资料。');
  });
});

describe('EventDetailModal', () => {
  const mockOnClose = vi.fn();
  const mockOnProcess = vi.fn();

  it('does not render when closed', () => {
    render(
      <EventDetailModal
        event={null}
        isOpen={false}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    expect(screen.queryByText('事件详情')).not.toBeInTheDocument();
  });

  it('renders modal when open', () => {
    render(
      <EventDetailModal
        event={mockEvent}
        isOpen={true}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    expect(screen.getByText('事件详情')).toBeInTheDocument();
    expect(screen.getByText('测试事件')).toBeInTheDocument();
    expect(screen.getByText('这是一个测试事件描述')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <EventDetailModal
        event={mockEvent}
        isOpen={true}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    const closeButton = screen.getByLabelText('关闭');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows process button for actionable events', () => {
    render(
      <EventDetailModal
        event={mockEvent}
        isOpen={true}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    expect(screen.getByText('处理事件')).toBeInTheDocument();
  });

  it('calls onProcess when process button is clicked', () => {
    render(
      <EventDetailModal
        event={mockEvent}
        isOpen={true}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    const processButton = screen.getByText('处理事件');
    fireEvent.click(processButton);

    expect(mockOnProcess).toHaveBeenCalledWith('1');
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes on Escape key', () => {
    render(
      <EventDetailModal
        event={mockEvent}
        isOpen={true}
        onClose={mockOnClose}
        onProcess={mockOnProcess}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(mockOnClose).toHaveBeenCalled();
  });
});
