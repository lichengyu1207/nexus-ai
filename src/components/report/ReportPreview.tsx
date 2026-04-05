import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentTextIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  ShareIcon,
  XMarkIcon,
  ArrowsPointingOutIcon,
  ChevronRightIcon,
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

interface KeyMetric {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  color?: string;
}

interface ChartData {
  type: 'line' | 'bar' | 'radar';
  title: string;
  data: Record<string, unknown>[];
  dataKeys?: string[];
  xKey?: string;
}

interface ReportPreviewData {
  reportId: string;
  title: string;
  summary: string;
  keyMetrics: KeyMetric[];
  charts?: ChartData[];
  generatedAt: string;
}

interface ReportPreviewProps {
  report: ReportPreviewData;
  onViewFullReport?: (reportId: string) => void;
  onDownload?: (reportId: string, format: 'pdf' | 'html') => void;
  onShare?: (reportId: string) => void;
  onClose?: () => void;
  embedded?: boolean;
}

const trendColors = {
  up: 'text-green-500',
  down: 'text-red-500',
  stable: 'text-gray-500',
};

const trendIcons = {
  up: '↑',
  down: '↓',
  stable: '→',
};

const ReportPreview: React.FC<ReportPreviewProps> = ({
  report,
  onViewFullReport,
  onDownload,
  onShare,
  onClose,
  embedded = false,
}) => {
  const [selectedChart, setSelectedChart] = useState(0);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const renderChart = (chart: ChartData) => {
    const commonProps = {
      data: chart.data,
    };

    switch (chart.type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#F9FAFB' }}
              />
              <Legend />
              {chart.dataKeys?.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][index % 4]}
                  strokeWidth={2}
                  dot={{ fill: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][index % 4] }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#F9FAFB' }}
              />
              <Legend />
              {chart.dataKeys?.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][index % 4]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'radar':
        return (
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart {...commonProps}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey={chart.xKey || 'name'} stroke="#9CA3AF" fontSize={12} />
              <PolarRadiusAxis stroke="#9CA3AF" fontSize={10} />
              {chart.dataKeys?.map((key, index) => (
                <Radar
                  key={key}
                  name={key}
                  dataKey={key}
                  stroke={['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][index % 4]}
                  fill={['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][index % 4]}
                  fillOpacity={0.3}
                />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  const content = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 ${
        embedded ? '' : 'max-w-2xl w-full'
      }`}
    >
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <DocumentTextIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{report.title}</h3>
              <p className="text-sm text-white/70">
                生成于 {new Date(report.generatedAt).toLocaleString('zh-CN')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!embedded && (
              <>
                <div className="relative">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                    className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors"
                  >
                    <ArrowDownTrayIcon className="w-5 h-5" />
                  </motion.button>

                  <AnimatePresence>
                    {showDownloadMenu && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-10"
                      >
                        <button
                          onClick={() => {
                            onDownload?.(report.reportId, 'pdf');
                            setShowDownloadMenu(false);
                          }}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          📄 PDF 格式
                        </button>
                        <button
                          onClick={() => {
                            onDownload?.(report.reportId, 'html');
                            setShowDownloadMenu(false);
                          }}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          🌐 HTML 格式
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onShare?.(report.reportId)}
                  className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors"
                >
                  <ShareIcon className="w-5 h-5" />
                </motion.button>

                {onClose && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={onClose}
                    className="p-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </motion.button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        <div>
          <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            分析摘要
          </h4>
          <p className="text-gray-700 dark:text-gray-300">{report.summary}</p>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            关键指标
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {report.keyMetrics.map((metric, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="p-3 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-700"
              >
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {metric.label}
                </div>
                <div className="flex items-baseline gap-1">
                  <span
                    className="text-xl font-bold"
                    style={{ color: metric.color || '#3B82F6' }}
                  >
                    {metric.value}
                  </span>
                  {metric.unit && (
                    <span className="text-sm text-gray-500">{metric.unit}</span>
                  )}
                  {metric.trend && (
                    <span className={`text-sm ${trendColors[metric.trend]}`}>
                      {trendIcons[metric.trend]}
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {report.charts && report.charts.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                数据图表
              </h4>
              {report.charts.length > 1 && (
                <div className="flex gap-1">
                  {report.charts.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedChart(index)}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        selectedChart === index
                          ? 'bg-primary-500'
                          : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                {report.charts[selectedChart].title}
              </h5>
              {renderChart(report.charts[selectedChart])}
            </div>
          </div>
        )}

        {!embedded && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onViewFullReport?.(report.reportId)}
            className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow"
          >
            <ArrowsPointingOutIcon className="w-5 h-5" />
            查看完整报告
            <ChevronRightIcon className="w-4 h-4" />
          </motion.button>
        )}
      </div>
    </motion.div>
  );

  if (embedded) {
    return content;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center justify-center p-4"
    >
      {content}
    </motion.div>
  );
};

export default ReportPreview;
