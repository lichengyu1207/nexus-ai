import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Pagination } from '../../components/ui';

interface Article {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  cover_image?: string;
  author: {
    name: string;
    avatar?: string;
  };
  tags: string[];
  view_count: number;
  published_at: string;
  created_at: string;
}

interface BlogPageProps {
  className?: string;
}

const BlogPage: React.FC<BlogPageProps> = ({ className = '' }) => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const tags = ['房产分析', '市场趋势', '购房指南', '投资建议', '政策解读', '案例分享'];

  useEffect(() => {
    fetchArticles();
  }, [page, selectedTag]);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '9',
        ...(selectedTag && { tag: selectedTag }),
        ...(searchTerm && { search: searchTerm }),
      });

      const response = await fetch(
        `http://localhost:8000/api/articles?${params}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (response.ok) {
        const data = await response.json();
        setArticles(data.articles || []);
        setTotalPages(data.total_pages || 1);
      }
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchArticles();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const mockArticles: Article[] = [
    {
      id: '1',
      title: '2024年房产市场趋势分析',
      slug: '2024-market-trends',
      summary: '深入分析2024年房产市场的发展趋势，包括价格走势、政策影响和投资机会。',
      content: '',
      author: { name: '房都督AI团队' },
      tags: ['市场趋势', '投资建议'],
      view_count: 1234,
      published_at: '2024-01-15',
      created_at: '2024-01-15',
    },
    {
      id: '2',
      title: '首次购房者必读指南',
      slug: 'first-time-buyer-guide',
      summary: '为首次购房者提供全面的购房指南，从选房到签约的完整流程解析。',
      content: '',
      author: { name: '房产专家' },
      tags: ['购房指南'],
      view_count: 2345,
      published_at: '2024-01-10',
      created_at: '2024-01-10',
    },
    {
      id: '3',
      title: '学区房投资价值分析',
      slug: 'school-district-investment',
      summary: '详细分析学区房的投资价值，包括租金回报率和升值潜力。',
      content: '',
      author: { name: '投资顾问' },
      tags: ['投资建议', '房产分析'],
      view_count: 3456,
      published_at: '2024-01-05',
      created_at: '2024-01-05',
    },
    {
      id: '4',
      title: '最新房产政策解读',
      slug: 'latest-policy-analysis',
      summary: '解读最新的房产政策变化，分析对购房者的影响。',
      content: '',
      author: { name: '政策研究员' },
      tags: ['政策解读'],
      view_count: 1890,
      published_at: '2024-01-01',
      created_at: '2024-01-01',
    },
    {
      id: '5',
      title: '如何评估房产的真实价值',
      slug: 'property-valuation-guide',
      summary: '教你如何从多个维度评估房产的真实价值，避免买贵。',
      content: '',
      author: { name: '房都督AI团队' },
      tags: ['房产分析', '购房指南'],
      view_count: 2100,
      published_at: '2023-12-28',
      created_at: '2023-12-28',
    },
    {
      id: '6',
      title: '深圳房产市场案例分析',
      slug: 'shenzhen-case-study',
      summary: '通过真实案例分析深圳房产市场的特点和投资机会。',
      content: '',
      author: { name: '市场分析师' },
      tags: ['案例分享', '市场趋势'],
      view_count: 1567,
      published_at: '2023-12-25',
      created_at: '2023-12-25',
    },
  ];

  const displayArticles = articles.length > 0 ? articles : mockArticles;

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      <div className="bg-primary text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl md:text-4xl font-bold text-center mb-4">
            资讯中心
          </h1>
          <p className="text-center text-white/80 max-w-2xl mx-auto">
            专业的房产分析文章、市场趋势解读和购房指南，助您做出明智的房产决策
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1">
            <form onSubmit={handleSearch} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索文章..."
                  className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary text-white px-4 py-1.5 rounded-md text-sm hover:bg-primaryDark transition-colors"
                >
                  搜索
                </button>
              </div>
            </form>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="bg-white rounded-lg shadow animate-pulse">
                    <div className="h-48 bg-gray-200 rounded-t-lg" />
                    <div className="p-4">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-full mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-5/6" />
                    </div>
                  </div>
                ))}
              </div>
            ) : displayArticles.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {displayArticles.map((article) => (
                    <Link
                      key={article.id}
                      to={`/articles/${article.slug}`}
                      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden group"
                    >
                      {article.cover_image ? (
                        <img
                          src={article.cover_image}
                          alt={article.title}
                          className="w-full h-48 object-cover group-hover:scale-105 transition-transform"
                        />
                      ) : (
                        <div className="w-full h-48 bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                          <span className="text-6xl">🏠</span>
                        </div>
                      )}
                      <div className="p-4">
                        <div className="flex flex-wrap gap-2 mb-2">
                          {article.tags.slice(0, 2).map((tag) => (
                            <span
                              key={tag}
                              className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-primary transition-colors">
                          {article.title}
                        </h3>
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                          {article.summary}
                        </p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{article.author.name}</span>
                          <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              {article.view_count}
                            </span>
                            <span>{formatDate(article.published_at)}</span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>

                {totalPages > 1 && (
                  <div className="mt-8">
                    <Pagination
                      currentPage={page}
                      totalPages={totalPages}
                      onPageChange={setPage}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">暂无文章</p>
                <p className="text-sm">请尝试其他搜索条件</p>
              </div>
            )}
          </div>

          <div className="lg:w-72 flex-shrink-0">
            <div className="bg-white rounded-lg shadow p-4 sticky top-4">
              <h3 className="font-semibold text-gray-900 mb-4">热门标签</h3>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    setSelectedTag(null);
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                    selectedTag === null
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  全部
                </button>
                {tags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => {
                      setSelectedTag(tag);
                      setPage(1);
                    }}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                      selectedTag === tag
                        ? 'bg-primary text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>

              <h3 className="font-semibold text-gray-900 mb-4 mt-6">热门文章</h3>
              <div className="space-y-3">
                {displayArticles.slice(0, 5).map((article, index) => (
                  <Link
                    key={article.id}
                    to={`/articles/${article.slug}`}
                    className="flex items-start gap-3 group"
                  >
                    <span className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary rounded text-sm flex items-center justify-center font-medium">
                      {index + 1}
                    </span>
                    <span className="text-sm text-gray-600 group-hover:text-primary transition-colors line-clamp-2">
                      {article.title}
                    </span>
                  </Link>
                ))}
              </div>

              <div className="mt-6 p-4 bg-gradient-to-br from-primary/10 to-purple-500/10 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">订阅资讯</h4>
                <p className="text-sm text-gray-600 mb-3">
                  获取最新房产分析和市场动态
                </p>
                <input
                  type="email"
                  placeholder="输入邮箱"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <button className="w-full bg-primary text-white py-2 rounded-md text-sm hover:bg-primaryDark transition-colors">
                  订阅
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlogPage;
