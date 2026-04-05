import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import WorkflowBuilderPage from '../index';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

vi.mock('../hooks/useWorkflow', () => ({
  useWorkflow: () => ({
    workflow: {
      id: 'test-workflow',
      name: '测试工作流',
      version: 1,
      nodes: [],
      edges: [],
      triggers: [],
      published: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    versions: [],
    isLoading: false,
    nodes: [],
    edges: [],
    selectedNodeId: null,
    selectedNode: null,
    hasUnsavedChanges: false,
    addNode: vi.fn(),
    updateNode: vi.fn(),
    deleteNode: vi.fn(),
    addEdge: vi.fn(),
    deleteEdge: vi.fn(),
    createNode: vi.fn(() => ({
      id: 'test-node',
      type: 'agent',
      position: { x: 100, y: 100 },
      data: { label: '测试节点', config: {} },
    })),
    createEdge: vi.fn(),
    save: vi.fn(),
    publish: vi.fn(),
    isSaving: false,
    isPublishing: false,
  }),
  useWorkflowStore: {
    getState: () => ({
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      setSelectedNodeId: vi.fn(),
      reset: vi.fn(),
    }),
  },
}));

vi.mock('../hooks/useWorkflowExecution', () => ({
  useWorkflowExecution: () => ({
    status: 'idle',
    nodeStatuses: {},
    logs: [],
    startExecution: vi.fn(),
    stopExecution: vi.fn(),
    resetExecution: vi.fn(),
  }),
}));

describe('WorkflowBuilderPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow builder page', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('节点库')).toBeInTheDocument();
  });

  it('shows workflow name in toolbar', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('测试工作流')).toBeInTheDocument();
  });

  it('shows save button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('保存')).toBeInTheDocument();
  });

  it('shows publish button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('发布')).toBeInTheDocument();
  });

  it('shows test button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('测试')).toBeInTheDocument();
  });

  it('shows version history button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('版本历史')).toBeInTheDocument();
  });

  it('shows template marketplace button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('模板市场')).toBeInTheDocument();
  });

  it('shows node categories', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('智能体节点')).toBeInTheDocument();
    expect(screen.getByText('工具节点')).toBeInTheDocument();
  });

  it('shows auto layout button', () => {
    render(<WorkflowBuilderPage />, { wrapper });
    expect(screen.getByText('自动布局')).toBeInTheDocument();
  });

  it('opens test runner when test button clicked', async () => {
    render(<WorkflowBuilderPage />, { wrapper });
    
    const testButton = screen.getByText('测试');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText('测试运行')).toBeInTheDocument();
    });
  });

  it('opens version history modal when button clicked', async () => {
    render(<WorkflowBuilderPage />, { wrapper });
    
    const versionButton = screen.getByText('版本历史');
    fireEvent.click(versionButton);
    
    await waitFor(() => {
      expect(screen.getByText('版本历史')).toBeInTheDocument();
    });
  });

  it('opens template marketplace when button clicked', async () => {
    render(<WorkflowBuilderPage />, { wrapper });
    
    const templateButton = screen.getByText('模板市场');
    fireEvent.click(templateButton);
    
    await waitFor(() => {
      expect(screen.getByText('模板市场')).toBeInTheDocument();
    });
  });
});
