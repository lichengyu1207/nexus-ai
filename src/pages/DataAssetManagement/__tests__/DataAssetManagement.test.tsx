import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DataAssetManagement from '../index';
import { AssetTree } from '../components/AssetTree';
import { AssetToolbar } from '../components/AssetToolbar';
import { AssetList } from '../components/AssetList';
import { CreateAssetModal } from '../components/CreateAssetModal';
import type { Asset, TreeNode, ViewMode } from '../types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockAssets: Asset[] = [
  {
    id: '1',
    name: '用户数据表',
    type: 'dataset',
    description: '包含用户基本信息',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    owner: 'admin',
    tags: ['用户', '核心数据'],
    size: 1024000,
    recordCount: 10000,
    qualityScore: 85,
    version: 1,
  },
  {
    id: '2',
    name: 'MySQL 主库',
    type: 'datasource',
    description: '生产环境主数据库',
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    owner: 'dba',
    tags: ['生产', 'MySQL'],
    qualityScore: 92,
    version: 3,
  },
  {
    id: '3',
    name: '房产知识库',
    type: 'knowledgebase',
    description: '房产评估相关知识库',
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    updatedAt: new Date().toISOString(),
    owner: 'analyst',
    tags: ['知识', '房产'],
    qualityScore: 78,
    version: 2,
  },
];

const mockTree: TreeNode[] = [
  {
    id: 'folder-1',
    name: '生产数据',
    type: 'folder',
    children: [
      {
        id: 'asset-1',
        name: '用户数据表',
        type: 'dataset',
      },
    ],
    assetCount: 1,
  },
  {
    id: 'folder-2',
    name: '测试数据',
    type: 'folder',
    children: [],
    assetCount: 0,
  },
];

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('AssetTree', () => {
  const mockOnSelect = vi.fn();
  const mockOnCreateFolder = vi.fn();
  const mockOnDeleteFolder = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders tree structure correctly', () => {
    render(
      <AssetTree
        tree={mockTree}
        onSelect={mockOnSelect}
        onCreateFolder={mockOnCreateFolder}
        onDeleteFolder={mockOnDeleteFolder}
      />
    );

    expect(screen.getByText('资产目录')).toBeInTheDocument();
    expect(screen.getByText('全部资产')).toBeInTheDocument();
    expect(screen.getByText('生产数据')).toBeInTheDocument();
    expect(screen.getByText('测试数据')).toBeInTheDocument();
  });

  it('expands and collapses folders on click', () => {
    render(
      <AssetTree
        tree={mockTree}
        onSelect={mockOnSelect}
        onCreateFolder={mockOnCreateFolder}
        onDeleteFolder={mockOnDeleteFolder}
      />
    );

    const folder = screen.getByText('生产数据');
    fireEvent.click(folder);

    expect(mockOnSelect).toHaveBeenCalled();
  });

  it('shows asset count badge', () => {
    render(
      <AssetTree
        tree={mockTree}
        onSelect={mockOnSelect}
        onCreateFolder={mockOnCreateFolder}
        onDeleteFolder={mockOnDeleteFolder}
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('calls onCreateFolder when create button is clicked', () => {
    render(
      <AssetTree
        tree={mockTree}
        onSelect={mockOnSelect}
        onCreateFolder={mockOnCreateFolder}
        onDeleteFolder={mockOnDeleteFolder}
      />
    );

    const createButton = screen.getByTitle('新建文件夹');
    fireEvent.click(createButton);

    expect(mockOnCreateFolder).toHaveBeenCalled();
  });
});

describe('AssetToolbar', () => {
  const mockOnSearchChange = vi.fn();
  const mockOnViewModeChange = vi.fn();
  const mockOnCreate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input and buttons', () => {
    render(
      <AssetToolbar
        searchQuery=""
        onSearchChange={mockOnSearchChange}
        viewMode="card"
        onViewModeChange={mockOnViewModeChange}
        onCreate={mockOnCreate}
      />
    );

    expect(screen.getByPlaceholderText('搜索资产...')).toBeInTheDocument();
    expect(screen.getByText('新建资产')).toBeInTheDocument();
  });

  it('calls onSearchChange when typing', () => {
    render(
      <AssetToolbar
        searchQuery=""
        onSearchChange={mockOnSearchChange}
        viewMode="card"
        onViewModeChange={mockOnViewModeChange}
        onCreate={mockOnCreate}
      />
    );

    const searchInput = screen.getByPlaceholderText('搜索资产...');
    fireEvent.change(searchInput, { target: { value: '测试' } });

    expect(mockOnSearchChange).toHaveBeenCalledWith('测试');
  });

  it('toggles view mode', () => {
    render(
      <AssetToolbar
        searchQuery=""
        onSearchChange={mockOnSearchChange}
        viewMode="card"
        onViewModeChange={mockOnViewModeChange}
        onCreate={mockOnCreate}
      />
    );

    const listButton = screen.getByTitle('列表视图');
    fireEvent.click(listButton);

    expect(mockOnViewModeChange).toHaveBeenCalledWith('list');
  });

  it('shows batch actions when items selected', () => {
    render(
      <AssetToolbar
        searchQuery=""
        onSearchChange={mockOnSearchChange}
        viewMode="card"
        onViewModeChange={mockOnViewModeChange}
        onCreate={mockOnCreate}
        selectedCount={3}
      />
    );

    expect(screen.getByText('已选择 3 项')).toBeInTheDocument();
  });

  it('calls onCreate when create button is clicked', () => {
    render(
      <AssetToolbar
        searchQuery=""
        onSearchChange={mockOnSearchChange}
        viewMode="card"
        onViewModeChange={mockOnViewModeChange}
        onCreate={mockOnCreate}
      />
    );

    const createButton = screen.getByText('新建资产');
    fireEvent.click(createButton);

    expect(mockOnCreate).toHaveBeenCalled();
  });
});

