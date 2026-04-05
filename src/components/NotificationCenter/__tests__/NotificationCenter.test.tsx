import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { NotificationCenter } from '../index';
import { NotificationBell } from '../NotificationBell';
import { NotificationItem } from '../NotificationItem';
import { NotificationList } from '../NotificationList';
import { NotificationSettingsModal } from '../NotificationSettingsModal';
import type { Notification, NotificationPreference } from '../types';
import { DEFAULT_NOTIFICATION_PREFERENCES } from '../types';

const mockNotification: Notification = {
  id: '1',
  type: 'task_status',
  title: '任务完成',
  content: '您的估值任务已完成',
  read: false,
  createdAt: new Date().toISOString(),
  targetUrl: '/tasks/1',
};

const mockReadNotification: Notification = {
  id: '2',
  type: 'agent_alert',
  title: '智能体告警',
  content: '智能体执行异常',
  read: true,
  createdAt: new Date(Date.now() - 3600000).toISOString(),
};

const mockNotifications: Notification[] = [
  mockNotification,
  mockReadNotification,
  {
    id: '3',
    type: 'collaboration',
    title: '协同邀请',
    content: '您收到一个新的协同邀请',
    read: false,
    createdAt: new Date(Date.now() - 7200000).toISOString(),
  },
];

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockWebSocket = vi.fn();
vi.mock('../hooks/useNotificationWebSocket', () => ({
  useNotificationWebSocket: () => ({
    isConnected: true,
    error: null,
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
}));

describe('NotificationBell', () => {
  it('renders bell icon with unread count', () => {
    render(<NotificationBell onClick={vi.fn()} unreadCount={5} />);

    expect(screen.getByLabelText(/通知，未读数量 5/)).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays 99+ for counts over 99', () => {
    render(<NotificationBell onClick={vi.fn()} unreadCount={100} />);

    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('does not display badge when unread count is 0', () => {
    render(<NotificationBell onClick={vi.fn()} unreadCount={0} />);

    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<NotificationBell onClick={handleClick} unreadCount={1} />);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies shake animation when isShaking is true', () => {
    const { rerender } = render(
      <NotificationBell onClick={vi.fn()} unreadCount={1} isShaking={false} />
    );

    const button = screen.getByRole('button');
    expect(button).not.toHaveStyle('transform');

    rerender(<NotificationBell onClick={vi.fn()} unreadCount={1} isShaking={true} />);
  });
});

describe('NotificationItem', () => {
  const mockOnMarkRead = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders notification with correct content', () => {
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    expect(screen.getByText('任务完成')).toBeInTheDocument();
    expect(screen.getByText('您的估值任务已完成')).toBeInTheDocument();
    expect(screen.getByText('任务状态')).toBeInTheDocument();
  });

  it('shows unread indicator for unread notifications', () => {
    const { container } = render(
      <NotificationItem
        notification={mockNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    const unreadDot = container.querySelector('.bg-amber-400');
    expect(unreadDot).toBeInTheDocument();
  });

  it('does not show unread indicator for read notifications', () => {
    const { container } = render(
      <NotificationItem
        notification={mockReadNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    const unreadDot = container.querySelector('.bg-amber-400');
    expect(unreadDot).not.toBeInTheDocument();
  });

  it('calls onMarkRead when mark read button is clicked', () => {
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    const markReadButton = screen.getByLabelText('标记已读');
    fireEvent.click(markReadButton);

    expect(mockOnMarkRead).toHaveBeenCalledWith('1');
    expect(mockOnClick).not.toHaveBeenCalled();
  });

  it('calls onDelete when delete button is clicked', () => {
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    const deleteButton = screen.getByLabelText('删除通知');
    fireEvent.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalledWith('1');
    expect(mockOnClick).not.toHaveBeenCalled();
  });

  it('calls onClick and onMarkRead when notification is clicked', () => {
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        onClick={mockOnClick}
      />
    );

    const item = screen.getByRole('listitem');
    fireEvent.click(item);

    expect(mockOnMarkRead).toHaveBeenCalledWith('1');
    expect(mockOnClick).toHaveBeenCalledWith(mockNotification);
  });
});

describe('NotificationList', () => {
  const mockOnMarkRead = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnLoadMore = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner when loading', () => {
    render(
      <NotificationList
        notifications={[]}
        isLoading={true}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        height={400}
      />
    );

    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('shows empty state when no notifications', () => {
    render(
      <NotificationList
        notifications={[]}
        isLoading={false}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        height={400}
      />
    );

    expect(screen.getByText('暂无通知')).toBeInTheDocument();
  });

  it('renders notifications correctly', () => {
    render(
      <NotificationList
        notifications={mockNotifications}
        isLoading={false}
        isFetchingNextPage={false}
        hasMore={false}
        onLoadMore={mockOnLoadMore}
        onMarkRead={mockOnMarkRead}
        onDelete={mockOnDelete}
        height={400}
      />
    );

    expect(screen.getByText('任务完成')).toBeInTheDocument();
    expect(screen.getByText('智能体告警')).toBeInTheDocument();
    expect(screen.getByText('协同邀请')).toBeInTheDocument();
  });
});

describe('NotificationSettingsModal', () => {
  const mockOnClose = vi.fn();
  const mockOnUpdatePreferences = vi.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    preferences: DEFAULT_NOTIFICATION_PREFERENCES,
    onUpdatePreferences: mockOnUpdatePreferences,
    isUpdating: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal when open', () => {
    render(<NotificationSettingsModal {...defaultProps} />);

    expect(screen.getByText('通知偏好设置')).toBeInTheDocument();
    expect(screen.getByText('任务状态')).toBeInTheDocument();
    expect(screen.getByText('智能体告警')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<NotificationSettingsModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('通知偏好设置')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<NotificationSettingsModal {...defaultProps} />);

    const closeButton = screen.getByLabelText('关闭');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('toggles preference switches', () => {
    render(<NotificationSettingsModal {...defaultProps} />);

    const switches = screen.getAllByRole('checkbox');
    fireEvent.click(switches[0]);

    expect(switches[0]).not.toBeChecked();
  });

  it('calls onUpdatePreferences when save button is clicked', () => {
    render(<NotificationSettingsModal {...defaultProps} />);

    const switches = screen.getAllByRole('checkbox');
    fireEvent.click(switches[0]);

    const saveButton = screen.getByText('保存设置');
    fireEvent.click(saveButton);

    expect(mockOnUpdatePreferences).toHaveBeenCalled();
  });

  it('disables save button when no changes', () => {
    render(<NotificationSettingsModal {...defaultProps} />);

    const saveButton = screen.getByText('保存设置');
    expect(saveButton).toBeDisabled();
  });
});

describe('NotificationCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();

    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/unread-count')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ count: 3 }),
        });
      }
      if (url.includes('/notifications')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              notifications: mockNotifications,
              total: 3,
              page: 1,
              limit: 20,
              hasMore: false,
            }),
        });
      }
      if (url.includes('/notification-preferences')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(DEFAULT_NOTIFICATION_PREFERENCES),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  it('renders bell with unread count', async () => {
    render(<NotificationCenter />, { wrapper });

    await waitFor(() => {
      expect(screen.getByLabelText(/通知/)).toBeInTheDocument();
    });
  });

  it('opens panel when bell is clicked', async () => {
    render(<NotificationCenter />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText('通知中心')).toBeInTheDocument();
    });
  });

  it('closes panel when clicking outside', async () => {
    render(
      <div>
        <NotificationCenter />
        <div data-testid="outside">Outside</div>
      </div>,
      { wrapper }
    );

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText('通知中心')).toBeInTheDocument();
    });

    fireEvent.mouseDown(screen.getByTestId('outside'));

    await waitFor(() => {
      expect(screen.queryByText('通知中心')).not.toBeInTheDocument();
    });
  });

  it('closes panel when Escape is pressed', async () => {
    render(<NotificationCenter />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText('通知中心')).toBeInTheDocument();
    });

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => {
      expect(screen.queryByText('通知中心')).not.toBeInTheDocument();
    });
  });

  it('shows tabs for filtering', async () => {
    render(<NotificationCenter />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText('全部')).toBeInTheDocument();
      expect(screen.getByText('未读')).toBeInTheDocument();
      expect(screen.getByText('已读')).toBeInTheDocument();
    });
  });

  it('shows settings modal when settings button is clicked', async () => {
    render(<NotificationCenter />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText('通知中心')).toBeInTheDocument();
    });

    const settingsButton = screen.getByLabelText('通知设置');
    fireEvent.click(settingsButton);

    await waitFor(() => {
      expect(screen.getByText('通知偏好设置')).toBeInTheDocument();
    });
  });
});
