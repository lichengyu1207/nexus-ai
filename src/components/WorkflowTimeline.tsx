import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface SubtaskNode {
  id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying' | 'skipped';
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count?: number;
  started_at?: string;
  completed_at?: string;
  depends_on?: string[];
  critical?: boolean;
}

interface TaskGraph {
  nodes: Record<string, SubtaskNode>;
  edges: Record<string, string[]>;
}

interface WorkflowTimelineProps {
  taskGraph: TaskGraph | null;
  steps: Array<{
    step_id: string;
    step_name: string;
    step_type: string;
    status: string;
    input_data?: Record<string, any>;
    output_data?: Record<string, any>;
    timestamp: string;
  }>;
  onNodeClick?: (nodeId: string) => void;
}

const statusConfig = {
  pending: {
    icon: ClockIcon,
    color: 'text-gray-400',
    bg: 'bg-gray-100 dark:bg-gray-700',
    border: 'border-gray-200 dark:border-gray-600',
    label: '待执行'
  },
  running: {
    icon: ArrowPathIcon,
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    label: '执行中',
    animate: true
  },
  completed: {
    icon: CheckCircleIcon,
    color: 'text-green-500',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    label: '已完成'
  },
  failed: {
    icon: XCircleIcon,
    color: 'text-red-500',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    label: '失败'
  },
  retrying: {
    icon: ArrowPathIcon,
    color: 'text-yellow-500',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    label: '重试中',
    animate: true
  },
  skipped: {
    icon: ExclamationTriangleIcon,
    color: 'text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-800',
    border: 'border-gray-200 dark:border-gray-700',
    label: '已跳过'
  }
};

const agentColors: Record<string, string> = {
  requirement: 'bg-purple-500',
  collector: 'bg-blue-500',
  analyst: 'bg-green-500',
  supervisor: 'bg-orange-500',
};

