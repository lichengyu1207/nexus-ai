import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import VoiceSettingsPage from '../index';
import { useVoiceSettings } from '../hooks/useVoiceSettings';

vi.mock('../hooks/useVoiceSettings');
vi.mock('../components/SpeechSynthesisWrapper', () => ({
  useSpeechSynthesis: () => ({
    speak: vi.fn(),
    stop: vi.fn(),
    voices: [],
    chineseVoices: [],
    isSupported: true,
  }),
}));

const mockSettings = {
  enabled: true,
  volume: 0.8,
  rate: 1.0,
  pitch: 1.0,
  voiceURI: '',
  events: {
    taskCompleted: true,
    taskFailed: true,
    taskProgress: false,
    newNotification: true,
    agentStatusChange: false,
    collaborationEvent: false,
  },
  customSounds: {},
  agentVoices: {},
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('VoiceSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useVoiceSettings as ReturnType<typeof vi.fn>).mockReturnValue({
      settings: mockSettings,
      isLoading: false,
      updateSettings: vi.fn(),
      updateEvent: vi.fn(),
      setCustomSound: vi.fn(),
      isSaving: false,
    });
  });

  it('renders voice settings page', () => {
    render(<VoiceSettingsPage />, { wrapper });
    expect(screen.getByText('语音交互设置')).toBeInTheDocument();
  });

  it('shows basic settings section', () => {
    render(<VoiceSettingsPage />, { wrapper });
    expect(screen.getByText('基础设置')).toBeInTheDocument();
  });

  it('shows event settings section', () => {
    render(<VoiceSettingsPage />, { wrapper });
    expect(screen.getByText('播报事件')).toBeInTheDocument();
  });

  it('shows voice test area', () => {
    render(<VoiceSettingsPage />, { wrapper });
    expect(screen.getByText('语音测试')).toBeInTheDocument();
  });

  it('shows custom voice upload section', () => {
    render(<VoiceSettingsPage />, { wrapper });
    expect(screen.getByText('自定义配音')).toBeInTheDocument();
  });

  it('toggles voice enabled state', async () => {
    const updateSettings = vi.fn();
    (useVoiceSettings as ReturnType<typeof vi.fn>).mockReturnValue({
      settings: mockSettings,
      isLoading: false,
      updateSettings,
      updateEvent: vi.fn(),
      setCustomSound: vi.fn(),
      isSaving: false,
    });

    render(<VoiceSettingsPage />, { wrapper });
    
    const toggleButton = screen.getByRole('button', { name: /启用语音|关闭语音/i });
    if (toggleButton) {
      fireEvent.click(toggleButton);
      expect(updateSettings).toHaveBeenCalledWith({ enabled: false });
    }
  });

  it('updates event settings', async () => {
    const updateEvent = vi.fn();
    (useVoiceSettings as ReturnType<typeof vi.fn>).mockReturnValue({
      settings: mockSettings,
      isLoading: false,
      updateSettings: vi.fn(),
      updateEvent,
      setCustomSound: vi.fn(),
      isSaving: false,
    });

    render(<VoiceSettingsPage />, { wrapper });
    
    const checkboxes = screen.getAllByRole('checkbox');
    if (checkboxes.length > 0) {
      fireEvent.click(checkboxes[0]);
      expect(updateEvent).toHaveBeenCalled();
    }
  });
});
