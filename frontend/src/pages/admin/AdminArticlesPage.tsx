import React, { useState, useEffect } from 'react';

interface Article {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  cover_image: string;
  author: string;
  tags: string[];
  view_count: number;
  published: boolean;
  created_at: string;
  updated_at: string;
}

const AdminArticlesPage: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [editingArticle, setEditingArticle] = useState<Article | null>(null);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    title: '',
    summary: '',
    content: '',
    cover_image: '',
    tags: '',
    published: false,
  });

  useEffect(() => {
    fetchArticles();
  }, [page, statusFilter]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');
      if (statusFilter) params.append('published', statusFilter);
      if (search) params.append('search', search);

      const response = await fetch(`http://localhost:8000/api/admin/articles?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setArticles(data.articles || []);
        setTotal(data.total || 0);
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

  const openEditModal = (article: Article) => {
    setEditingArticle(article);
    setFormData({
      title: article.title,
      summary: article.summary || '',
      content: article.content || '',
      cover_image: article.cover_image || '',
      tags: article.tags?.join(', ') || '',
      published: article.published,
    });
    setShowModal(true);
  };

  const openCreateModal = () => {
    setEditingArticle(null);
    setFormData({
      title: '',
      summary: '',
      content: '',
      cover_image: '',
      tags: '',
      published: false,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const token = localStorage.getItem('token');
      const url = editingArticle
        ? `http://localhost:8000/api/admin/articles/${editingArticle.id}`
        : 'http://localhost:8000/api/admin/articles';
      const method = editingArticle ? 'PUT' : 'POST';

      const body = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
        slug: formData.title.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, ''),
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        setShowModal(false);
        fetchArticles();
      } else {
        const error = await response.json();
        alert(error.detail || '保存失败');
      }
    } catch (error) {
      console.error('Failed to save article:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此文章吗？')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/articles/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        fetchArticles();
      } else {
        alert('删除失败');
      }
    } catch (error) {
      console.error('Failed to delete article:', error);
      alert('删除失败');
    }
  };

  const handleTogglePublished = async (article: Article) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/articles/${article.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ published: !article.published }),
      });

      if (response.ok) {
        fetchArticles();
      }
    } catch (error) {
      console.error('Failed to toggle published:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">文章管理</h1>
        <button
          onClick={openCreateModal}
          className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
        >
          新建文章
        </button>
      </div>

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索文章..."
            className="flex-1 min-w-[200px] border rounded px-3 py-2"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">全部状态</option>
            <option value="true">已发布</option>
            <option value="false">草稿</option>
          </select>
          <button
            type="submit"
            className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
          >
            搜索
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="text-center py-10">加载中...</div>
        ) : articles.length === 0 ? (
          <div className="text-center py-10 text-gray-500">暂无文章</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">作者</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标签</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">浏览</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {articles.map((article) => (
                <tr key={article.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm">
                    <div className="font-medium">{article.title}</div>
                    <div className="text-gray-500 text-xs truncate max-w-xs">{article.summary}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{article.author}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex flex-wrap gap-1">
                      {article.tags?.slice(0, 2).map((tag) => (
                        <span key={tag} className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {article.view_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleTogglePublished(article)}
                      className={`px-2 py-1 text-xs rounded-full ${
                        article.published
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {article.published ? '已发布' : '草稿'}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(article.created_at).toLocaleDateString('zh-CN')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => openEditModal(article)}
                      className="text-primary hover:underline mr-3"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(article.id)}
                      className="text-red-600 hover:underline"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="bg-white px-4 py-3 flex items-center justify-between border-t">
          <div className="text-sm text-gray-500">共 {total} 条</div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              上一页
            </button>
            <span className="px-3 py-1">第 {page} 页</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={articles.length < 20}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold mb-4">
              {editingArticle ? '编辑文章' : '新建文章'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">摘要</label>
                <textarea
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">内容 (Markdown)</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full border rounded px-3 py-2 font-mono"
                  rows={10}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">封面图片</label>
                <input
                  type="text"
                  value={formData.cover_image}
                  onChange={(e) => setFormData({ ...formData, cover_image: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="图片URL"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标签 (逗号分隔)</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="房产知识, 市场分析"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="published"
                  checked={formData.published}
                  onChange={(e) => setFormData({ ...formData, published: e.target.checked })}
                  className="h-4 w-4 text-primary border-gray-300 rounded"
                />
                <label htmlFor="published" className="ml-2 text-sm text-gray-700">
                  立即发布
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
                >
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminArticlesPage;
