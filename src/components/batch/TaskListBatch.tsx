import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrashIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import toast from '@/utils/toast';

type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

interface Task {
  id: string;
  type: string;
  typeLabel: string;
  status: TaskStatus;
  query: string;
  createdAt: string;
  completedAt?: string;
  result?: Record<string, unknown>;
  error?: string;
}

interface TaskListBatchProps {
  tasks: Task[];
  onRefresh?: () => void;
  onTaskClick?: (taskId: string) => void;
}

const STATUS_CONFIG: Record<TaskStatus, { label: string; icon: typeof CheckCircleIcon; color: string; bgColor: string }> = {
  pending: { label: '等待中', icon: ClockIcon, color: 'text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' },
  running: { label: '执行中', icon: ArrowPathIcon, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/20' },
  completed: { label: '已完成', icon: CheckCircleIcon, color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-900/20' },
  failed: { label: '失败', icon: XCircleIcon, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/20' },
};

const TaskListBatch: React.FC<TaskListBatchProps> = ({
  tasks,
  onRefresh,
  onTaskClick,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'status'>('createdAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const filteredTasks = useMemo(() => {
    let filtered = [...tasks];
    
    if (filterStatus !== 'all') {
      filtered = filtered.filter(t => t.status === filterStatus);
    }
    
    filtered.sort((a, b) => {
      if (sortBy === 'createdAt') {
        const dateA = new Date(a.createdAt).getTime();
        const dateB = new Date(b.createdAt).getTime();
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
      } else {
        const statusOrder = { running: 0, pending: 1, failed: 2, completed: 3 };
        const orderA = statusOrder[a.status] ?? 4;
        const orderB = statusOrder[b.status] ?? 4;
        return sortOrder === 'desc' ? orderB - orderA : orderA - orderB;
      }
    });
    
    return filtered;
  }, [tasks, filterStatus, sortBy, sortOrder]);

  const stats = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    
    return { total, completed, failed, running, pending };
  }, [tasks]);

  const isAllSelected = filteredTasks.length > 0 && filteredTasks.every(t => selectedIds.has(t.id));
  const isPartialSelected = filteredTasks.some(t => selectedIds.has(t.id)) && !isAllSelected;

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTasks.map(t => t.id)));
    }
  };

  const toggleSelect = (taskId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    
    setIsDeleting(true);
    try {
      const ids = Array.from(selectedIds);
      await Promise.all(ids.map(id => api.delete(`/api/tasks/${id}`)));
      
      toast.success(`成功删除 ${ids.length} 个任务`);
      setSelectedIds(new Set());
      setShowConfirmDelete(false);
      onRefresh?.();
    } catch (error) {
      toast.error('删除任务失败');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleBatchRetry = async () => {
    const failedIds = Array.from(selectedIds).filter(id => 
      tasks.find(t => t.id === id)?.status === 'failed'
    );
    
    if (failedIds.length === 0) {
      toast.warning('请选择失败的任务进行重试');
      return;
    }
    
    setIsRetrying(true);
    try {
      await Promise.all(failedIds.map(id => api.post(`/api/tasks/${id}/retry`)));
      
      toast.success(`正在重试 ${failedIds.length} 个任务`);
      setSelectedIds(new Set());
      onRefresh?.();
    } catch (error) {
      toast.error('重试任务失败');
    } finally {
      setIsRetrying(false);
    }
  };

  const handleBatchExport = async (format: 'json' | 'csv' | 'zip') => {
    if (selectedIds.size === 0) return;
    
    setIsExporting(true);
    try {
      const ids = Array.from(selectedIds);
      
      if (format === 'zip') {
        const response = await api.post('/api/tasks/export', { task_ids: ids }, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `tasks_export_${Date.now()}.zip`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        const response = await api.post('/api/tasks/export', { task_ids: ids, format });
        const content = format === 'json' 
          ? JSON.stringify(response.data, null, 2)
          : response.data;
        
        const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `tasks_export_${Date.now()}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
      
      toast.success('导出成功');
    } catch (error) {
      toast.error('导出失败');
    } finally {
      setIsExporting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">任务列表</h3>
            <div className="flex items-center gap-2 text-sm">
              <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                {stats.completed} 完成
              </span>
              <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full">
                {stats.failed} 失败
              </span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full">
                {stats.running} 执行中
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as TaskStatus | 'all')}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">全部状态</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
              <option value="running">执行中</option>
              <option value="pending">等待中</option>
            </select>
            
            <button
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              {sortOrder === 'desc' ? (
                <ChevronDownIcon className="w-5 h-5" />
              ) : (
                <ChevronUpIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {selectedIds.size > 0 && (
        <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700 dark:text-blue-400">
              已选择 {selectedIds.size} 个任务
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleBatchRetry}
                disabled={isRetrying}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                <ArrowPathIcon className="w-4 h-4" />
                重试失败
              </button>
              <button
                onClick={() => handleBatchExport('json')}
                disabled={isExporting}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                导出JSON
              </button>
              <button
                onClick={() => handleBatchExport('zip')}
                disabled={isExporting}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
                导出ZIP
              </button>
              <button
                onClick={() => setShowConfirmDelete(true)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                <TrashIcon className="w-4 h-4" />
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="w-12 px-4 py-3">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = isPartialSelected;
                  }}
                  onChange={toggleSelectAll}
                  className="w-4 h-4 text-blue-500 rounded"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                任务类型
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                描述
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                状态
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                创建时间
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredTasks.map((task) => {
              const statusConfig = STATUS_CONFIG[task.status];
              const StatusIcon = statusConfig.icon;
              const isExpanded = expandedId === task.id;

              return (
                <motion.tr
                  key={task.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                    selectedIds.has(task.id) ? 'bg-blue-50 dark:bg-blue-900/10' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(task.id)}
                      onChange={() => toggleSelect(task.id)}
                      className="w-4 h-4 text-blue-500 rounded"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {task.typeLabel}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900 dark:text-white max-w-xs truncate">
                      {task.query}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <StatusIcon className={`w-4 h-4 ${statusConfig.color} ${task.status === 'running' ? 'animate-spin' : ''}`} />
                      <span className={`text-sm ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(task.createdAt)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onTaskClick?.(task.id)}
                        className="text-sm text-blue-500 hover:text-blue-600"
                      >
                        查看
                      </button>
                      {task.status === 'failed' && (
                        <button
                          onClick={() => {
                            setSelectedIds(new Set([task.id]));
                            handleBatchRetry();
                          }}
                          className="text-sm text-orange-500 hover:text-orange-600"
                        >
                          重试
                        </button>
                      )}
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : task.id)}
                        className="text-sm text-gray-500 hover:text-gray-600"
                      >
                        {isExpanded ? '收起' : '展开'}
                      </button>
                    </div>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filteredTasks.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ClockIcon className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>暂无任务记录</p>
        </div>
      )}

      <AnimatePresence>
        {showConfirmDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full"
            >
              <div className="flex items-center gap-3 mb-4">
                <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  确认删除
                </h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                确定要删除选中的 {selectedIds.size} 个任务吗？此操作不可撤销。
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowConfirmDelete(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  取消
                </button>
                <button
                  onClick={handleBatchDelete}
                  disabled={isDeleting}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
                >
                  {isDeleting ? '删除中...' : '确认删除'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TaskListBatch;
