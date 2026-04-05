import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface Article {
  id: string;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  view_count: number;
  like_count: number;
  comment_count: number;
  published_at: string;
  created_at: string;
}

interface Comment {
  id: string;
  user_id: string;
  content: string;
  created_at: string;
}

const ArticleDetailPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');

  useEffect(() => {
    fetchArticle();
  }, [slug]);

  const fetchArticle = async () => {
    setLoading(true);
    try {
      const [articleRes, commentsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/articles/${slug}`).then(r => r.json()),
        fetch(`http://localhost:8000/api/articles/${slug}/comments`).then(r => r.json()),
      ]);
      setArticle(articleRes);
      setComments(commentsRes.comments || []);
    } catch (error) {
      console.error('Failed to fetch article:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!commentText.trim() || !article) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`http://localhost:8000/api/articles/${article.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content: commentText }),
      });
      setCommentText('');
      fetchArticle();
    } catch (error) {
      console.error('Failed to submit comment:', error);
    }
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

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      news: 'bg-blue-100 text-blue-700',
      tutorial: 'bg-green-100 text-green-700',
      analysis: 'bg-purple-100 text-purple-700',
      update: 'bg-orange-100 text-orange-700',
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="p-6 text-center">
        <h2 className="text-xl text-gray-500">文章未找到</h2>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">{article.title}</h1>

      <div className="flex items-center gap-4 mb-6 text-sm text-gray-500">
        <span className={`px-2 py-1 rounded ${getCategoryColor(article.category)}`}>
          {getCategoryName(article.category)}
        </span>
        <span>{new Date(article.published_at || article.created_at).toLocaleDateString('zh-CN')}</span>
        <span>{article.view_count} 阅读</span>
      </div>

      <hr className="mb-6" />

      <div 
        className="prose max-w-none"
        dangerouslySetInnerHTML={{ __html: article.content.replace(/\n/g, '<br/>') }}
      />

      {article.tags.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {article.tags.map((tag) => (
            <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm">
              {tag}
            </span>
          ))}
        </div>
      )}

      <hr className="my-8" />

      <h2 className="text-xl font-bold mb-4">评论 ({article.comment_count})</h2>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <textarea
          className="w-full border border-gray-300 rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-primary/50"
          rows={3}
          placeholder="写下你的评论..."
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
        />
        <div className="mt-2 text-right">
          <button
            onClick={handleSubmitComment}
            disabled={!commentText.trim()}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primaryDark disabled:opacity-50"
          >
            发表评论
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {comments.map((comment) => (
          <div key={comment.id} className="flex gap-3 p-4 bg-white rounded-lg shadow">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium">
              U
            </div>
            <div className="flex-1">
              <div className="flex justify-between text-sm text-gray-500 mb-1">
                <span>用户</span>
                <span>{new Date(comment.created_at).toLocaleDateString('zh-CN')}</span>
              </div>
              <p className="text-gray-700">{comment.content}</p>
            </div>
          </div>
        ))}
        {comments.length === 0 && (
          <p className="text-center text-gray-500 py-4">暂无评论</p>
        )}
      </div>
    </div>
  );
};

export default ArticleDetailPage;
