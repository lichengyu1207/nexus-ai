import React, { useState, useEffect, useCallback } from 'react';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  TrashIcon,
  PencilIcon,
  ArrowUturnLeftIcon,
  UserCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { commentApi, Comment } from '@/services/api';
import showToast from '@/utils/toast';

interface CommentPanelProps {
  reportId: string;
  currentUserId?: string;
}

const CommentPanel: React.FC<CommentPanelProps> = ({ reportId, currentUserId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [expandedReplies, setExpandedReplies] = useState<Set<string>>(new Set());
  const [repliesMap, setRepliesMap] = useState<Record<string, Comment[]>>({});

  const loadComments = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await commentApi.list(reportId, 50, 0);
      setComments(result.comments);
      setTotal(result.total);
    } catch (error) {
      console.error('加载评论失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return;

    try {
      await commentApi.create(reportId, { content: newComment.trim() });
      setNewComment('');
      await loadComments();
      showToast.success('评论发布成功');
    } catch (error) {
      showToast.error('发布评论失败');
    }
  };

  const handleSubmitReply = async (parentId: string) => {
    if (!replyContent.trim()) return;

    try {
      await commentApi.create(reportId, { content: replyContent.trim(), parent_id: parentId });
      setReplyContent('');
      setReplyingTo(null);
      await loadReplies(parentId);
      showToast.success('回复发布成功');
    } catch (error) {
      showToast.error('发布回复失败');
    }
  };

  const handleEditComment = async (commentId: string) => {
    if (!editContent.trim()) return;

    try {
      await commentApi.update(commentId, editContent.trim());
      setEditingId(null);
      setEditContent('');
      await loadComments();
      showToast.success('评论已更新');
    } catch (error) {
      showToast.error('更新评论失败');
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!confirm('确定要删除这条评论吗？')) return;

    try {
      await commentApi.delete(commentId);
      await loadComments();
      showToast.success('评论已删除');
    } catch (error) {
      showToast.error('删除评论失败');
    }
  };

  const loadReplies = async (commentId: string) => {
    try {
      const replies = await commentApi.getReplies(commentId);
      setRepliesMap(prev => ({ ...prev, [commentId]: replies }));
    } catch (error) {
      console.error('加载回复失败:', error);
    }
  };

  const toggleReplies = async (commentId: string) => {
    if (expandedReplies.has(commentId)) {
      setExpandedReplies(prev => {
        const newSet = new Set(prev);
        newSet.delete(commentId);
        return newSet;
      });
    } else {
      setExpandedReplies(prev => new Set(prev).add(commentId));
      if (!repliesMap[commentId]) {
        await loadReplies(commentId);
      }
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderContent = (content: string) => {
    const mentionRegex = /@(\w+(?:\.\w+)*)/g;
    const parts = content.split(mentionRegex);
    
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return (
          <span key={index} className="text-primary-600 font-medium">
            @{part}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            团队讨论
          </h3>
          <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded-full">
            {total} 条评论
          </span>
        </div>
      </div>

      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <UserCircleIcon className="w-8 h-8 text-gray-400" />
          </div>
          <div className="flex-1">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="发表评论，使用 @用户名 可以提及团队成员..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              rows={3}
            />
            <div className="mt-2 flex justify-end">
              <button
                onClick={handleSubmitComment}
                disabled={!newComment.trim()}
                className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                <PaperAirplaneIcon className="w-4 h-4" />
                发布评论
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[500px] overflow-y-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">
            加载中...
          </div>
        ) : comments.length === 0 ? (
          <div className="p-8 text-center">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">暂无评论</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
              成为第一个发表评论的人吧
            </p>
          </div>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="p-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <UserCircleIcon className="w-8 h-8 text-gray-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {comment.full_name || comment.email.split('@')[0]}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatDate(comment.created_at)}
                    </span>
                    {comment.updated_at && comment.updated_at !== comment.created_at && (
                      <span className="text-xs text-gray-400">(已编辑)</span>
                    )}
                  </div>

                  {editingId === comment.id ? (
                    <div className="mt-2">
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
                        rows={3}
                      />
                      <div className="mt-2 flex gap-2">
                        <button
                          onClick={() => handleEditComment(comment.id)}
                          className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(null);
                            setEditContent('');
                          }}
                          className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">
                      {renderContent(comment.content)}
                    </div>
                  )}

                  <div className="mt-2 flex items-center gap-4">
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
                    
                    {currentUserId === comment.user_id && (
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

                    {repliesMap[comment.id] && repliesMap[comment.id].length > 0 && (
                      <button
                        onClick={() => toggleReplies(comment.id)}
                        className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
                      >
                        {expandedReplies.has(comment.id) ? (
                          <>
                            <ChevronUpIcon className="w-3.5 h-3.5" />
                            收起回复
                          </>
                        ) : (
                          <>
                            <ChevronDownIcon className="w-3.5 h-3.5" />
                            {repliesMap[comment.id].length} 条回复
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {replyingTo === comment.id && (
                    <div className="mt-3 pl-4 border-l-2 border-primary-200 dark:border-primary-800">
                      <textarea
                        value={replyContent}
                        onChange={(e) => setReplyContent(e.target.value)}
                        placeholder={`回复 ${comment.full_name || comment.email.split('@')[0]}...`}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 resize-none text-sm"
                        rows={2}
                      />
                      <div className="mt-2 flex gap-2">
                        <button
                          onClick={() => handleSubmitReply(comment.id)}
                          disabled={!replyContent.trim()}
                          className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50"
                        >
                          发送
                        </button>
                        <button
                          onClick={() => {
                            setReplyingTo(null);
                            setReplyContent('');
                          }}
                          className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  )}

                  {expandedReplies.has(comment.id) && repliesMap[comment.id] && (
                    <div className="mt-3 pl-4 border-l-2 border-gray-200 dark:border-gray-700 space-y-3">
                      {repliesMap[comment.id].map((reply) => (
                        <div key={reply.id} className="flex gap-2">
                          <UserCircleIcon className="w-6 h-6 text-gray-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900 dark:text-white text-sm">
                                {reply.full_name || reply.email.split('@')[0]}
                              </span>
                              <span className="text-xs text-gray-400">
                                {formatDate(reply.created_at)}
                              </span>
                            </div>
                            <div className="text-sm text-gray-700 dark:text-gray-300">
                              {renderContent(reply.content)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CommentPanel;
