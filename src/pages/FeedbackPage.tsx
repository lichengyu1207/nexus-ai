import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  LightBulbIcon,
  BugAntIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
  ClockIcon,
  CheckCircleIcon,
  EyeIcon,
  XMarkIcon,
  ArrowLeftIcon,
  CloudArrowUpIcon,
} from '@heroicons/react/24/outline';
import { useDropzone } from 'react-dropzone';
import {
  submitFeedback,
  getMyFeedbacks,
  getFeedbackDetail,
  uploadAttachment,
  feedbackTypes,
  feedbackStatus,
  Feedback as FeedbackType,
} from '@/api/feedback';
import showToast from '@/utils/toast';
import { useMascotToast } from '@/components/mascot';

type ViewMode = 'form' | 'history' | 'detail';

const FEEDBACK_TYPE_OPTIONS = [
  { value: 'feedback', label: '功能反馈', icon: ChatBubbleLeftRightIcon, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/20' },
  { value: 'suggestion', label: '建议', icon: LightBulbIcon, color: 'text-yellow-500', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20' },
  { value: 'bug', label: '问题报告', icon: BugAntIcon, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/20' },
  { value: 'complaint', label: '投诉', icon: ExclamationTriangleIcon, color: 'text-orange-500', bgColor: 'bg-orange-50 dark:bg-orange-900/20' },
];

const FeedbackPage: React.FC = () => {
  const navigate = useNavigate();
  const { showFeedbackSent } = useMascotToast();
  const [viewMode, setViewMode] = useState<ViewMode>('form');
  const [feedbacks, setFeedbacks] = useState<FeedbackType[]>([]);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackType | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 10;

  const [type, setType] = useState<string>('feedback');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [attachmentUrls, setAttachmentUrls] = useState<string[]>([]);

  useEffect(() => {
    if (viewMode === 'history') {
      loadFeedbacks();
    }
  }, [viewMode, currentPage]);

  const loadFeedbacks = async () => {
    setLoading(true);
    try {
      const result = await getMyFeedbacks(pageSize * currentPage);
      setFeedbacks(result.items);
      setTotalItems(result.total);
    } catch (error) {
      showToast.error('获取反馈列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (feedbackId: string) => {
    setLoading(true);
    try {
      const detail = await getFeedbackDetail(feedbackId);
      setSelectedFeedback(detail);
      setViewMode('detail');
    } catch (error) {
      showToast.error('获取详情失败');
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp'],
    },
    maxFiles: 5,
    maxSize: 5 * 1024 * 1024,
    onDrop: (acceptedFiles, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        showToast.error('部分文件不符合要求（最大5张，每张不超过5MB）');
      }
      if (acceptedFiles.length + attachments.length > 5) {
        showToast.error('最多上传5张图片');
        return;
      }
      setAttachments((prev) => [...prev, ...acceptedFiles].slice(0, 5));
    },
  });

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      showToast.error('请填写反馈内容');
      return;
    }
    if (content.length < 10) {
      showToast.error('反馈内容至少10个字符');
      return;
    }

    setSubmitting(true);
    try {
      let uploadedUrls: string[] = [];
      if (attachments.length > 0) {
        showToast.info('正在上传附件...');
        for (const file of attachments) {
          try {
            const url = await uploadAttachment(file);
            uploadedUrls.push(url);
          } catch (error) {
            console.error('Failed to upload file:', error);
          }
        }
      }

      await submitFeedback({
        type,
        title: title || undefined,
        content,
        attachments: uploadedUrls.length > 0 ? uploadedUrls : undefined,
      });

      showFeedbackSent();
      setType('feedback');
      setTitle('');
      setContent('');
      setAttachments([]);
      setAttachmentUrls([]);
      setViewMode('history');
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const renderForm = () => (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">提交反馈</h2>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            反馈类型
          </label>
          <div className="grid grid-cols-2 gap-3">
            {FEEDBACK_TYPE_OPTIONS.map((option) => {
              const Icon = option.icon;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setType(option.value)}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    type === option.value
                      ? `border-primary-500 ${option.bgColor}`
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <Icon className={`w-6 h-6 ${option.color}`} />
                  <span className="font-medium text-gray-900 dark:text-white">{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            标题（可选）
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="简要描述您的反馈"
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            maxLength={100}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            详细内容 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="请详细描述您的反馈、建议或遇到的问题（至少10个字符）..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={6}
            maxLength={2000}
          />
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-400">最少10个字符</span>
            <span className="text-xs text-gray-400">{content.length}/2000</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            附件上传（可选，最多5张图片）
          </label>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <CloudArrowUpIcon className="w-10 h-10 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {isDragActive ? '松开以上传文件' : '拖拽图片到这里，或点击选择文件'}
            </p>
            <p className="text-xs text-gray-400 mt-1">支持 JPG、PNG、GIF，每张最大5MB</p>
          </div>

          {attachments.length > 0 && (
            <div className="mt-4 grid grid-cols-5 gap-3">
              {attachments.map((file, index) => (
                <div key={index} className="relative group">
                  <img
                    src={URL.createObjectURL(file)}
                    alt={`附件 ${index + 1}`}
                    className="w-full h-20 object-cover rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={() => removeAttachment(index)}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            感谢您的反馈！我们会认真对待每一条意见，并在必要时通过站内信回复您。
          </p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitting || content.length < 10}
          className="w-full py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
        >
          <PaperAirplaneIcon className="w-5 h-5" />
          {submitting ? '提交中...' : '提交反馈'}
        </button>
      </div>
    </div>
  );

  const renderHistory = () => {
    const totalPages = Math.ceil(totalItems / pageSize);
    
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">我的反馈记录</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">共 {totalItems} 条记录</p>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : feedbacks.length === 0 ? (
          <div className="p-8 text-center">
            <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">暂无反馈记录</p>
            <button
              onClick={() => setViewMode('form')}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              提交第一条反馈
            </button>
          </div>
        ) : (
          <>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {feedbacks.map((feedback) => {
                const statusConfig = feedbackStatus[feedback.status] || feedbackStatus.pending;
                return (
                  <div
                    key={feedback.id}
                    className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                    onClick={() => handleViewDetail(feedback.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {feedback.title || feedback.content.slice(0, 30)}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs ${statusConfig.color}`}>
                            {statusConfig.label}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                          {feedback.content}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                          <span>{feedbackTypes[feedback.type] || feedback.type}</span>
                          <span>{formatDate(feedback.created_at)}</span>
                          {feedback.admin_reply && (
                            <span className="text-green-500 flex items-center gap-1">
                              <CheckCircleIcon className="w-3 h-3" />
                              已回复
                            </span>
                          )}
                        </div>
                      </div>
                      <EyeIcon className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                );
              })}
            </div>
            
            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  上一页
                </button>
                <span className="text-sm text-gray-500">
                  第 {currentPage} / {totalPages} 页
                </span>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  const renderDetail = () => {
    if (!selectedFeedback) return null;

    const statusConfig = feedbackStatus[selectedFeedback.status] || feedbackStatus.pending;

    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setViewMode('history')}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            返回列表
          </button>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {selectedFeedback.title || '反馈详情'}
            </h2>
            <span className={`px-3 py-1 rounded-full text-sm ${statusConfig.color}`}>
              {statusConfig.label}
            </span>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">反馈类型</p>
            <p className="font-medium">{feedbackTypes[selectedFeedback.type] || selectedFeedback.type}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">提交时间</p>
            <p className="font-medium">{formatDate(selectedFeedback.created_at)}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">反馈内容</p>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
              <p className="whitespace-pre-wrap">{selectedFeedback.content}</p>
            </div>
          </div>

          {selectedFeedback.attachments && selectedFeedback.attachments.length > 0 && (
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">附件</p>
              <div className="grid grid-cols-5 gap-3">
                {selectedFeedback.attachments.map((url, index) => (
                  <a
                    key={index}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <img
                      src={url}
                      alt={`附件 ${index + 1}`}
                      className="w-full h-20 object-cover rounded-lg hover:opacity-80 transition-opacity"
                    />
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedFeedback.admin_reply && (
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                管理员回复
                {selectedFeedback.replied_at && (
                  <span className="ml-2 text-xs">
                    · {formatDate(selectedFeedback.replied_at)}
                  </span>
                )}
              </p>
              <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-xl p-4">
                <p className="whitespace-pre-wrap text-blue-900 dark:text-blue-100">
                  {selectedFeedback.admin_reply}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">反馈与建议</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('form')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'form'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            提交反馈
          </button>
          <button
            onClick={() => setViewMode('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'history' || viewMode === 'detail'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            历史记录
          </button>
        </div>
      </div>

      {viewMode === 'form' && renderForm()}
      {viewMode === 'history' && renderHistory()}
      {viewMode === 'detail' && renderDetail()}
    </div>
  );
};

export default FeedbackPage;
