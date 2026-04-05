import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import {
  ArrowLeftIcon,
  ArrowDownTrayIcon,
  ShareIcon,
  ChatBubbleLeftRightIcon,
  BookmarkIcon,
  PencilIcon,
  PrinterIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import AnalysisReport from '../ui/AnalysisReport';

interface ReferenceCase {
  id: string;
  title: string;
  similarity: number;
  summary: string;
}

interface ReasoningStep {
  step: string;
  content: string;
  timestamp: string;
}

interface ReportDetailData {
  id: string;
  title: string;
  summary: string;
  keyMetrics: {
    label: string;
    value: string | number;
    unit?: string;
    description?: string;
  }[];
  charts: {
    type: 'line' | 'bar' | 'radar';
    title: string;
    data: Record<string, unknown>[];
    dataKeys?: string[];
    xKey?: string;
  }[];
  reasoningChain: ReasoningStep[];
  recommendations: string[];
  actionSteps: {
    step: number;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }[];
  referenceCases: ReferenceCase[];
  fullReport: string;
  findings: string[];
  integralCost: number;
  stepsCount: number;
  createdAt: string;
  query: string;
}

const ReportDetailPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<ReportDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [showComments, setShowComments] = useState(false);
  const [annotations, setAnnotations] = useState<{ id: string; text: string; position: number }[]>([]);

  useEffect(() => {
    const fetchReport = async () => {
      if (!reportId) return;

      try {
        setIsLoading(true);
        const response = await fetch(`/api/reports/${reportId}`);
        if (!response.ok) throw new Error('报告不存在');
        const data = await response.json();
        setReport(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载报告失败');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [reportId]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  const handleExport = (format: 'pdf' | 'markdown' | 'html') => {
    console.log(`导出报告为 ${format} 格式`);
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('链接已复制到剪贴板');
  };

  const handleConsultAgain = () => {
    navigate('/consult', { state: { context: report?.query } });
  };

  const handlePrint = () => {
    window.print();
  };

  const renderChart = (chart: ReportDetailData['charts'][0]) => {
    switch (chart.type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} />
              <Legend />
              {chart.dataKeys?.map((key, i) => (
                <Line key={key} type="monotone" dataKey={key} stroke={['#3B82F6', '#10B981', '#F59E0B'][i % 3]} strokeWidth={2} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} />
              <Legend />
              {chart.dataKeys?.map((key, i) => (
                <Bar key={key} dataKey={key} fill={['#3B82F6', '#10B981', '#F59E0B'][i % 3]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      case 'radar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={chart.data}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" />
              <PolarRadiusAxis stroke="#9CA3AF" />
              {chart.dataKeys?.map((key, i) => (
                <Radar key={key} name={key} dataKey={key} stroke={['#3B82F6', '#10B981', '#F59E0B'][i % 3]} fill={['#3B82F6', '#10B981', '#F59E0B'][i % 3]} fillOpacity={0.3} />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <ExclamationCircleIcon className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {error || '报告不存在'}
        </h2>
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >
          返回仪表盘
        </button>
      </div>
    );
  }

  const sections = [
    { id: 'overview', title: '概览', icon: '📊' },
    { id: 'metrics', title: '关键指标', icon: '📈' },
    { id: 'charts', title: '数据图表', icon: '📉' },
    { id: 'reasoning', title: '分析过程', icon: '🧠' },
    { id: 'recommendations', title: '建议与行动', icon: '💡' },
    { id: 'cases', title: '参考案例', icon: '📚' },
    { id: 'full', title: '完整报告', icon: '📄' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 print:bg-white">
      <div className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 print:hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ArrowLeftIcon className="w-5 h-5 text-gray-500" />
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate max-w-md">
                  {report.title}
                </h1>
                <p className="text-xs text-gray-500">
                  生成于 {new Date(report.createdAt).toLocaleString('zh-CN')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleConsultAgain}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-500 text-white text-sm rounded-lg hover:bg-primary-600"
              >
                <ChatBubbleLeftRightIcon className="w-4 h-4" />
                再次咨询
              </motion.button>

              <div className="relative">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleExport('pdf')}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                  导出
                </motion.button>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleShare}
                className="p-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <ShareIcon className="w-4 h-4" />
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePrint}
                className="p-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <PrinterIcon className="w-4 h-4" />
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          <div className="hidden lg:block w-48 flex-shrink-0 print:hidden">
            <div className="sticky top-24">
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => {
                      setActiveSection(section.id);
                      document.getElementById(section.id)?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                      activeSection === section.id
                        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    <span>{section.icon}</span>
                    {section.title}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          <div className="flex-1 space-y-8">
            <section id="overview" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  📊 分析概览
                </h2>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                  {report.summary}
                </p>

                <div className="mt-6 flex gap-6 text-sm text-gray-500">
                  <div>
                    消耗积分: <span className="font-medium text-primary-600">{report.integralCost}</span>
                  </div>
                  <div>
                    执行步骤: <span className="font-medium text-primary-600">{report.stepsCount}</span>
                  </div>
                </div>
              </div>
            </section>

            <section id="metrics" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  📈 关键指标
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {report.keyMetrics.map((metric, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 rounded-xl"
                    >
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                        {metric.label}
                      </div>
                      <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                        {metric.value}
                        {metric.unit && <span className="text-sm font-normal text-gray-500 ml-1">{metric.unit}</span>}
                      </div>
                      {metric.description && (
                        <div className="text-xs text-gray-400 mt-1">{metric.description}</div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            </section>

            <section id="charts" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  📉 数据图表
                </h2>
                <div className="space-y-6">
                  {report.charts.map((chart, index) => (
                    <div key={index} className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                        {chart.title}
                      </h3>
                      {renderChart(chart)}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section id="reasoning" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  🧠 分析过程
                </h2>
                <div className="space-y-4">
                  {report.reasoningChain.map((step, index) => (
                    <div key={index} className="relative pl-6">
                      <div className="absolute left-0 top-2 w-4 h-4 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-primary-500" />
                      </div>
                      {index < report.reasoningChain.length - 1 && (
                        <div className="absolute left-[7px] top-6 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
                      )}
                      <div className="pb-4">
                        <div className="text-xs text-gray-500 mb-1">
                          {new Date(step.timestamp).toLocaleTimeString('zh-CN')}
                        </div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                          {step.step}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-300">
                          {step.content}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section id="recommendations" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  💡 建议与行动步骤
                </h2>

                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                    核心建议
                  </h3>
                  <ul className="space-y-2">
                    {report.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                          {index + 1}
                        </span>
                        <span className="text-gray-700 dark:text-gray-300">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                    行动步骤
                  </h3>
                  <div className="space-y-3">
                    {report.actionSteps.map((action) => (
                      <div
                        key={action.step}
                        className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                      >
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                            action.priority === 'high'
                              ? 'bg-red-100 text-red-600'
                              : action.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-600'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {action.step}
                        </span>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {action.title}
                          </div>
                          <div className="text-sm text-gray-500">{action.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            <section id="cases" className="scroll-mt-24">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  📚 参考案例
                </h2>
                <div className="grid gap-4">
                  {report.referenceCases.map((caseItem) => (
                    <motion.div
                      key={caseItem.id}
                      whileHover={{ scale: 1.01 }}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 cursor-pointer hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {caseItem.title}
                        </h4>
                        <span className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full">
                          相似度 {Math.round(caseItem.similarity * 100)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-2">{caseItem.summary}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </section>

            <section id="full" className="scroll-mt-24">
              <AnalysisReport
                reportData={{
                  summary: report.summary,
                  findings: report.findings,
                  recommendations: report.recommendations,
                  report: report.fullReport,
                  integral_cost: report.integralCost,
                  steps_count: report.stepsCount,
                }}
                taskId={reportId}
              />
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportDetailPage;
