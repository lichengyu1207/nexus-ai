import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentTextIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowsRightLeftIcon,
} from '@heroicons/react/24/outline';
import BarChart from '@/components/charts/BarChart';
import RadarChart from '@/components/charts/RadarChart';

type ViewMode = 'summary' | 'comparison' | 'detail';
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

interface SubTask {
  id: string;
  type: string;
  typeLabel: string;
  status: TaskStatus;
  params: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  duration?: number;
  createdAt: string;
  completedAt?: string;
}

interface BatchResultViewProps {
  parentTaskId: string;
  tasks: SubTask[];
  onTaskClick?: (taskId: string) => void;
  onExport?: (format: 'pdf' | 'excel') => void;
  onRetry?: (taskId: string) => void;
}

const TASK_TYPE_LABELS: Record<string, string> = {
  property_analysis: '房产分析',
  policy_query: '政策查询',
  mingpan: '命理咨询',
  emotion: '情感陪伴',
  report_generation: '报告生成',
};

const STATUS_CONFIG: Record<TaskStatus, { label: string; icon: typeof CheckCircleIcon; color: string }> = {
  pending: { label: '等待中', icon: ClockIcon, color: 'text-gray-400' },
  running: { label: '执行中', icon: ArrowPathIcon, color: 'text-blue-500' },
  completed: { label: '已完成', icon: CheckCircleIcon, color: 'text-green-500' },
  failed: { label: '失败', icon: XCircleIcon, color: 'text-red-500' },
};