describe('AssetList', () => {
  const mockOnAssetClick = vi.fn();
  const mockOnSelect = vi.fn();
  const mockOnDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders assets in card view', () => {
    render(
      <AssetList
        assets={mockAssets}
        viewMode="card"
        onAssetClick={mockOnAssetClick}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('用户数据表')).toBeInTheDocument();
    expect(screen.getByText('MySQL 主库')).toBeInTheDocument();
    expect(screen.getByText('房产知识库')).toBeInTheDocument();
  });

  it('renders assets in list view', () => {
    render(
      <AssetList
        assets={mockAssets}
        viewMode="list"
        onAssetClick={mockOnAssetClick}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('类型')).toBeInTheDocument();
    expect(screen.getByText('名称')).toBeInTheDocument();
  });

  it('calls onAssetClick when card is clicked', () => {
    render(
      <AssetList
        assets={mockAssets}
        viewMode="card"
        onAssetClick={mockOnAssetClick}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    const assetCard = screen.getByText('用户数据表').closest('div');
    if (assetCard) {
      fireEvent.click(assetCard);
    }

    expect(mockOnAssetClick).toHaveBeenCalled();
  });

  it('shows empty state when no assets', () => {
    render(
      <AssetList
        assets={[]}
        viewMode="card"
        onAssetClick={mockOnAssetClick}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('暂无数据资产')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <AssetList
        assets={[]}
        viewMode="card"
        isLoading={true}
        onAssetClick={mockOnAssetClick}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });
});

describe('CreateAssetModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal when open', () => {
    render(
      <CreateAssetModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('新建资产')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入资产名称')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <CreateAssetModal
        isOpen={false}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.queryByText('新建资产')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <CreateAssetModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const closeButton = screen.getByLabelText('关闭');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('submits form with correct data', async () => {
    render(
      <CreateAssetModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByPlaceholderText('输入资产名称');
    fireEvent.change(nameInput, { target: { value: '测试资产' } });

    const submitButton = screen.getByText('创建资产');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: '测试资产',
        })
      );
    });
  });

  it('adds and removes tags', () => {
    render(
      <CreateAssetModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const tagInput = screen.getByPlaceholderText('输入标签后按回车添加');
    fireEvent.change(tagInput, { target: { value: '测试标签' } });

    const addButton = screen.getByText('添加');
    fireEvent.click(addButton);

    expect(screen.getByText('测试标签')).toBeInTheDocument();

    const removeButton = screen.getByText('×');
    fireEvent.click(removeButton);

    expect(screen.queryByText('测试标签')).not.toBeInTheDocument();
  });

  it('shows data source config when type is datasource', () => {
    render(
      <CreateAssetModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const typeSelect = screen.getByDisplayValue('数据集');
    fireEvent.change(typeSelect, { target: { value: 'datasource' } });

    expect(screen.getByText('数据源配置')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('mysql://user:password@host:port/database')).toBeInTheDocument();
  });
});

describe('DataAssetManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();

    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/tree')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTree),
        });
      }
      if (url.includes('/assets') && !url.includes('quality')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              assets: mockAssets,
              total: 3,
              page: 1,
              limit: 20,
              hasMore: false,
            }),
        });
      }
      if (url.includes('quality-stats')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              overall: 85,
              byType: {
                datasource: 90,
                dataset: 85,
                knowledgebase: 80,
              },
              lowQualityAssets: [],
            }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  it('renders main layout', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('数据资产管理')).toBeInTheDocument();
    });
  });

  it('shows sidebar with tree', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('资产目录')).toBeInTheDocument();
    });
  });

  it('shows asset list', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('用户数据表')).toBeInTheDocument();
    });
  });

  it('opens create modal when create button is clicked', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('新建资产')).toBeInTheDocument();
    });

    const createButton = screen.getByText('新建资产');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('新建资产')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('输入资产名称')).toBeInTheDocument();
    });
  });

  it('filters assets by search query', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('搜索资产...')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('搜索资产...');
    fireEvent.change(searchInput, { target: { value: 'MySQL' } });

    await waitFor(() => {
      expect(screen.getByText('MySQL 主库')).toBeInTheDocument();
    });
  });

  it('toggles sidebar visibility', async () => {
    render(<DataAssetManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('数据资产管理')).toBeInTheDocument();
    });

    const toggleButton = screen.getByRole('button', { name: '' });
    fireEvent.click(toggleButton);
  });
});
