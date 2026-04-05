import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  TrashIcon,
  PencilIcon,
  ArrowUturnLeftIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import ReportButton from './ReportButton';

export interface Comment {
  id: string;
  report_id: string;
  user_id: string;
  content: string;
  parent_id: string | null;
  mentions: string[] | null;
  email: string;
  full_name: string | null;
  created_at: string | null;
  updated_at: string | null;
  replies?: Comment[];
}

interface CommentSectionProps {
  reportId: string;
  currentUserId?: string;
}

const CommentSection: React.FC<CommentSectionProps> = ({ reportId, currentUserId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [expandedReplies, setExpandedReplies] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadComments = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/reports/${reportId}/comments`);
      setComments(response.data.comments || []);
    } catch {
      showToast.error('加载评论失败');
    } finally {
      setIsLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await api.post(`/reports/${reportId}/comments`, {
        content: newComment.trim(),
      });
      setComments([response.data, ...comments]);
      setNewComment('');
      showToast.success('评论已发布');
    } catch {
      showToast.error('发布评论失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitReply = async (parentId: string) => {
    if (!replyContent.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await api.post(`/reports/${reportId}/comments`, {
        content: replyContent.trim(),
        parent_id: parentId,
      });
      
      setComments(comments.map(c => {
        if (c.id === parentId) {
          return { ...c, replies: [...(c.replies || []), response.data] };
        }
        return c;
      }));
      
      setReplyContent('');
      setReplyingTo(null);
      setExpandedReplies(new Set([...expandedReplies, parentId]));
      showToast.success('回复已发布');
    } catch {
      showToast.error('发布回复失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditComment = async (commentId: string) => {
    if (!editContent.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await api.put(`/comments/${commentId}`, {
        content: editContent.trim(),
      });
      
      setComments(comments.map(c => {
        if (c.id === commentId) {
          return response.data;
        }
        if (c.replies) {
          return { ...c, replies: c.replies.map(r => r.id === commentId ? response.data : r) };
        }
        return c;
      }));
      
      setEditingId(null);
      setEditContent('');
      showToast.success('评论已更新');
    } catch {
      showToast.error('更新评论失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!confirm('确定要删除这条评论吗？')) return;

    try {
      await api.delete(`/comments/${commentId}`);
      setComments(comments.filter(c => c.id !== commentId).map(c => ({
        ...c,
        replies: c.replies?.filter(r => r.id !== commentId) || []
      })));
      showToast.success('评论已删除');
    } catch {
      showToast.error('删除评论失败');
    }
  };

  const loadReplies = async (parentId: string) => {
    try {
      const response = await api.get(`/comments/${parentId}/replies`);
      setComments(comments.map(c => {
        if (c.id === parentId) {
          return { ...c, replies: response.data };
        }
        return c;
      }));
      setExpandedReplies(new Set([...expandedReplies, parentId]));
    } catch {
      showToast.error('加载回复失败');
    }
  };

  const toggleReplies = (commentId: string) => {
    if (expandedReplies.has(commentId)) {
      const newExpanded = new Set(expandedReplies);
      newExpanded.delete(commentId);
      setExpandedReplies(newExpanded);
    } else {
      loadReplies(commentId);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderContent = (content: string) => {
    const mentionRegex = /@(\w+(?:\.\w+)*)/g;
    const parts = content.split(mentionRegex);
    
    return (
      <ReactMarkdown className="prose prose-sm max-w-none">
        {content.replace(mentionRegex, '**@$1**')}
      </ReactMarkdown>
    );
  };

  const CommentItem: React.FC<{ comment: Comment; isReply?: boolean }> = ({ comment, isReply = false }) => {
    const isOwner = currentUserId === comment.user_id;

    return (
      <div className={`${isReply ? 'ml-8 mt-3' : ''}`}>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <UserCircleIcon className="w-5 h-5 text-primary-600" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900 text-sm">
                {comment.full_name || comment.email}
              </span>
              <span className="text-xs text-gray-400">
                {formatDate(comment.created_at)}
              </span>
              {comment.updated_at && (
                <span className="text-xs text-gray-400">(已编辑)</span>
              )}
            </div>

            {editingId === comment.id ? (
              <div className="mt-2">
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                  rows={3}
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => handleEditComment(comment.id)}
                    disabled={isSubmitting}
                    className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50"
                  >
                    保存
                  </button>
                  <button
                    onClick={() => { setEditingId(null); setEditContent(''); }}
                    className="px-3 py-1 text-gray-600 text-sm hover:text-gray-800"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-1 text-sm text-gray-700">
                {renderContent(comment.content)}
              </div>
            )}

            <div className="flex items-center gap-3 mt-2">
              {!isReply && (
                <button
                  onClick={() => {
                    setReplyingTo(replyingTo === comment.id ? null : comment.id);
                    setReplyContent('');
                  }}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600"
                >
                  <ArrowUturnLeftIcon className="w-3.5 h-3.5" />
                  回复
                </button>
              )}
              {isOwner && (
                <>
                  <button
                    onClick={() => {
                      setEditingId(comment.id);
                      setEditContent(comment.content);
                    }}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600"
                  >
                    <PencilIcon className="w-3.5 h-3.5" />
                    编辑
                  </button>
                  <button
                    onClick={() => handleDeleteComment(comment.id)}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600"
                  >
                    <TrashIcon className="w-3.5 h-3.5" />
                    删除
                  </button>
                </>
              )}
              {!isOwner && (
                <ReportButton
                  type="comment"
                  id={comment.id}
                  title={comment.content.slice(0, 50)}
                  variant="text"
                />
              )}
            </div>

            {replyingTo === comment.id && (
              <div className="mt-3">
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="写下你的回复..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                  rows={2}
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => handleSubmitReply(comment.id)}
                    disabled={isSubmitting || !replyContent.trim()}
                    className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50"
                  >
                    发送回复
                  </button>
                  <button
                    onClick={() => { setReplyingTo(null); setReplyContent(''); }}
                    className="px-3 py-1 text-gray-600 text-sm hover:text-gray-800"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}

            {!isReply && comment.replies && comment.replies.length > 0 && (
              <button
                onClick={() => toggleReplies(comment.id)}
                className="mt-2 text-xs text-primary-600 hover:text-primary-700"
              >
                {expandedReplies.has(comment.id) ? '隐藏回复' : `查看 ${comment.replies.length} 条回复`}
              </button>
            )}

            {expandedReplies.has(comment.id) && comment.replies && (
              <div className="mt-3 space-y-3">
                {comment.replies.map((reply) => (
                  <CommentItem key={reply.id} comment={reply} isReply />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold text-gray-900">评论</h3>
          <span className="text-sm text-gray-500">({comments.length})</span>
        </div>
      </div>

      {/* Comment Form */}
      <div className="p-4 border-b border-gray-100">
        <form onSubmit={handleSubmitComment}>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="写下你的评论... 使用 @用户名 来提及其他人"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={3}
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-gray-400">
              支持 Markdown 格式，@提及团队成员
            </span>
            <button
              type="submit"
              disabled={isSubmitting || !newComment.trim()}
              className="flex items-center gap-1 px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <PaperAirplaneIcon className="w-4 h-4" />
              发布评论
            </button>
          </div>
        </form>
      </div>

      {/* Comments List */}
      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : comments.length === 0 ? (
          <div className="text-center py-8">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">暂无评论</p>
            <p className="text-sm text-gray-400 mt-1">成为第一个评论的人吧</p>
          </div>
        ) : (
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="pb-4 border-b border-gray-100 last:border-b-0">
                <CommentItem comment={comment} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentSection;
