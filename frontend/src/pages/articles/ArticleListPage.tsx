import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Article {
  id: string;
  title: string;
  slug: string;
  summary: string;
  cover_image: string;
  category: string;
  tags: string[];
  view_count: number;
  like_count: number;
  comment_count: number;
  is_featured: boolean;
  published_at: string;
  created_at: string;
}

const ArticleListPage: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchArticles();
  }, [page]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/articles?page=${page}&page_size=9`);
      const data = await res.json();
      setArticles(data.articles || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      news: 'bg-blue-100 text-blue-700',
      tutorial: 'bg-green-100 text-green-700',
      analysis: 'bg-purple-100 text-purple-700',
      update: 'bg-orange-100 text-orange-700',
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  const getCategoryName = (category: string): string => {
    const names: Record<string, string> = {
      news: '新闻',
      tutorial: '教程',
      analysis: '分析',
      update: '更新',
    };
    return names[category] || category;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">资讯中心</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {articles.map((article) => (
          <div
            key={article.id}
            className="bg-white rounded-lg shadow overflow-hidden cursor-pointer transition-all hover:-translate-y-1 hover:shadow-lg"
            onClick={() => navigate(`/articles/${article.slug || article.id}`)}
          >
            {article.cover_image && (
              <img
                src={article.cover_image}
                alt={article.title}
                className="w-full h-36 object-cover"
              />
            )}
            <div className="p-4">
              <div className="flex gap-2 mb-2">
                <span className={`px-2 py-0.5 rounded text-xs ${getCategoryColor(article.category)}`}>
                  {getCategoryName(article.category)}
                </span>
                {article.is_featured && (
                  <span className="px-2 py-0.5 rounded text-xs bg-pink-100 text-pink-700">
                    精选
                  </span>
                )}
              </div>
              <h3 className="font-medium text-lg truncate">{article.title}</h3>
              <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                {article.summary}
              </p>
              <div className="flex justify-between items-center mt-3 text-xs text-gray-400">
                <span>{new Date(article.published_at || article.created_at).toLocaleDateString('zh-CN')}</span>
                <span>{article.view_count} 阅读</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {total > 9 && (
        <div className="flex justify-center mt-8 gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            上一页
          </button>
          <span className="px-4 py-2">
            第 {page} / {Math.ceil(total / 9)} 页
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= Math.ceil(total / 9)}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default ArticleListPage;
