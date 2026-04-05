import React, { useState, useRef } from 'react';
import {
  DocumentTextIcon,
  ChartBarIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { generateReportText } from '@/utils/pdfExport';

interface DataSource {
  name: string;
  type: string;
  description: string;
  reliability: string;
}

interface CoreFindings {
  location?: {
    city: string;
    district: string;
    community: string;
  };
  market_overview?: {
    total_properties: number;
    average_price: number;
    price_range: { min?: number; max?: number };
  };
  price_analysis?: {
    trend: string;
    year_over_year: number;
    month_over_month: number;
  };
  key_insights?: string[];
}

interface DetailedAnalysis {
  market_analysis?: {
    supply_demand: string;
    liquidity: string;
    market_sentiment: string;
  };
  price_analysis?: {
    current_level: string;
    historical_trend: string;
    future_outlook: string;
  };
  location_analysis?: {
    transportation: string;
    education: string;
    medical: string;
    commercial: string;
  };
  property_analysis?: Record<string, string>;
}

interface InvestmentAdvice {
  overall_rating: string;
  investment_horizon?: {
    short_term: string;
    medium_term: string;
    long_term: string;
  };
  action_recommendation: string;
  key_factors?: string[];
  style_specific_advice?: {
    risk_level: string;
    suggestion: string;
  };
}

interface Report {
  id: string;
  task_id: string;
  query: string;
  style: string;
  executive_summary: string;
  core_findings: CoreFindings;
  detailed_analysis: DetailedAnalysis;
  investment_advice: InvestmentAdvice;
  risk_warnings: string[];
  data_sources: DataSource[];
  confidence_score: number;
  created_at: string;
}

interface ReportViewerProps {
  report: Report;
  onCopy?: () => void;
  onExport?: () => void;
}

const ReportViewer: React.FC<ReportViewerProps> = ({ report, onCopy, onExport }) => {
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('summary');
  const reportRef = useRef<HTMLDivElement>(null);
  const exportRef = useRef<HTMLDivElement>(null);

  const handleCopy = async () => {
    const text = generateReportText(report as unknown as Record<string, unknown>);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };

  const handleExportPDF = async () => {
    if (exporting || !exportRef.current) return;
    
    setExporting(true);
    
    try {
      const element = exportRef.current;
      
      // 临时显示隐藏元素
      element.style.display = 'block';
      element.style.position = 'fixed';
      element.style.left = '-9999px';
      element.style.top = '0';
      element.style.zIndex = '-9999';
      
      // 等待渲染
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        logging: false,
        windowWidth: 800,
        windowHeight: element.scrollHeight,
      });
      
      // 恢复隐藏状态
      element.style.display = 'none';
      element.style.position = '';
      element.style.left = '';
      element.style.top = '';
      element.style.zIndex = '';
      
      const imgWidth = 210;
      const pageHeight = 297;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });
      
      const imgData = canvas.toDataURL('image/png', 1.0);
      
      let heightLeft = imgHeight;
      let position = 0;
      
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
      
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }
      
      const filename = `房产分析报告_${report.task_id?.slice(0, 8) || 'unknown'}_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.pdf`;
      pdf.save(filename);
      
      onExport?.();
    } catch (error) {
      console.error('PDF export failed:', error);
      alert('PDF导出失败，请稍后重试');
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
      case 'conservative': return 'text-blue-600 bg-blue-50';
      case 'aggressive': return 'text-orange-600 bg-orange-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  const getReliabilityColor = (reliability: string): string => {
    switch (reliability) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'low': return 'text-red-600 bg-red-100';
      default: return 'text-yellow-600 bg-yellow-100';
    }
  };

  const sections = [
    { id: 'summary', label: '执行摘要', icon: DocumentTextIcon },
    { id: 'findings', label: '核心发现', icon: ChartBarIcon },
    { id: 'analysis', label: '详细分析', icon: InformationCircleIcon },
    { id: 'advice', label: '投资建议', icon: LightBulbIcon },
    { id: 'risks', label: '风险提示', icon: ExclamationTriangleIcon },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">房产分析报告</h2>
              <p className="text-gray-500 mt-1">{report.query}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStyleColor(report.style)}`}>
                {getStyleLabel(report.style)}
              </span>
              <div className="text-right">
                <div className="text-sm text-gray-500">置信度</div>
                <div className="text-lg font-bold text-primary-600">
                  {(report.confidence_score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-2 mt-4">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              {copied ? (
                <>
                  <CheckIcon className="w-4 h-4 text-green-500" />
                  已复制
                </>
              ) : (
                <>
                  <ClipboardDocumentIcon className="w-4 h-4" />
                  复制报告
                </>
              )}
            </button>
            <button
              onClick={handleExportPDF}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {exporting ? (
                <>
                  <ArrowDownTrayIcon className="w-4 h-4 animate-bounce" />
                  导出中...
                </>
              ) : (
                <>
                  <ArrowDownTrayIcon className="w-4 h-4" />
                  导出PDF
                </>
              )}
            </button>
          </div>
        </div>

        {/* Section Navigation */}
        <div className="border-b border-gray-100">
          <nav className="flex overflow-x-auto">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeSection === section.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Report Content - Exportable Area */}
      <div 
        ref={reportRef}
        id="report-content"
        className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"
      >
        {/* Executive Summary */}
        {activeSection === 'summary' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">执行摘要</h3>
            <p className="text-gray-700 leading-relaxed text-lg">
              {report.executive_summary}
            </p>
          </div>
        )}

        {/* Core Findings */}
        {activeSection === 'findings' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">核心发现</h3>
            
            {/* Location */}
            {report.core_findings?.location && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">位置信息</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">城市</span>
                    <p className="font-medium text-gray-900">{report.core_findings.location.city || '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">区域</span>
                    <p className="font-medium text-gray-900">{report.core_findings.location.district || '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">小区</span>
                    <p className="font-medium text-gray-900">{report.core_findings.location.community || '-'}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Market Overview */}
            {report.core_findings?.market_overview && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">市场概况</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">在售房源</span>
                    <p className="font-medium text-gray-900">{report.core_findings.market_overview.total_properties || 0} 套</p>
                  </div>
                  <div>
                    <span className="text-gray-500">均价</span>
                    <p className="font-medium text-gray-900">
                      {report.core_findings.market_overview.average_price?.toLocaleString() || '-'} 元/㎡
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">价格区间</span>
                    <p className="font-medium text-gray-900">
                      {report.core_findings.market_overview.price_range?.min?.toLocaleString() || '-'} - 
                      {report.core_findings.market_overview.price_range?.max?.toLocaleString() || '-'} 万
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Price Analysis */}
            {report.core_findings?.price_analysis && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">价格分析</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">趋势</span>
                    <p className="font-medium text-gray-900">{report.core_findings.price_analysis.trend}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">同比变化</span>
                    <p className={`font-medium ${report.core_findings.price_analysis.year_over_year >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {report.core_findings.price_analysis.year_over_year >= 0 ? '+' : ''}
                      {report.core_findings.price_analysis.year_over_year}%
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">环比变化</span>
                    <p className={`font-medium ${report.core_findings.price_analysis.month_over_month >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {report.core_findings.price_analysis.month_over_month >= 0 ? '+' : ''}
                      {report.core_findings.price_analysis.month_over_month}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Key Insights */}
            {report.core_findings?.key_insights && report.core_findings.key_insights.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-700 mb-2">关键洞察</h4>
                <ul className="space-y-2">
                  {report.core_findings.key_insights.map((insight, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                        {index + 1}
                      </span>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Detailed Analysis */}
        {activeSection === 'analysis' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">详细分析</h3>
            
            {/* Market Analysis */}
            {report.detailed_analysis?.market_analysis && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">市场分析</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">供需关系</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.market_analysis.supply_demand}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">流动性</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.market_analysis.liquidity}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">市场情绪</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.market_analysis.market_sentiment}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Location Analysis */}
            {report.detailed_analysis?.location_analysis && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">配套分析</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">交通</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.location_analysis.transportation}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">教育</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.location_analysis.education}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">医疗</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.location_analysis.medical}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">商业</span>
                    <p className="font-medium text-gray-900">{report.detailed_analysis.location_analysis.commercial}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Property Analysis */}
            {report.detailed_analysis?.property_analysis && Object.keys(report.detailed_analysis.property_analysis).length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">房产属性</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  {Object.entries(report.detailed_analysis.property_analysis).map(([key, value]) => (
                    <div key={key}>
                      <span className="text-gray-500">{key}</span>
                      <p className="font-medium text-gray-900">{value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Investment Advice */}
        {activeSection === 'advice' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">投资建议</h3>
            
            {/* Overall Rating */}
            <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm text-primary-600">综合评级</span>
                  <p className="text-2xl font-bold text-primary-700">{report.investment_advice.overall_rating}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm text-primary-600">操作建议</span>
                  <p className="text-lg font-semibold text-primary-700">{report.investment_advice.action_recommendation}</p>
                </div>
              </div>
            </div>

            {/* Investment Horizon */}
            {report.investment_advice?.investment_horizon && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">投资周期建议</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg">
                    <span className="text-xs text-gray-500">短期 (1年内)</span>
                    <p className="font-medium text-gray-900 mt-1">{report.investment_advice.investment_horizon.short_term}</p>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <span className="text-xs text-gray-500">中期 (1-3年)</span>
                    <p className="font-medium text-gray-900 mt-1">{report.investment_advice.investment_horizon.medium_term}</p>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <span className="text-xs text-gray-500">长期 (3年以上)</span>
                    <p className="font-medium text-gray-900 mt-1">{report.investment_advice.investment_horizon.long_term}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Style Specific Advice */}
            {report.investment_advice?.style_specific_advice && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">风格化建议</h4>
                <div className="flex items-center gap-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStyleColor(report.style)}`}>
                    {report.investment_advice.style_specific_advice.risk_level}
                  </span>
                  <p className="text-gray-700">{report.investment_advice.style_specific_advice.suggestion}</p>
                </div>
              </div>
            )}

            {/* Key Factors */}
            {report.investment_advice?.key_factors && report.investment_advice.key_factors.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-700 mb-2">关键因素</h4>
                <div className="flex flex-wrap gap-2">
                  {report.investment_advice.key_factors.map((factor, index) => (
                    <span key={index} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm">
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Risk Warnings */}
        {activeSection === 'risks' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">风险提示</h3>
            
            <div className="space-y-3">
              {report.risk_warnings.map((warning, index) => (
                <div key={index} className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <p className="text-yellow-800 text-sm">{warning}</p>
                </div>
              ))}
            </div>

            {/* Data Sources */}
            <div className="mt-8">
              <h4 className="font-medium text-gray-700 mb-3">数据来源</h4>
              <div className="space-y-2">
                {report.data_sources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="font-medium text-gray-900">{source.name}</span>
                      <p className="text-sm text-gray-500">{source.description}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getReliabilityColor(source.reliability)}`}>
                      {source.type === 'real' ? '真实数据' : '模拟数据'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-gray-100 text-sm text-gray-500">
          报告生成时间: {new Date(report.created_at).toLocaleString('zh-CN')}
        </div>
      </div>

      {/* Hidden Full Report for PDF Export */}
      <div 
        ref={exportRef}
        style={{ 
          display: 'none',
          width: '800px',
          backgroundColor: 'white',
          padding: '24px'
        }}
      >
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', textAlign: 'center', marginBottom: '20px' }}>
          房都督AI - 房产分析报告
        </h1>
        
        <div style={{ marginBottom: '10px' }}>
          <strong>查询:</strong> {report.query}
        </div>
        <div style={{ marginBottom: '10px' }}>
          <strong>分析风格:</strong> {getStyleLabel(report.style)} | <strong>置信度:</strong> {((report.confidence_score || 0) * 100).toFixed(0)}%
        </div>

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>执行摘要</h2>
        <p style={{ lineHeight: '1.6', marginBottom: '20px' }}>{report.executive_summary}</p>

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>核心发现</h2>
        
        {report.core_findings?.location && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>位置信息</h3>
            <p>城市: {report.core_findings.location.city || '-'} | 区域: {report.core_findings.location.district || '-'} | 小区: {report.core_findings.location.community || '-'}</p>
          </div>
        )}

        {report.core_findings?.market_overview && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>市场概况</h3>
            <p>在售房源: {report.core_findings.market_overview.total_properties || 0} 套</p>
            <p>均价: {report.core_findings.market_overview.average_price?.toLocaleString() || '-'} 元/㎡</p>
            <p>价格区间: {report.core_findings.market_overview.price_range?.min?.toLocaleString() || '-'} - {report.core_findings.market_overview.price_range?.max?.toLocaleString() || '-'} 元/㎡</p>
          </div>
        )}

        {report.core_findings?.price_analysis && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>价格分析</h3>
            <p>趋势: {report.core_findings.price_analysis.trend_direction || '稳定'}</p>
            <p>同比变化: {report.core_findings.price_analysis.year_over_year || 0}%</p>
            <p>环比变化: {report.core_findings.price_analysis.month_over_month || 0}%</p>
          </div>
        )}

        {report.core_findings?.key_insights && report.core_findings.key_insights.length > 0 && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>关键洞察</h3>
            <ul style={{ paddingLeft: '20px' }}>
              {report.core_findings.key_insights.map((insight, index) => (
                <li key={index}>{index + 1}. {insight}</li>
              ))}
            </ul>
          </div>
        )}

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>详细分析</h2>
        
        {report.detailed_analysis?.market_analysis && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>市场分析</h3>
            <p>供需关系: {report.detailed_analysis.market_analysis.supply_demand}</p>
            <p>流动性: {report.detailed_analysis.market_analysis.liquidity}</p>
            <p>市场情绪: {report.detailed_analysis.market_analysis.market_sentiment}</p>
          </div>
        )}

        {report.detailed_analysis?.location_analysis && (
          <div style={{ marginBottom: '15px' }}>
            <h3 style={{ fontWeight: 'bold', marginBottom: '5px' }}>配套分析</h3>
            <p>交通: {report.detailed_analysis.location_analysis.transportation}</p>
            <p>教育: {report.detailed_analysis.location_analysis.education}</p>
            <p>医疗: {report.detailed_analysis.location_analysis.medical}</p>
            <p>商业: {report.detailed_analysis.location_analysis.commercial}</p>
          </div>
        )}

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>投资建议</h2>
        
        {report.investment_advice && (
          <div style={{ marginBottom: '15px' }}>
            <p><strong>综合评级:</strong> {report.investment_advice.overall_rating}</p>
            <p><strong>行动建议:</strong> {report.investment_advice.action_recommendation}</p>
            
            {report.investment_advice.key_factors && (
              <div style={{ marginTop: '10px' }}>
                <strong>关键因素:</strong>
                <ul style={{ paddingLeft: '20px' }}>
                  {report.investment_advice.key_factors.map((factor, index) => (
                    <li key={index}>• {factor}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.investment_advice.investment_horizon && (
              <div style={{ marginTop: '10px' }}>
                <strong>投资周期建议:</strong>
                <p>短期: {report.investment_advice.investment_horizon.short_term}</p>
                <p>中期: {report.investment_advice.investment_horizon.medium_term}</p>
                <p>长期: {report.investment_advice.investment_horizon.long_term}</p>
              </div>
            )}
          </div>
        )}

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>风险提示</h2>
        
        {report.risk_warnings && report.risk_warnings.length > 0 && (
          <ul style={{ paddingLeft: '20px', marginBottom: '20px' }}>
            {report.risk_warnings.map((warning, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>⚠️ {warning}</li>
            ))}
          </ul>
        )}

        <hr style={{ margin: '20px 0' }} />

        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>数据来源</h2>
        
        {report.data_sources && report.data_sources.length > 0 && (
          <ul style={{ paddingLeft: '20px' }}>
            {report.data_sources.map((source, index) => (
              <li key={index}>
                📋 {source.name}: {source.description} (可靠性: {source.reliability === 'high' ? '高' : source.reliability === 'medium' ? '中' : '低'})
              </li>
            ))}
          </ul>
        )}

        <hr style={{ margin: '20px 0' }} />
        
        <p style={{ textAlign: 'center', color: '#666', fontSize: '12px' }}>
          报告生成时间: {new Date(report.created_at).toLocaleString('zh-CN')}
        </p>
        <p style={{ textAlign: 'center', color: '#999', fontSize: '10px' }}>
          本报告由房都督AI生成，仅供参考，不构成投资建议
        </p>
      </div>
    </div>
  );
};

export default ReportViewer;
export type { Report, ReportViewerProps };
