import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Settings from '../index';
import { SettingsSidebar } from '../components/SettingsSidebar';
import { PersonalSettings } from '../components/PersonalSettings';
import { ConfirmModal } from '../components/ConfirmModal';
import type { SettingsTab } from '../types';

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

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders settings page', () => {
    render(<Settings />);
    expect(screen.getByText('设置')).toBeInTheDocument();
  });
});

describe('SettingsSidebar', () => {
  const mockOnSelect = vi.fn();

  it('renders all personal menu items', () => {
    render(
      <SettingsSidebar
        activeKey="theme"
        onSelect={mockOnSelect}
        isAdmin={false}
      />
    );

    expect(screen.getByText('主题设置')).toBeInTheDocument();
    expect(screen.getByText('语言设置')).toBeInTheDocument();
    expect(screen.getByText('通知设置')).toBeInTheDocument();
    expect(screen.getByText('配音设置')).toBeInTheDocument();
  });

  it('shows admin menu items when isAdmin is true', () => {
    render(
      <SettingsSidebar
        activeKey="theme"
        onSelect={mockOnSelect}
        isAdmin={true}
      />
    );

    expect(screen.getByText('智能体权限')).toBeInTheDocument();
    expect(screen.getByText('审计日志')).toBeInTheDocument();
    expect(screen.getByText('MCP工具管理')).toBeInTheDocument();
    expect(screen.getByText('全局配置')).toBeInTheDocument();
  });

  it('hides admin menu items when isAdmin is false', () => {
    render(
      <SettingsSidebar
        activeKey="theme"
        onSelect={mockOnSelect}
        isAdmin={false}
      />
    );

    expect(screen.queryByText('智能体权限')).not.toBeInTheDocument();
    expect(screen.queryByText('审计日志')).not.toBeInTheDocument();
  });

  it('calls onSelect when menu item is clicked', () => {
    render(
      <SettingsSidebar
        activeKey="theme"
        onSelect={mockOnSelect}
        isAdmin={false}
      />
    );

    fireEvent.click(screen.getByText('语言设置'));
    expect(mockOnSelect).toHaveBeenCalledWith('language');
  });

  it('highlights active menu item', () => {
    render(
      <SettingsSidebar
        activeKey="theme"
        onSelect={mockOnSelect}
        isAdmin={false}
      />
    );

    const activeItem = screen.getByText('主题设置').closest('button');
    expect(activeItem).toHaveClass('bg-amber-500/20');
  });
});

describe('PersonalSettings', () => {
  it('renders loading state', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));
    render(wrapper(<PersonalSettings />));

    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('renders theme options', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          theme: 'dark',
          language: 'zh',
          notifications: { email: true, inApp: true },
          voiceEnabled: false,
        }),
    });

    render(wrapper(<PersonalSettings />));

    await waitFor(() => {
      expect(screen.getByText('主题设置')).toBeInTheDocument();
    });
  });
});

describe('ConfirmModal', () => {
  const mockOnConfirm = vi.fn();
  const mockOnCancel = vi.fn();

  it('renders when open', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={false}
      />
    );

    expect(screen.getByText('确认删除')).toBeInTheDocument();
    expect(screen.getByText('此操作不可恢复')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <ConfirmModal
        isOpen={false}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={false}
      />
    );

    expect(screen.queryByText('确认删除')).not.toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={false}
      />
    );

    fireEvent.click(screen.getByText('确认'));
    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={false}
      />
    );

    fireEvent.click(screen.getByText('取消'));
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('shows danger styling when isDanger is true', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={false}
        isDanger={true}
      />
    );

    const confirmButton = screen.getByText('删除');
    expect(confirmButton).toHaveClass('bg-red-500');
  });

  it('disables buttons when pending', () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="确认删除"
        message="此操作不可恢复"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isPending={true}
      />
    );

    const cancelButton = screen.getByText('取消');
    expect(cancelButton).toBeDisabled();
  });
});