const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({
  taskGraph,
  steps,
  onNodeClick
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'timeline' | 'graph'>('timeline');

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const formatTime = (dateStr: string | undefined) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getDuration = (start: string | undefined, end: string | undefined) => {
    if (!start || !end) return null;
    const duration = new Date(end).getTime() - new Date(start).getTime();
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}min`;
  };

  const renderNode = (node: SubtaskNode, index: number) => {
    const config = statusConfig[node.status] || statusConfig.pending;
    const Icon = config.icon;
    const isExpanded = expandedNodes.has(node.id);
    const duration = getDuration(node.started_at, node.completed_at);

    return (
      <div
        key={node.id}
        className={`relative ${index > 0 ? 'ml-8' : ''}`}
      >
        {node.depends_on && node.depends_on.length > 0 && (
          <div className="absolute left-0 top-4 w-8 h-0.5 bg-gray-200 dark:bg-gray-700 -translate-x-full" />
        )}
        
        <div
          className={`
            rounded-lg border ${config.border} ${config.bg} p-4
            transition-all duration-200 cursor-pointer
            hover:shadow-md
          `}
          onClick={() => onNodeClick?.(node.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${agentColors[node.agent_name] || 'bg-gray-500'}`} />
              <span className="font-medium text-gray-900 dark:text-white">
                {node.agent_name}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                #{node.id.slice(0, 8)}
              </span>
              {node.critical && (
                <span className="text-xs px-1.5 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded">
                  关键
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-3">
              {duration && (
                <span className="text-xs text-gray-400">{duration}</span>
              )}
              <div className={`flex items-center gap-1 ${config.color}`}>
                <Icon className={`w-5 h-5 ${config.animate ? 'animate-spin' : ''}`} />
                <span className="text-sm">{config.label}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleNode(node.id);
                }}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                {isExpanded ? (
                  <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          {node.error_message && (
            <div className="mt-2 p-2 bg-red-100 dark:bg-red-900/30 rounded text-sm text-red-600 dark:text-red-400">
              {node.error_message}
            </div>
          )}

          {isExpanded && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2">
              {node.input_data && Object.keys(node.input_data).length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">输入数据</span>
                  <pre className="mt-1 text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                    {JSON.stringify(node.input_data, null, 2)}
                  </pre>
                </div>
              )}
              
              {node.output_data && Object.keys(node.output_data).length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">输出数据</span>
                  <pre className="mt-1 text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                    {JSON.stringify(node.output_data, null, 2)}
                  </pre>
                </div>
              )}

              <div className="flex gap-4 text-xs text-gray-400">
                {node.started_at && <span>开始: {formatTime(node.started_at)}</span>}
                {node.completed_at && <span>完成: {formatTime(node.completed_at)}</span>}
                {node.retry_count && node.retry_count > 0 && <span>重试: {node.retry_count}次</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderGraphView = () => {
    if (!taskGraph) return null;

    const executionOrder = getExecutionOrder();
    
    return (
      <div className="space-y-4">
        {executionOrder.map((layer, layerIndex) => (
          <div key={layerIndex}>
            <div className="text-xs text-gray-400 mb-2">层级 {layerIndex + 1}</div>
            <div className="flex gap-4 flex-wrap">
              {layer.map(nodeId => {
                const node = taskGraph.nodes[nodeId];
                if (!node) return null;
                return (
                  <div
                    key={nodeId}
                    className={`
                      w-48 p-3 rounded-lg border
                      ${statusConfig[node.status]?.border || 'border-gray-200'}
                      ${statusConfig[node.status]?.bg || 'bg-gray-50'}
                    `}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-2 h-2 rounded-full ${agentColors[node.agent_name] || 'bg-gray-500'}`} />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {node.agent_name}
                      </span>
                    </div>
                    <div className={`text-xs ${statusConfig[node.status]?.color || 'text-gray-400'}`}>
                      {statusConfig[node.status]?.label || '未知'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const getExecutionOrder = (): string[][] => {
    if (!taskGraph) return [];
    
    const layers: string[][] = [];
    const completed = new Set<string>();
    const remaining = new Set(Object.keys(taskGraph.nodes));

    while (remaining.size > 0) {
      const layer: string[] = [];
      
      for (const nodeId of remaining) {
        const node = taskGraph.nodes[nodeId];
        if (!node) continue;
        
        const deps = node.depends_on || [];
        if (deps.every(dep => completed.has(dep))) {
          layer.push(nodeId);
        }
      }

      if (layer.length === 0) break;
      
      layers.push(layer);
      layer.forEach(id => {
        completed.add(id);
        remaining.delete(id);
      });
    }

    return layers;
  };

  const renderTimelineView = () => {
    if (!taskGraph) return null;

    const nodes = Object.values(taskGraph.nodes);
    
    return (
      <div className="space-y-3">
        {nodes.map((node, index) => renderNode(node, index))}
      </div>
    );
  };

  const stats = taskGraph ? {
    total: Object.keys(taskGraph.nodes).length,
    completed: Object.values(taskGraph.nodes).filter(n => n.status === 'completed').length,
    failed: Object.values(taskGraph.nodes).filter(n => n.status === 'failed').length,
    running: Object.values(taskGraph.nodes).filter(n => n.status === 'running').length,
    pending: Object.values(taskGraph.nodes).filter(n => n.status === 'pending').length,
  } : null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            工作流执行详情
          </h3>
          
          <div className="flex items-center gap-4">
            {stats && (
              <div className="flex items-center gap-3 text-sm">
                <span className="text-gray-500 dark:text-gray-400">
                  总计: <span className="font-medium text-gray-900 dark:text-white">{stats.total}</span>
                </span>
                <span className="text-green-500">
                  完成: <span className="font-medium">{stats.completed}</span>
                </span>
                {stats.running > 0 && (
                  <span className="text-blue-500">
                    执行中: <span className="font-medium">{stats.running}</span>
                  </span>
                )}
                {stats.failed > 0 && (
                  <span className="text-red-500">
                    失败: <span className="font-medium">{stats.failed}</span>
                  </span>
                )}
              </div>
            )}
            
            <div className="flex border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'timeline'
                    ? 'bg-primary-500 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }`}
              >
                时间线
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'graph'
                    ? 'bg-primary-500 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }`}
              >
                图视图
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4">
        {viewMode === 'timeline' ? renderTimelineView() : renderGraphView()}
      </div>
    </div>
  );
};

export default WorkflowTimeline;
