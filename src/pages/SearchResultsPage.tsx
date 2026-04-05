import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import { LoadingCard } from '@/components/Loading';
import { EmptyStateWithMascot } from '@/components/mascot';
import DOMPurify from 'dompurify';

interface SearchResult {
  id: string;
  type: string;
  title: string;
  snippet: string;
  created_at: string | null;
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

const SearchResultsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const query = searchParams.get('q') || '';
  const typeFilter = searchParams.get('type') || '';
  
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [inputQuery, setInputQuery] = useState(query);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const search = useCallback(async (searchQuery: string, filter: string, page: number) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const params: Record<string, string | number> = {
        q: searchQuery,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      };
      
      if (filter) {
        params.type = filter;
      }

      const response = await api.get<SearchResponse>('/search', { params });
      setResults(response.data.results);
      setTotal(response.data.total);
    } catch {
      setResults([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (query) {
      setInputQuery(query);
      setCurrentPage(1);
      search(query, typeFilter, 1);
    }
  }, [query, typeFilter, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputQuery.trim()) {
      const params = new URLSearchParams({ q: inputQuery.trim() });
      if (typeFilter) params.set('type', typeFilter);
      setSearchParams(params);
    }
  };

  const handleTypeFilter = (type: string) => {
    const params = new URLSearchParams(searchParams);
    if (type === typeFilter) {
      params.delete('type');
    } else {
      params.set('type', type);
    }
    setSearchParams(params);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    search(query, typeFilter, page);
    window.scrollTo(0, 0);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'task':
        return ClipboardDocumentListIcon;
      case 'report':
        return DocumentTextIcon;
      default:
        return DocumentTextIcon;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'task':
        return '任务';
      case 'report':
        return '报告';
      default:
        return type;
    }
  };

  const getResultLink = (result: SearchResult) => {
    switch (result.type) {
      case 'task':
        return `/tasks/${result.id}`;
      case 'report':
        return `/reports?highlight=${result.id}`;
      default:
        return '#';
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="搜索任务、报告..."
              className="w-full pl-10 pr-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            搜索
          </button>
        </form>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <FunnelIcon className="w-4 h-4" />
          <span>筛选：</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleTypeFilter('task')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              typeFilter === 'task'
                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            任务
          </button>
          <button
            onClick={() => handleTypeFilter('report')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              typeFilter === 'report'
                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            报告
          </button>
        </div>
      </div>

      {isLoading ? (
        <LoadingCard message="搜索中..." />
      ) : query && results.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-6">
          <EmptyStateWithMascot
            type="no-results"
            title="未找到结果"
            description={`没有找到与 "${query}" 相关的任务或报告`}
            message="没有找到匹配的任务，换个关键词试试？"
            actionText="清除搜索"
            onAction={() => {
              setInputQuery('');
              navigate('/search');
            }}
          />
        </div>
      ) : results.length > 0 ? (
        <>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            找到 {total} 个结果
          </p>

          <div className="space-y-4">
            {results.map((result) => {
              const Icon = getTypeIcon(result.type);
              return (
                <Link
                  key={`${result.type}-${result.id}`}
                  to={getResultLink(result)}
                  className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700 p-4 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                          {getTypeLabel(result.type)}
                        </span>
                        {result.created_at && (
                          <span className="text-xs text-gray-400">
                            {new Date(result.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-medium text-gray-900 dark:text-white mb-1 truncate">
                        {result.title}
                      </h3>
                      <p
                        className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2"
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(result.snippet, { ALLOWED_TAGS: ['b', 'strong', 'em', 'span'] }) }}
                      />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                上一页
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let page: number;
                  if (totalPages <= 5) {
                    page = i + 1;
                  } else if (currentPage <= 3) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    page = totalPages - 4 + i;
                  } else {
                    page = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                        currentPage === page
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                下一页
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-6">
          <EmptyStateWithMascot
            type="no-data"
            title="开始搜索"
            description="输入关键词搜索您的任务和报告"
            message="输入关键词，我来帮你找找看～"
            emotion="thinking"
          />
        </div>
      )}
    </div>
  );
};

export default SearchResultsPage;
