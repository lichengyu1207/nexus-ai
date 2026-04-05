import React, { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  DocumentTextIcon,
  ChartBarIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClipboardDocumentIcon,
  ArrowDownTrayIcon,
  CheckIcon,
  SparklesIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import { ReportContent, KeyFinding, DataSource } from '@/services/reports';
import { exportToPDF } from '@/utils/pdfExport';
import showToast from '@/utils/toast';
import { ChartRenderer, ChartConfig } from '@/components/charts';
import DataSourcesPanel from './DataSourcesPanel';
import FeedbackModal from './FeedbackModal';
import ReportButton from './ReportButton';

interface ReportRendererProps {
  report: ReportContent & { charts?: ChartConfig[] };
  reportId?: string;
  taskId?: string;
  progress?: number;
  isStreaming?: boolean;
}

interface DataPointValue {
  title: string;
  value: string | number;
  source?: DataSourceInfo;
  confidence?: number;
  is_estimated?: boolean;
  note?: string;
  confidence_level?: 'high' | 'medium' | 'low';
}

interface DataSourceInfo {
  name: string;
  type: string;
  label: string;
  icon: string;
  reliability: string;
  description: string;
  confidence: number;
  timestamp?: string;
  url?: string;
}

interface AnalysisValue {
  value: string;
  confidence?: number;
  source?: DataSourceInfo;
  is_estimated?: boolean;
}

const ReportRenderer: React.FC<ReportRendererProps> = ({
  report,
  reportId,
  taskId,
  progress = 100,
  isStreaming = false,
}) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('summary');
  const [showSourcesPanel, setShowSourcesPanel] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  const sections = report.sections || {};

  const handleCopy = async () => {
    const text = generatePlainText(report);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    showToast.success('报告已复制到剪贴板');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportPDF = async () => {
    if (!reportRef.current || exporting) return;

    setExporting(true);
    try {
      await exportToPDF(reportRef.current, {
        taskId: taskId || 'unknown',
        title: '房都督AI - 房产分析报告',
      });
      showToast.success('PDF导出成功');
    } catch (error) {
      showToast.error('PDF导出失败');
    } finally {
      setExporting(false);
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

  const getAllSources = (): DataSourceInfo[] => {
    const sources: DataSourceInfo[] = [];
    const sourceIds = new Set<string>();
    
    const addSource = (source?: DataSourceInfo) => {
      if (source && !sourceIds.has(`${source.type}_${source.name}`)) {
        sourceIds.add(`${source.type}_${source.name}`);
        sources.push(source);
      }
    };
    
    if (sections.key_findings) {
      sections.key_findings.forEach((finding: DataPointValue) => {
        addSource(finding.source);
      });
    }
    
    if (sections.data_sources?.sources) {
      sections.data_sources.sources.forEach((source: DataSourceInfo) => {
        addSource(source);
      });
    }
    
    return sources;
  };

  const sectionTabs = [
    { id: 'summary', label: '执行摘要', icon: DocumentTextIcon },
    { id: 'findings', label: '核心发现', icon: ChartBarIcon },
    { id: 'analysis', label: '详细分析', icon: InformationCircleIcon },
    { id: 'advice', label: '投资建议', icon: LightBulbIcon },
    { id: 'risks', label: '风险提示', icon: ExclamationTriangleIcon },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-gray-900">房产分析报告</h2>
                {isStreaming && (
                  <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                    <SparklesIcon className="w-3 h-3 animate-pulse" />
                    生成中
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-2">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStyleColor(report.style)}`}>
                  {getStyleLabel(report.style)}
                </span>
                <span className="text-sm text-gray-500">
                  生成时间: {new Date(report.generated_at).toLocaleString('zh-CN')}
                </span>
                {sections.data_sources?.summary && (
                  <button
                    onClick={() => setShowSourcesPanel(!showSourcesPanel)}
                    className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                  >
                    <InformationCircleIcon className="w-4 h-4" />
                    数据可信度
                  </button>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {!isStreaming && progress === 100 && reportId && (
                <>
                  <button
                    onClick={() => setShowFeedback(true)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    <ChatBubbleLeftRightIcon className="w-4 h-4" />
                    反馈
                  </button>
                  <ReportButton
                    type="report"
                    id={reportId}
                    title={sections.summary?.text?.slice(0, 50) || '分析报告'}
                    variant="button"
                  />
                </>
              )}
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                {copied ? (
                  <>
                    <CheckIcon className="w-4 h-4 text-green-500" />
                    已复制
                  </>
                ) : (
                  <>
                    <ClipboardDocumentIcon className="w-4 h-4" />
                    复制
                  </>
                )}
              </button>
              <button
                onClick={handleExportPDF}
                disabled={exporting || isStreaming}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                {exporting ? '导出中...' : '导出PDF'}
              </button>
            </div>
          </div>

          {isStreaming && progress < 100 && (
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600">生成进度</span>
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

        <div className="border-b border-gray-100 overflow-x-auto">
          <nav className="flex">
            {sectionTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSection(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeSection === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {showSourcesPanel && sections.data_sources && (
        <DataSourcesPanel
          sources={sections.data_sources.sources || []}
          summary={sections.data_sources.summary}
          onClose={() => setShowSourcesPanel(false)}
        />
      )}

      {showFeedback && reportId && (
        <FeedbackModal
          reportId={reportId}
          onClose={() => setShowFeedback(false)}
        />
      )}

      <div
        ref={reportRef}
        id="report-content"
        className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"
      >
        {activeSection === 'summary' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <DocumentTextIcon className="w-5 h-5 text-primary-600" />
              执行摘要
            </h3>
            {sections.summary ? (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{sections.summary.text || ''}</ReactMarkdown>
                <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                  <ConfidenceBadge confidence={sections.summary.confidence || 0.5} />
                  {sections.summary.sources && sections.summary.sources.length > 0 && (
                    <SourceTooltip source={sections.summary.sources[0]} />
                  )}
                </div>
              </div>
            ) : (
              <p className="text-gray-500 italic">摘要生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'findings' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-primary-600" />
              核心发现
            </h3>
            {sections.key_findings && sections.key_findings.length > 0 ? (
              <div className="grid gap-3">
                {sections.key_findings.map((finding: DataPointValue, index: number) => (
                  <DataPointCard key={index} dataPoint={finding} index={index} />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 italic">核心发现生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'analysis' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <InformationCircleIcon className="w-5 h-5 text-primary-600" />
              详细分析
            </h3>
            
            {report.charts && report.charts.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                {report.charts.map((chart) => (
                  <ChartRenderer key={chart.id} chart={chart} />
                ))}
              </div>
            )}
            
            {sections.detailed_analysis ? (
              <>
                {sections.detailed_analysis.market_analysis && (
                  <AnalysisBlockWithConfidence
                    title="市场分析"
                    data={sections.detailed_analysis.market_analysis}
                  />
                )}
                {sections.detailed_analysis.price_analysis && (
                  <AnalysisBlockWithConfidence
                    title="价格分析"
                    data={sections.detailed_analysis.price_analysis}
                  />
                )}
                {sections.detailed_analysis.location_analysis && (
                  <AnalysisBlockWithConfidence
                    title="配套分析"
                    data={sections.detailed_analysis.location_analysis}
                  />
                )}
              </>
            ) : (
              <p className="text-gray-500 italic">详细分析生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'advice' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <LightBulbIcon className="w-5 h-5 text-primary-600" />
              投资建议
            </h3>
            {sections.investment_advice ? (
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm text-primary-600">综合评级</span>
                      <p className="text-2xl font-bold text-primary-700">
                        {typeof sections.investment_advice.overall_rating === 'object' 
                          ? sections.investment_advice.overall_rating.value 
                          : sections.investment_advice.overall_rating}
                      </p>
                      {typeof sections.investment_advice.overall_rating === 'object' && (
                        <ConfidenceBadge confidence={sections.investment_advice.overall_rating.confidence || 0.7} />
                      )}
                    </div>
                    <div className="text-right">
                      <span className="text-sm text-primary-600">操作建议</span>
                      <p className="text-lg font-semibold text-primary-700">
                        {typeof sections.investment_advice.action_recommendation === 'object'
                          ? sections.investment_advice.action_recommendation.value
                          : sections.investment_advice.action_recommendation}
                      </p>
                    </div>
                  </div>
                </div>

                {sections.investment_advice.investment_horizon && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-700 mb-3">投资周期建议</h4>
                    <div className="grid grid-cols-3 gap-3">
                      {['short_term', 'medium_term', 'long_term'].map((term) => {
                        const horizonData = sections.investment_advice.investment_horizon[term];
                        const horizonValue = typeof horizonData === 'object' ? horizonData.value : horizonData;
                        const horizonConfidence = typeof horizonData === 'object' ? horizonData.confidence : undefined;
                        const isEstimated = typeof horizonData === 'object' ? horizonData.is_estimated : false;
                        
                        return (
                          <div key={term} className={`text-center p-3 bg-white rounded-lg ${isEstimated ? 'border-2 border-dashed border-amber-300' : ''}`}>
                            <span className="text-xs text-gray-500">
                              {term === 'short_term' ? '短期' : term === 'medium_term' ? '中期' : '长期'}
                              {isEstimated && <span className="ml-1 text-amber-500">📈</span>}
                            </span>
                            <p className="font-medium text-gray-900 mt-1">{horizonValue}</p>
                            {horizonConfidence && (
                              <ConfidenceBadge confidence={horizonConfidence} size="xs" />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {sections.investment_advice.style_specific_advice && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-700 mb-2">个性化建议</h4>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStyleColor(report.style)}`}>
                        {sections.investment_advice.style_specific_advice.risk_level}
                      </span>
                      <p className="text-gray-700">{sections.investment_advice.style_specific_advice.suggestion}</p>
                    </div>
                  </div>
                )}

                {sections.investment_advice.key_factors && sections.investment_advice.key_factors.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">关键因素</h4>
                    <div className="flex flex-wrap gap-2">
                      {sections.investment_advice.key_factors.map((factor, index) => (
                        <span key={index} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm">
                          {factor}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 italic">投资建议生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'analysis' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <InformationCircleIcon className="w-5 h-5 text-primary-600" />
              详细分析
            </h3>
            
            {report.charts && report.charts.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                {report.charts.map((chart) => (
                  <ChartRenderer key={chart.id} chart={chart} />
                ))}
              </div>
            )}
            
            {sections.detailed_analysis ? (
              <>
                {sections.detailed_analysis.market_analysis && (
                  <AnalysisBlockWithConfidence
                    title="市场分析"
                    data={sections.detailed_analysis.market_analysis}
                  />
                )}
                {sections.detailed_analysis.price_analysis && (
                  <AnalysisBlockWithConfidence
                    title="价格分析"
                    data={sections.detailed_analysis.price_analysis}
                  />
                )}
                {sections.detailed_analysis.location_analysis && (
                  <AnalysisBlockWithConfidence
                    title="配套分析"
                    data={sections.detailed_analysis.location_analysis}
                  />
                )}
              </>
            ) : (
              <p className="text-gray-500 italic">详细分析生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'advice' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <LightBulbIcon className="w-5 h-5 text-primary-600" />
              投资建议
            </h3>
            {sections.investment_advice ? (
              <InvestmentAdviceSection advice={sections.investment_advice} reportStyle={report.style} getStyleColor={getStyleColor} />
            ) : (
              <p className="text-gray-500 italic">投资建议生成中...</p>
            )}
          </div>
        )}

        {activeSection === 'risks' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
              风险提示
            </h3>
            {sections.risk_warning ? (
              <div className="space-y-3">
                {sections.risk_warning.warnings && sections.risk_warning.warnings.map((warning: { text: string; severity: string; confidence: number }, index: number) => (
                  <div 
                    key={index} 
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      warning.severity === 'high' 
                        ? 'bg-red-50 border-red-200' 
                        : warning.severity === 'medium'
                        ? 'bg-yellow-50 border-yellow-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <ExclamationTriangleIcon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                      warning.severity === 'high' ? 'text-red-600' : 'text-yellow-600'
                    }`} />
                    <div className="flex-1">
                      <p className={`text-sm ${
                        warning.severity === 'high' ? 'text-red-800' : 'text-yellow-800'
                      }`}>{warning.text}</p>
                    </div>
                  </div>
                ))}
                
                {sections.risk_warning.disclaimer && (
                  <div className="mt-4 p-4 bg-gray-100 rounded-lg text-sm text-gray-600">
                    <strong>免责声明：</strong>{sections.risk_warning.disclaimer}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 italic">风险提示生成中...</p>
            )}

            {sections.data_sources && sections.data_sources.sources && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <InformationCircleIcon className="w-4 h-4" />
                  数据来源
                </h4>
                <div className="space-y-2">
                  {sections.data_sources.sources.map((source: DataSourceInfo, index: number) => (
                    <DataSourceCard key={index} source={source} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const ConfidenceBadge: React.FC<{ confidence: number; size?: 'xs' | 'sm' }> = ({ confidence, size = 'sm' }) => {
  const getConfidenceStyle = () => {
    if (confidence >= 0.9) return { bg: 'bg-green-100', text: 'text-green-700', label: '高' };
    if (confidence >= 0.7) return { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '中' };
    return { bg: 'bg-red-100', text: 'text-red-700', label: '低' };
  };

  const style = getConfidenceStyle();
  const sizeClass = size === 'xs' ? 'text-xs px-1.5 py-0.5' : 'text-xs px-2 py-0.5';

  return (
    <span className={`${style.bg} ${style.text} ${sizeClass} rounded font-medium`}>
      {style.label} {(confidence * 100).toFixed(0)}%
    </span>
  );
};

const SourceTooltip: React.FC<{ source: DataSourceInfo }> = ({ source }) => {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
      >
        <InformationCircleIcon className="w-4 h-4" />
        <span>{source.icon} {source.label}</span>
      </button>
      
      {show && (
        <div className="absolute z-10 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
          <div className="font-medium mb-1">{source.name}</div>
          <div className="text-gray-300">{source.description}</div>
          <div className="mt-2 flex items-center justify-between">
            <span>可信度: {(source.confidence * 100).toFixed(0)}%</span>
            <span className={`px-1.5 py-0.5 rounded ${
              source.reliability === 'high' ? 'bg-green-600' :
              source.reliability === 'medium' ? 'bg-yellow-600' : 'bg-red-600'
            }`}>
              {source.reliability === 'high' ? '高可靠' : source.reliability === 'medium' ? '中等' : '低可靠'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const DataPointCard: React.FC<{ point: DataPointValue; index: number }> = ({ point, index }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const isLowConfidence = (point.confidence || 0) < 0.7;
  const isEstimated = point.is_estimated;

  return (
    <div 
      className={`p-4 rounded-lg transition-all ${
        isEstimated ? 'bg-amber-50 border-2 border-dashed border-amber-300' :
        isLowConfidence ? 'bg-gray-50 border border-gray-200' : 
        'bg-gray-50'
      }`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-medium">
            {index + 1}
          </span>
          <div>
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              {point.title}
              {isEstimated && <span className="text-amber-500 text-sm">📈 估算</span>}
            </h4>
            <p className="text-lg font-semibold text-primary-600 mt-1">{point.value}</p>
            {point.note && <p className="text-sm text-gray-500 mt-1">{point.note}</p>}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <ConfidenceBadge confidence={point.confidence || 0.5} />
          {point.source && showTooltip && (
            <div className="absolute right-0 top-full mt-2 w-56 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-10">
              <div className="font-medium">{point.source.icon} {point.source.label}</div>
              <div className="text-gray-300 mt-1">{point.source.description}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const AnalysisBlockWithConfidence: React.FC<{ title: string; data: Record<string, AnalysisValue> }> = ({ title, data }) => {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h4 className="font-medium text-gray-700 mb-3">{title}</h4>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(data).map(([key, valueData]) => {
          const value = typeof valueData === 'object' ? valueData.value : valueData;
          const confidence = typeof valueData === 'object' ? valueData.confidence : undefined;
          const isEstimated = typeof valueData === 'object' ? valueData.is_estimated : false;
          
          return (
            <div 
              key={key} 
              className={`p-3 rounded-lg ${
                isEstimated ? 'bg-amber-50 border-2 border-dashed border-amber-300' : 'bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">{formatKey(key)}</span>
                {isEstimated && <span className="text-amber-500 text-xs">📈</span>}
              </div>
              <p className="font-medium text-gray-900 mt-1">{value}</p>
              {confidence && <ConfidenceBadge confidence={confidence} size="xs" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const DataSourceCard: React.FC<{ source: DataSourceInfo }> = ({ source }) => {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <span className="text-xl">{source.icon}</span>
        <div>
          <span className="font-medium text-gray-900">{source.name}</span>
          <p className="text-sm text-gray-500">{source.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <ConfidenceBadge confidence={source.confidence} size="xs" />
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          source.reliability === 'high' ? 'bg-green-100 text-green-700' :
          source.reliability === 'medium' ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700'
        }`}>
          {source.reliability === 'high' ? '高可靠' : source.reliability === 'medium' ? '中等' : '低可靠'}
        </span>
      </div>
    </div>
  );
};

const InvestmentAdviceSection: React.FC<{ 
  advice: Record<string, unknown>; 
  reportStyle: string;
  getStyleColor: (style: string) => string;
}> = ({ advice, reportStyle, getStyleColor }) => {
  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm text-primary-600">综合评级</span>
            <p className="text-2xl font-bold text-primary-700">
              {typeof advice.overall_rating === 'object' ? (advice.overall_rating as AnalysisValue).value : advice.overall_rating}
            </p>
          </div>
          <div className="text-right">
            <span className="text-sm text-primary-600">操作建议</span>
            <p className="text-lg font-semibold text-primary-700">
              {typeof advice.action_recommendation === 'object' ? (advice.action_recommendation as AnalysisValue).value : advice.action_recommendation}
            </p>
          </div>
        </div>
      </div>

      {advice.key_factors && Array.isArray(advice.key_factors) && advice.key_factors.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">关键因素</h4>
          <div className="flex flex-wrap gap-2">
            {advice.key_factors.map((factor, index) => (
              <span key={index} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm">
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}

      {advice.style_specific_advice && typeof advice.style_specific_advice === 'object' && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-700 mb-2">个性化建议</h4>
          <div className="flex items-center gap-3">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStyleColor(reportStyle)}`}>
              {(advice.style_specific_advice as Record<string, string>).risk_level}
            </span>
            <p className="text-gray-700">{(advice.style_specific_advice as Record<string, string>).suggestion}</p>
          </div>
        </div>
      )}
    </div>
  );
};

const formatKey = (key: string): string => {
  const keyMap: Record<string, string> = {
    supply_demand: '供需关系',
    liquidity: '流动性',
    market_sentiment: '市场情绪',
    current_level: '当前水平',
    historical_trend: '历史趋势',
    future_outlook: '未来展望',
    transportation: '交通',
    education: '教育',
    medical: '医疗',
    commercial: '商业',
  };
  return keyMap[key] || key;
};

const generatePlainText = (report: ReportContent): string => {
  const lines: string[] = [];
  const sections = report.sections || {};

  lines.push('# 房都督AI - 房产分析报告\n');

  if (sections.summary?.text) {
    lines.push('## 执行摘要\n');
    lines.push(sections.summary.text + '\n');
  }

  if (sections.key_findings?.length) {
    lines.push('## 核心发现\n');
    sections.key_findings.forEach((f, i) => {
      const finding = f as DataPointValue;
      lines.push(`${i + 1}. ${finding.title}: ${finding.value}`);
    });
    lines.push('');
  }

  if (sections.investment_advice) {
    lines.push('## 投资建议\n');
    const advice = sections.investment_advice;
    const rating = typeof advice.overall_rating === 'object' 
      ? (advice.overall_rating as AnalysisValue).value 
      : advice.overall_rating;
    const recommendation = typeof advice.action_recommendation === 'object'
      ? (advice.action_recommendation as AnalysisValue).value
      : advice.action_recommendation;
    lines.push(`综合评级: ${rating}`);
    lines.push(`操作建议: ${recommendation}`);
    lines.push('');
  }

  if (sections.risk_warning?.warnings) {
    lines.push('## 风险提示\n');
    sections.risk_warning.warnings.forEach((w: { text: string }, i: number) => {
      lines.push(`${i + 1}. ${w.text}`);
    });
  }

  return lines.join('\n');
};

export default ReportRenderer;
