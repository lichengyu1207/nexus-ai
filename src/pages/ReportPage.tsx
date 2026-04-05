import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  DocumentTextIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  SparklesIcon,
  ShareIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import { reportApi, Report, ReportContent, ReportChunk } from '@/services/reports';
import ReportRenderer from '@/components/ReportRenderer';
import VersionSelector, { ReportVersion } from '@/components/VersionSelector';
import ReportCompare from '@/components/ReportCompare';
import CommentSection from '@/components/CommentSection';
import ExportButton from '@/components/ExportButton';
import Spinner, { LoadingCard } from '@/components/Loading';
import showToast from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/services/api';
import CharacterAvatar from '@/components/CharacterAvatar';
import PersonaSeal from '@/components/PersonaSeal';
import Dudu from '@/components/Dudu';

interface DiffResult {
  sections: Record<string, {
    status: 'added' | 'removed' | 'modified';
    current: unknown;
    compare: unknown;
  }>;
  summary: {
    status: 'modified';
    current: unknown;
    compare: unknown;
  } | null;
  added: string[];
  removed: string[];
  modified: string[];
}

const ReportPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const { user } = useAuth();
  
  const [report, setReport] = useState<Report | null>(null);
  const [reportContent, setReportContent] = useState<ReportContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState(0);
  const [persona, setPersona] = useState<'zhouyu' | 'luxun'>('zhouyu');
  
  const [versions, setVersions] = useState<ReportVersion[]>([]);
  const [currentVersion, setCurrentVersion] = useState<number>(1);
  const [compareVersion, setCompareVersion] = useState<number | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [compareContent, setCompareContent] = useState<ReportContent | null>(null);
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [shareInfo, setShareInfo] = useState<{ is_public: boolean; share_token: string | null; share_url: string | null } | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);

  const loadReport = useCallback(async () => {
    if (!taskId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const [data, versionsData] = await Promise.all([
        reportApi.getByTask(taskId),
        reportApi.getTaskVersions(taskId),
      ]);
      
      setReport(data);
      setVersions(versionsData.versions || []);
      setCurrentVersion(data.version || 1);
      
      if (data.status === 'completed' && data.content) {
        setReportContent(data.content);
        setProgress(100);
        
        try {
          const shareResponse = await api.get(`/reports/${data.id}/share`);
          setShareInfo(shareResponse.data);
        } catch {
          // Share info not available
        }
      } else if (data.status === 'generating') {
        setProgress(data.progress || 0);
        startStreaming();
      } else if (data.status === 'failed') {
        setError(data.error_message || '报告生成失败');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '加载报告失败';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  const startStreaming = useCallback(() => {
    if (!taskId || eventSourceRef.current) return;
    
    setIsStreaming(true);
    
    const es = reportApi.streamReport(
      taskId,
      handleChunk,
      handleComplete,
      handleError,
      () => console.log('SSE connected')
    );
    
    eventSourceRef.current = es;
  }, [taskId]);

  const handleChunk = (chunk: ReportChunk) => {
    setProgress(chunk.progress);
    
    setReportContent(prev => {
      if (!prev) {
        return {
          task_id: chunk.task_id,
          style: 'balanced',
          generated_at: new Date().toISOString(),
          sections: { [chunk.section]: chunk.content },
        };
      }
      
      return {
        ...prev,
        sections: { ...prev.sections, [chunk.section]: chunk.content },
      };
    });
  };

  const handleComplete = (content: ReportContent) => {
    setReportContent(content);
    setProgress(100);
    setIsStreaming(false);
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    showToast.success('报告生成完成');
    loadReport();
  };

  const handleError = (errorMsg: string) => {
    setError(errorMsg);
    setIsStreaming(false);
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    showToast.error(errorMsg);
  };

  const handleRetry = async () => {
    if (!report) return;
    
    try {
      await reportApi.retry(report.id);
      setError(null);
      setProgress(0);
      setReportContent(null);
      loadReport();
      showToast.success('已重新开始生成报告');
    } catch {
      showToast.error('重试失败');
    }
  };

  const handleShare = async () => {
    if (!report) return;
    
    try {
      const response = await api.post(`/reports/${report.id}/share`);
      setShareInfo(response.data);
      showToast.success('分享链接已生成');
    } catch {
      showToast.error('生成分享链接失败');
    }
  };

  const handleRevokeShare = async () => {
    if (!report) return;
    
    try {
      await api.delete(`/reports/${report.id}/share`);
      setShareInfo({ is_public: false, share_token: null, share_url: null });
      showToast.success('分享已撤销');
    } catch {
      showToast.error('撤销分享失败');
    }
  };

  const handleCopyShareLink = () => {
    if (!shareInfo?.share_url) return;
    
    const fullUrl = `${window.location.origin}${shareInfo.share_url}`;
    navigator.clipboard.writeText(fullUrl);
    showToast.success('链接已复制到剪贴板');
  };

  const handleVersionChange = async (version: number) => {
    if (!taskId || version === currentVersion) return;
    
    try {
      const versions = await reportApi.getTaskVersions(taskId);
      const targetVersion = versions.versions.find((v: ReportVersion) => v.version === version);
      
      if (targetVersion) {
        const reportData = await reportApi.getById(targetVersion.id);
        setReport(reportData);
        setReportContent(reportData.content);
        setCurrentVersion(version);
        setCompareVersion(null);
        setCompareContent(null);
        setDiff(null);
        setIsComparing(false);
      }
    } catch {
      showToast.error('加载版本失败');
    }
  };

  const handleCompareChange = async (version: number | null) => {
    setCompareVersion(version);
    
    if (!version || !report) {
      setCompareContent(null);
      setDiff(null);
      return;
    }
    
    try {
      const result = await reportApi.compareVersions(report.id, version);
      setCompareContent(result.compare_content);
      setDiff(result.diff);
    } catch {
      showToast.error('加载对比版本失败');
    }
  };

  const handleToggleCompare = () => {
    setIsComparing(!isComparing);
    if (isComparing) {
      setCompareVersion(null);
      setCompareContent(null);
      setDiff(null);
    }
  };

  useEffect(() => {
    loadReport();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [loadReport]);

  const getStatusBadge = () => {
    if (!report) return null;
    
    const configs: Record<string, { bg: string; text: string; label: string }> = {
      completed: { bg: 'bg-green-100', text: 'text-green-700', label: '已完成' },
      failed: { bg: 'bg-red-100', text: 'text-red-700', label: '失败' },
      generating: { bg: 'bg-blue-100', text: 'text-blue-700', label: '生成中' },
      pending: { bg: 'bg-gray-100', text: 'text-gray-700', label: '等待中' },
      archived: { bg: 'bg-gray-100', text: 'text-gray-600', label: '已归档' },
    };
    
    const config = configs[report.status] || configs.pending;
    
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  if (isLoading) {
    return <LoadingCard message="加载报告中..." />;
  }

  if (error && !reportContent) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
          <ExclamationCircleIcon className="w-16 h-16 text-red-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">报告加载失败</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <ArrowPathIcon className="w-4 h-4" />
              重试
            </button>
            <Link
              to={`/tasks/${taskId}`}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              查看任务详情
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            to={`/tasks/${taskId}`}
            className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            返回任务详情
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2 flex items-center gap-3">
            <DocumentTextIcon className="w-7 h-7 text-primary-600" />
            分析报告
            {report?.version && report.version > 1 && (
              <span className="text-sm font-normal text-gray-500">
                版本 {report.version}
              </span>
            )}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {report?.status === 'completed' && (
            <>
              <ExportButton type="report" reportId={report.id} />
              <div className="flex items-center gap-2">
                {shareInfo?.is_public ? (
                  <>
                    <button
                      onClick={handleCopyShareLink}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-200 dark:hover:bg-primary-900/50"
                    >
                      <LinkIcon className="w-4 h-4" />
                      复制链接
                    </button>
                    <button
                      onClick={handleRevokeShare}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      取消分享
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleShare}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <ShareIcon className="w-4 h-4" />
                    分享
                  </button>
                )}
              </div>
            </>
          )}
          {isStreaming && (
            <span className="flex items-center gap-2 text-sm text-blue-600">
              <SparklesIcon className="w-4 h-4 animate-pulse" />
              正在生成...
            </span>
          )}
          {getStatusBadge()}
        </div>
      </div>

      {/* Version Selector */}
      {versions.length > 1 && !isStreaming && (
        <VersionSelector
          versions={versions}
          currentVersion={currentVersion}
          compareVersion={compareVersion}
          onVersionChange={handleVersionChange}
          onCompareChange={handleCompareChange}
          isComparing={isComparing}
          onToggleCompare={handleToggleCompare}
        />
      )}

      {/* Compare View */}
      {isComparing && compareVersion && compareContent && diff && reportContent ? (
        <ReportCompare
          currentContent={reportContent}
          compareContent={compareContent}
          currentVersion={currentVersion}
          compareVersion={compareVersion}
          diff={diff}
        />
      ) : reportContent ? (
        <ReportRenderer
          report={reportContent}
          reportId={report?.id}
          taskId={taskId}
          progress={progress}
          isStreaming={isStreaming}
        />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Spinner size="lg" />
          </div>
          <h3 className="text-lg font-medium text-gray-900">报告生成中</h3>
          <p className="text-gray-500 mt-2">请稍候，报告正在生成...</p>
          {progress > 0 && (
            <div className="mt-4 max-w-xs mx-auto">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600">进度</span>
                <span className="font-medium text-primary-600">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Failed State */}
      {report?.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <ExclamationCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-700">报告生成失败</h3>
              <p className="text-red-600 text-sm mt-1">{report.error_message}</p>
              <button
                onClick={handleRetry}
                className="mt-3 flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
              >
                <ArrowPathIcon className="w-4 h-4" />
                重新生成
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments Section */}
      {report?.status === 'completed' && report?.id && (
        <CommentSection reportId={report.id} currentUserId={user?.id} />
      )}
    </div>
  );
};

export default ReportPage;
