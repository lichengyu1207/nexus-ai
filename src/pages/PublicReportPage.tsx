import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { DocumentTextIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import { ReportContent } from '@/services/reports';
import { LoadingCard } from '@/components/Loading';

interface PublicReport {
  id: string;
  task_id: string;
  status: string;
  content: ReportContent | null;
  summary: string | null;
  version: number;
  created_at: string | null;
  completed_at: string | null;
}

const sectionLabels: Record<string, string> = {
  summary: '执行摘要',
  key_findings: '核心发现',
  detailed_analysis: '详细分析',
  investment_advice: '投资建议',
  risk_warning: '风险提示',
  data_sources: '数据来源',
};

const PublicReportPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [report, setReport] = useState<PublicReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('summary');

  useEffect(() => {
    loadReport();
  }, [token]);

  const loadReport = async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get(`/public/reports/${token}`);
      setReport(response.data);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || '报告不存在或已取消分享');
    } finally {
      setIsLoading(false);
    }
  };

  const getStyleLabel = (style: string): string => {
    switch (style) {
      case 'conservative': return '保守型';
      case 'aggressive': return '进取型';
      default: return '平衡型';
    }
  };

  const getStyleColor = (style: string): string => {
    switch (style) {
      case 'conservative': return 'bg-blue-100 text-blue-700';
      case 'aggressive': return 'bg-orange-100 text-orange-700';
      default: return 'bg-green-100 text-green-700';
    }
  };

  if (isLoading) {
    return <LoadingCard message="加载报告..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center max-w-md">
          <ExclamationCircleIcon className="w-16 h-16 text-red-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">无法访问报告</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/login"
            className="inline-block px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            登录查看更多
          </Link>
        </div>
      </div>
    );
  }

  if (!report || !report.content) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center max-w-md">
          <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">报告内容为空</h2>
          <p className="text-gray-600">该报告暂无内容</p>
        </div>
      </div>
    );
  }

  const sections = report.content.sections || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">房</span>
              </div>
              <span className="text-lg font-bold text-gray-900">房都督AI</span>
            </div>
            <Link
              to="/login"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              登录 / 注册
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Report Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">房产分析报告</h1>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStyleColor(report.content.style)}`}>
                {getStyleLabel(report.content.style)}
              </span>
              <span className="text-sm text-gray-500">
                生成时间: {new Date(report.content.generated_at).toLocaleString('zh-CN')}
              </span>
            </div>
          </div>

          {/* Section Navigation */}
          <div className="border-t border-gray-100 overflow-x-auto">
            <nav className="flex">
              {Object.entries(sectionLabels).map(([key, label]) => {
                if (!sections[key as keyof typeof sections]) return null;
                return (
                  <button
                    key={key}
                    onClick={() => setActiveSection(key)}
                    className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                      activeSection === key
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Report Content */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {/* Summary */}
          {activeSection === 'summary' && sections.summary && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">执行摘要</h2>
              <div className="prose prose-sm max-w-none">
                <p className="text-gray-700">{sections.summary.text || ''}</p>
              </div>
            </div>
          )}

          {/* Key Findings */}
          {activeSection === 'key_findings' && sections.key_findings && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">核心发现</h2>
              <div className="space-y-3">
                {(sections.key_findings as Array<{ title: string; description: string; confidence: number }>).map((finding, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{finding.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{finding.description}</p>
                      </div>
                      <span className="text-xs text-gray-500">{(finding.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Analysis */}
          {activeSection === 'detailed_analysis' && sections.detailed_analysis && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">详细分析</h2>
              <div className="space-y-4">
                {Object.entries(sections.detailed_analysis as Record<string, Record<string, string>>).map(([key, value]) => (
                  <div key={key} className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-medium text-gray-900 mb-2">{key}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(value).map(([k, v]) => (
                        <div key={k}>
                          <span className="text-xs text-gray-500">{k}</span>
                          <p className="font-medium text-gray-900 mt-1">{v}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Investment Advice */}
          {activeSection === 'investment_advice' && sections.investment_advice && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">投资建议</h2>
              <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm text-primary-600">综合评级</span>
                    <p className="text-2xl font-bold text-primary-700">
                      {(sections.investment_advice as { overall_rating: string }).overall_rating}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-primary-600">操作建议</span>
                    <p className="text-lg font-semibold text-primary-700">
                      {(sections.investment_advice as { action_recommendation: string }).action_recommendation}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Risk Warning */}
          {activeSection === 'risk_warning' && sections.risk_warning && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">风险提示</h2>
              <div className="space-y-3">
                {(sections.risk_warning as string[]).map((warning, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <ExclamationCircleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-yellow-800 text-sm">{warning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Sources */}
          {activeSection === 'data_sources' && sections.data_sources && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">数据来源</h2>
              <div className="space-y-2">
                {(sections.data_sources as Array<{ name: string; type: string; description: string }>).map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="font-medium text-gray-900">{source.name}</span>
                      <p className="text-sm text-gray-500">{source.description}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      source.type === 'real' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {source.type === 'real' ? '真实数据' : '模拟数据'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Watermark */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-400">
            由 <span className="font-medium text-primary-600">房都督AI</span> 智能生成
          </p>
          <p className="text-xs text-gray-300 mt-1">
            本报告仅供参考，不构成投资建议
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              © 2024 房都督AI - 智能房产分析平台
            </p>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-sm text-gray-500 hover:text-gray-700">
                登录
              </Link>
              <Link to="/register" className="text-sm text-gray-500 hover:text-gray-700">
                注册
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PublicReportPage;
