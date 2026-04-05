import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface CompareTask {
  taskId: string;
  name: string;
  status: 'completed' | 'failed';
  metrics: {
    price?: number;
    riskScore?: number;
    valueScore?: number;
    locationScore?: number;
    potentialScore?: number;
    liquidityScore?: number;
  };
  keyFindings: string[];
  recommendations: string[];
  createdAt: string;
}

interface TaskCompareViewProps {
  tasks: CompareTask[];
  onClose: () => void;
  onExportPdf?: () => void;
}

const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

const TaskCompareView: React.FC<TaskCompareViewProps> = ({
  tasks,
  onClose,
  onExportPdf,
}) => {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    'price',
    'riskScore',
    'valueScore',
    'locationScore',
    'potentialScore',
    'liquidityScore',
  ]);
  const [highlightDifferences, setHighlightDifferences] = useState(true);

  const metricLabels: Record<string, string> = {
    price: '估价',
    riskScore: '风险评分',
    valueScore: '性价比',
    locationScore: '地段评分',
    potentialScore: '增值潜力',
    liquidityScore: '流动性',
  };

  const radarData = useMemo(() => {
    return selectedMetrics.map((metric) => {
      const dataPoint: Record<string, string | number> = {
        metric: metricLabels[metric] || metric,
      };
      tasks.forEach((task, index) => {
        const value = task.metrics[metric as keyof typeof task.metrics];
        dataPoint[`task${index}`] = value !== undefined ? value : 0;
      });
      return dataPoint;
    });
  }, [tasks, selectedMetrics]);

  const comparisonTable = useMemo(() => {
    const allMetrics = [
      { key: 'price', label: '估价', unit: '万', format: (v: number) => v.toFixed(2) },
      { key: 'riskScore', label: '风险评分', unit: '分', format: (v: number) => v.toFixed(1) },
      { key: 'valueScore', label: '性价比', unit: '分', format: (v: number) => v.toFixed(1) },
      { key: 'locationScore', label: '地段评分', unit: '分', format: (v: number) => v.toFixed(1) },
      { key: 'potentialScore', label: '增值潜力', unit: '分', format: (v: number) => v.toFixed(1) },
      { key: 'liquidityScore', label: '流动性', unit: '分', format: (v: number) => v.toFixed(1) },
    ];

    return allMetrics.map((metric) => {
      const values = tasks.map((t) => t.metrics[metric.key as keyof typeof t.metrics] as number);
      const max = Math.max(...values.filter((v) => v !== undefined));
      const min = Math.min(...values.filter((v) => v !== undefined));
      const diff = max - min;
      const diffPercent = min > 0 ? ((diff / min) * 100).toFixed(1) : '0';

      return {
        ...metric,
        values,
        max,
        min,
        diffPercent,
        hasSignificantDiff: diffPercent !== '0' && parseFloat(diffPercent) > 10,
      };
    });
  }, [tasks]);

  const getDifferenceStyle = (value: number, max: number, min: number, hasSignificantDiff: boolean) => {
    if (!highlightDifferences || !hasSignificantDiff) return '';
    if (value === max) return 'text-green-600 dark:text-green-400 font-semibold';
    if (value === min) return 'text-red-600 dark:text-red-400';
    return '';
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 overflow-auto"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="min-h-screen p-4 md:p-8"
      >
        <div className="max-w-6xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-2xl overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">任务对比分析</h2>
                <p className="text-white/70 mt-1">
                  对比 {tasks.length} 个任务的分析结果
                </p>
              </div>
              <div className="flex items-center gap-2">
                {onExportPdf && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={onExportPdf}
                    className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                  >
                    <ArrowDownTrayIcon className="w-5 h-5" />
                    导出PDF
                  </motion.button>
                )}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onClose}
                  className="p-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </motion.button>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-8">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <ChartBarIcon className="w-5 h-5 text-primary-500" />
                指标对比雷达图
              </h3>
              <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={highlightDifferences}
                  onChange={(e) => setHighlightDifferences(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                高亮差异
              </label>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#374151" />
                  <PolarAngleAxis dataKey="metric" stroke="#9CA3AF" fontSize={12} />
                  <PolarRadiusAxis stroke="#9CA3AF" fontSize={10} />
                  {tasks.map((_, index) => (
                    <Radar
                      key={index}
                      name={tasks[index].name}
                      dataKey={`task${index}`}
                      stroke={colors[index % colors.length]}
                      fill={colors[index % colors.length]}
                      fillOpacity={0.2}
                    />
                  ))}
                  <Legend />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: 'none',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#F9FAFB' }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                详细指标对比
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                        指标
                      </th>
                      {tasks.map((task) => (
                        <th
                          key={task.taskId}
                          className="text-center py-3 px-4 text-sm font-medium text-gray-900 dark:text-white"
                        >
                          {task.name}
                        </th>
                      ))}
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                        差异
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonTable.map((row) => (
                      <tr
                        key={row.key}
                        className={`border-b border-gray-100 dark:border-gray-800 ${
                          highlightDifferences && row.hasSignificantDiff
                            ? 'bg-yellow-50 dark:bg-yellow-900/10'
                            : ''
                        }`}
                      >
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">
                          {row.label}
                        </td>
                        {row.values.map((value, index) => (
                          <td
                            key={index}
                            className={`text-center py-3 px-4 text-sm ${getDifferenceStyle(
                              value,
                              row.max,
                              row.min,
                              row.hasSignificantDiff
                            )}`}
                          >
                            {value !== undefined ? (
                              <>
                                {row.format(value)}
                                <span className="text-xs text-gray-400 ml-1">{row.unit}</span>
                              </>
                            ) : (
                              '-'
                            )}
                            {highlightDifferences && value === row.max && row.hasSignificantDiff && (
                              <CheckCircleIcon className="inline w-4 h-4 text-green-500 ml-1" />
                            )}
                          </td>
                        ))}
                        <td className="text-center py-3 px-4">
                          {row.hasSignificantDiff ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs rounded-full">
                              <ExclamationTriangleIcon className="w-3 h-3" />
                              {row.diffPercent}%
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                关键发现对比
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tasks.map((task, taskIndex) => (
                  <div
                    key={task.taskId}
                    className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border-l-4"
                    style={{ borderColor: colors[taskIndex % colors.length] }}
                  >
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                      {task.name}
                    </h4>
                    <ul className="space-y-2">
                      {task.keyFindings.slice(0, 3).map((finding, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <span className="w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                            {index + 1}
                          </span>
                          {finding}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                建议对比
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tasks.map((task, taskIndex) => (
                  <div
                    key={task.taskId}
                    className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: colors[taskIndex % colors.length] }}
                      />
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {task.name}
                      </h4>
                    </div>
                    <ul className="space-y-2">
                      {task.recommendations.slice(0, 3).map((rec, index) => (
                        <li key={index} className="text-sm text-gray-600 dark:text-gray-300 pl-2 border-l-2 border-gray-200 dark:border-gray-700">
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TaskCompareView;
