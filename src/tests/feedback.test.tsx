import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import FeedbackPage from '@/pages/FeedbackPage';
import ReportModal from '@/components/ReportModal';
import ReportButton from '@/components/ReportButton';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock('@/utils/toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'test-user-id', email: 'test@example.com' },
  }),
}));

vi.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({ onClick: vi.fn() }),
    getInputProps: () => ({}),
    isDragActive: false,
  }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('FeedbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders feedback page with title', () => {
    renderWithRouter(<FeedbackPage />);
    expect(screen.getByText('反馈与建议')).toBeInTheDocument();
  });

  it('shows submit feedback button', () => {
    renderWithRouter(<FeedbackPage />);
    expect(screen.getByText('提交反馈')).toBeInTheDocument();
  });

  it('shows history button', () => {
    renderWithRouter(<FeedbackPage />);
    expect(screen.getByText('历史记录')).toBeInTheDocument();
  });

  it('shows feedback type options', () => {
    renderWithRouter(<FeedbackPage />);
    expect(screen.getByText('功能反馈')).toBeInTheDocument();
    expect(screen.getByText('建议')).toBeInTheDocument();
    expect(screen.getByText('问题报告')).toBeInTheDocument();
    expect(screen.getByText('投诉')).toBeInTheDocument();
  });

  it('shows content textarea', () => {
    renderWithRouter(<FeedbackPage />);
    const textarea = screen.getByPlaceholderText(/请详细描述您的反馈/);
    expect(textarea).toBeInTheDocument();
  });

  it('disables submit button when content is too short', () => {
    renderWithRouter(<FeedbackPage />);
    const submitButton = screen.getByText('提交反馈');
    expect(submitButton).toBeDisabled();
  });
});

describe('ReportModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmitted = vi.fn();

  const defaultProps = {
    reportedType: 'report' as const,
    reportedId: 'test-id',
    onClose: mockOnClose,
    onSubmitted: mockOnSubmitted,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders report modal with title', () => {
    renderWithRouter(<ReportModal {...defaultProps} />);
    expect(screen.getByText('举报分析报告')).toBeInTheDocument();
  });

  it('shows reason options', () => {
    renderWithRouter(<ReportModal {...defaultProps} />);
    expect(screen.getByText('不当内容')).toBeInTheDocument();
    expect(screen.getByText('垃圾信息')).toBeInTheDocument();
    expect(screen.getByText('涉嫌欺诈')).toBeInTheDocument();
  });

  it('shows confirmation checkbox', () => {
    renderWithRouter(<ReportModal {...defaultProps} />);
    expect(screen.getByText(/我确认举报内容真实有效/)).toBeInTheDocument();
  });

  it('disables submit button without confirmation', () => {
    renderWithRouter(<ReportModal {...defaultProps} />);
    const submitButton = screen.getByText('提交举报');
    expect(submitButton).toBeDisabled();
  });

  it('calls onClose when cancel button is clicked', () => {
    renderWithRouter(<ReportModal {...defaultProps} />);
    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});

describe('ReportButton', () => {
  const defaultProps = {
    type: 'report' as const,
    id: 'test-id',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders report button', () => {
    renderWithRouter(<ReportButton {...defaultProps} />);
    const button = screen.getByTitle('举报');
    expect(button).toBeInTheDocument();
  });

  it('shows report icon', () => {
    renderWithRouter(<ReportButton {...defaultProps} />);
    const button = screen.getByTitle('举报');
    expect(button.querySelector('svg')).toBeInTheDocument();
  });
});