const BatchResultView: React.FC<BatchResultViewProps> = ({
  parentTaskId,
  tasks,
  onTaskClick,
  onExport,
  onRetry,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('summary');
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());

  const stats = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const totalDuration = tasks.reduce((sum, t) => sum + (t.duration || 0), 0);
    
    return { total, completed, failed, running, pending, totalDuration };
  }, [tasks]);

  const comparisonData = useMemo(() => {
    const propertyTasks = tasks.filter(t => t.type === 'property_analysis' && t.status === 'completed');
    
    if (propertyTasks.length < 2) return null;

    return propertyTasks.map(task => ({
      name: (task.params.city as string) || (task.params.district as string) || '未知区域',
      avgPrice: (task.result?.avgPrice as number) || 0,
      priceChange: (task.result?.priceChange as number) || 0,
      volume: (task.result?.volume as number) || 0,
      liquidity: (task.result?.liquidity as number) || 0,
    }));
  }, [tasks]);

  const radarData = useMemo(() => {
    if (!comparisonData || comparisonData.length === 0) return [];
    
    const metrics = ['avgPrice', 'priceChange', 'volume', 'liquidity'];
    return metrics.map(metric => {
      const max = Math.max(...comparisonData.map(d => d[metric as keyof typeof comparisonData[0]] as number));
      const row: Record<string, string | number> = { metric: metric === 'avgPrice' ? '均价' : metric === 'priceChange' ? '涨幅' : metric === 'volume' ? '成交量' : '流动性' };
      comparisonData.forEach(d => {
        const value = d[metric as keyof typeof comparisonData[0]] as number;
        row[d.name] = max > 0 ? Math.round((value / max) * 100) : 0;
      });
      return row;
    });
  }, [comparisonData]);

  const toggleExpand = (taskId: string) => {
    setExpandedTasks(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const toggleSelect = (taskId: string) => {
    setSelectedTasks(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const handleExport = (format: 'pdf' | 'excel') => {
    onExport?.(format);
  };

  const renderSummaryView = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">总任务数</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.completed}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">已完成</div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.failed}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">失败</div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.running}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">执行中</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
          <div className="text-2xl font-bold text-gray-600 dark:text-gray-300">{Math.round(stats.totalDuration / 1000)}s</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">总耗时</div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white">任务列表</h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {tasks.map(task => {
            const statusConfig = STATUS_CONFIG[task.status];
            const StatusIcon = statusConfig.icon;
            const isExpanded = expandedTasks.has(task.id);

            return (
              <motion.div
                key={task.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
              >
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer"
                  onClick={() => toggleExpand(task.id)}
                >
                  <div className="flex items-center gap-3">
                    <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {TASK_TYPE_LABELS[task.type] || task.type}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {task.params.city && `${task.params.city}`}
                        {task.params.district && ` · ${task.params.district}`}
                        {task.duration && ` · ${Math.round(task.duration / 1000)}s`}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.status === 'failed' && onRetry && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRetry(task.id);
                        }}
                        className="text-sm text-blue-500 hover:text-blue-600"
                      >
                        重试
                      </button>
                    )}
                    {task.status === 'completed' && onTaskClick && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onTaskClick(task.id);
                        }}
                        className="text-sm text-blue-500 hover:text-blue-600 flex items-center gap-1"
                      >
                        <EyeIcon className="w-4 h-4" />
                        查看
                      </button>
                    )}
                    {isExpanded ? (
                      <ChevronUpIcon className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-3 pl-12">
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">参数</div>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {Object.entries(task.params).map(([key, value]) => (
                              <div key={key} className="flex gap-2">
                                <span className="text-gray-500 dark:text-gray-400">{key}:</span>
                                <span className="text-gray-900 dark:text-white">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                          {task.error && (
                            <div className="mt-3 text-sm text-red-500">
                              <span className="font-medium">错误: </span>
                              {task.error}
                            </div>
                          )}
                          {task.result && (
                            <div className="mt-3">
                              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">结果摘要</div>
                              <pre className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 p-2 rounded overflow-auto max-h-40">
                                {JSON.stringify(task.result, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderComparisonView = () => {
    if (!comparisonData || comparisonData.length < 2) {
      return (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ArrowsRightLeftIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>需要至少2个已完成的房产分析任务才能进行对比</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">价格对比</h3>
          <BarChart
            data={comparisonData}
            xKey="name"
            series={[
              { dataKey: 'avgPrice', name: '均价(元/㎡)', color: '#3B82F6' },
            ]}
            height={250}
          />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">综合指标雷达图</h3>
          <RadarChart
            data={radarData}
            angleKey="metric"
            series={comparisonData.map((d, i) => ({
              dataKey: d.name,
              name: d.name,
              color: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][i % 4],
            }))}
            height={300}
          />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-medium text-gray-900 dark:text-white">详细对比表</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">区域</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">均价(元/㎡)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">涨幅(%)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">成交量</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">流动性</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {comparisonData.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{row.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{row.avgPrice.toLocaleString()}</td>
                    <td className={`px-4 py-3 text-sm ${row.priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {row.priceChange >= 0 ? '+' : ''}{row.priceChange}%
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{row.volume}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{row.liquidity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderDetailView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          选择要查看详情的任务
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedTasks(new Set(tasks.map(t => t.id)))}
            className="text-sm text-blue-500 hover:text-blue-600"
          >
            全选
          </button>
          <button
            onClick={() => setSelectedTasks(new Set())}
            className="text-sm text-gray-500 hover:text-gray-600"
          >
            清空
          </button>
        </div>
      </div>

      <div className="grid gap-4">
        {tasks.filter(t => t.status === 'completed').map(task => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`bg-white dark:bg-gray-800 rounded-xl border-2 transition-colors cursor-pointer ${
              selectedTasks.has(task.id)
                ? 'border-blue-500'
                : 'border-gray-200 dark:border-gray-700'
            }`}
            onClick={() => toggleSelect(task.id)}
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedTasks.has(task.id)}
                    onChange={() => toggleSelect(task.id)}
                    className="w-4 h-4 text-blue-500 rounded"
                  />
                  <span className="font-medium text-gray-900 dark:text-white">
                    {TASK_TYPE_LABELS[task.type] || task.type}
                  </span>
                </div>
                {onTaskClick && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onTaskClick(task.id);
                    }}
                    className="text-sm text-blue-500 hover:text-blue-600 flex items-center gap-1"
                  >
                    <EyeIcon className="w-4 h-4" />
                    查看完整报告
                  </button>
                )}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                {task.params.city && `${task.params.city}`}
                {task.params.district && ` · ${task.params.district}`}
              </div>
              {task.result && (
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                  <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-32">
                    {JSON.stringify(task.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {selectedTasks.size > 0 && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-4 flex items-center gap-4">
          <span className="text-sm text-gray-600 dark:text-gray-300">
            已选择 {selectedTasks.size} 个任务
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => handleExport('pdf')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <DocumentTextIcon className="w-4 h-4" />
              导出PDF
            </button>
            <button
              onClick={() => handleExport('excel')}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              导出Excel
            </button>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">批量任务结果</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            父任务ID: {parentTaskId}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
          >
            <DocumentTextIcon className="w-4 h-4" />
            导出报告
          </button>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {[
          { mode: 'summary' as ViewMode, label: '摘要视图', icon: DocumentTextIcon },
          { mode: 'comparison' as ViewMode, label: '对比视图', icon: ChartBarIcon },
          { mode: 'detail' as ViewMode, label: '详细视图', icon: EyeIcon },
        ].map(({ mode, label, icon: Icon }) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === mode
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={viewMode}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {viewMode === 'summary' && renderSummaryView()}
          {viewMode === 'comparison' && renderComparisonView()}
          {viewMode === 'detail' && renderDetailView()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default BatchResultView;
