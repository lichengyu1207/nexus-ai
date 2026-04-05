import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ClockIcon,
  PlayIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

interface AgentNode {
  id: string;
  name: string;
  nameCn: string;
  description: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

interface WorkflowEdge {
  from: string;
  to: string;
  label?: string;
}

interface AgentWorkflowStatusProps {
  nodes: AgentNode[];
  edges: WorkflowEdge[];
  activeNodeId?: string;
  onNodeClick?: (node: AgentNode) => void;
  compact?: boolean;
}

const statusConfigs = {
  idle: {
    icon: ClockIcon,
    color: 'text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    borderColor: 'border-gray-200 dark:border-gray-700',
    glowColor: '',
  },
  running: {
    icon: PlayIcon,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-400 dark:border-blue-500',
    glowColor: 'shadow-blue-500/30',
  },
  completed: {
    icon: CheckCircleIcon,
    color: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-400 dark:border-green-500',
    glowColor: 'shadow-green-500/30',
  },
  failed: {
    icon: ExclamationCircleIcon,
    color: 'text-red-500',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-400 dark:border-red-500',
    glowColor: 'shadow-red-500/30',
  },
};

const provinceColors = {
  zhongshu: 'from-amber-500 to-orange-500',
  menxia: 'from-purple-500 to-pink-500',
  shangshu: 'from-blue-500 to-cyan-500',
};

const AgentWorkflowStatus: React.FC<AgentWorkflowStatusProps> = ({
  nodes,
  edges,
  activeNodeId,
  onNodeClick,
  compact = false,
}) => {
  const [selectedNode, setSelectedNode] = useState<AgentNode | null>(null);
  const [animatingEdge, setAnimatingEdge] = useState<string | null>(null);

  useEffect(() => {
    const runningEdges = edges.filter((edge) => {
      const fromNode = nodes.find((n) => n.id === edge.from);
      const toNode = nodes.find((n) => n.id === edge.to);
      return fromNode?.status === 'completed' && toNode?.status === 'running';
    });

    if (runningEdges.length > 0) {
      const edgeId = `${runningEdges[0].from}-${runningEdges[0].to}`;
      setAnimatingEdge(edgeId);
    } else {
      setAnimatingEdge(null);
    }
  }, [nodes, edges]);

  const getNodeProvince = (nodeId: string): string => {
    if (nodeId.includes('zhongshu') || nodeId.includes('中书')) return 'zhongshu';
    if (nodeId.includes('menxia') || nodeId.includes('门下')) return 'menxia';
    return 'shangshu';
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  const renderNode = (node: AgentNode) => {
    const config = statusConfigs[node.status];
    const StatusIcon = config.icon;
    const province = getNodeProvince(node.id);
    const isActive = activeNodeId === node.id;

    return (
      <motion.div
        key={node.id}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileHover={{ scale: 1.05 }}
        onClick={() => {
          setSelectedNode(node);
          onNodeClick?.(node);
        }}
        className={`
          relative cursor-pointer p-4 rounded-xl border-2 transition-all
          ${config.bgColor} ${config.borderColor}
          ${isActive ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
          ${node.status === 'running' ? `shadow-lg ${config.glowColor}` : ''}
        `}
      >
        {node.status === 'running' && (
          <motion.div
            className="absolute inset-0 rounded-xl"
            animate={{
              boxShadow: [
                `0 0 0px ${config.glowColor}`,
                `0 0 20px ${config.glowColor}`,
                `0 0 0px ${config.glowColor}`,
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}

        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-lg bg-gradient-to-r ${provinceColors[province]} flex items-center justify-center text-white text-lg shadow-md`}
          >
            {node.name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-gray-900 dark:text-white truncate">
              {node.nameCn}
            </h4>
            <p className="text-xs text-gray-500 truncate">{node.description}</p>
          </div>
          <StatusIcon
            className={`w-5 h-5 ${config.color} ${
              node.status === 'running' ? 'animate-pulse' : ''
            }`}
          />
        </div>

        {node.status === 'running' && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>进度</span>
              <span>{node.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${node.progress}%` }}
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
              />
            </div>
          </div>
        )}

        {node.status === 'completed' && node.duration && (
          <div className="mt-2 text-xs text-gray-500">
            耗时: {formatDuration(node.duration)}
          </div>
        )}
      </motion.div>
    );
  };

  const renderEdge = (edge: WorkflowEdge) => {
    const isAnimating = animatingEdge === `${edge.from}-${edge.to}`;
    const fromNode = nodes.find((n) => n.id === edge.from);
    const toNode = nodes.find((n) => n.id === edge.to);
    const isActive = fromNode?.status === 'completed' && toNode?.status !== 'idle';

    return (
      <motion.div
        key={`${edge.from}-${edge.to}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative flex items-center justify-center py-2"
      >
        <div className="flex flex-col items-center">
          {edge.label && (
            <span className="text-xs text-gray-400 mb-1">{edge.label}</span>
          )}
          <div className="relative h-8 w-0.5">
            <div
              className={`absolute inset-0 ${
                isActive ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            />
            {isAnimating && (
              <motion.div
                className="absolute w-2 h-2 rounded-full bg-primary-500 -left-[3px]"
                animate={{
                  top: ['0%', '100%'],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  if (compact) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          工作流状态
        </h3>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {nodes.map((node, index) => {
            const config = statusConfigs[node.status];
            const StatusIcon = config.icon;
            return (
              <React.Fragment key={node.id}>
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  onClick={() => {
                    setSelectedNode(node);
                    onNodeClick?.(node);
                  }}
                  className={`flex-shrink-0 w-10 h-10 rounded-lg ${config.bgColor} border ${config.borderColor} flex items-center justify-center cursor-pointer`}
                >
                  <StatusIcon
                    className={`w-5 h-5 ${config.color} ${
                      node.status === 'running' ? 'animate-spin' : ''
                    }`}
                  />
                </motion.div>
                {index < nodes.length - 1 && (
                  <div className="w-4 h-0.5 bg-gray-300 dark:bg-gray-600" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            三省六部工作流
          </h3>
          <div className="flex items-center gap-4 text-xs">
            {Object.entries(statusConfigs).map(([status, config]) => {
              const Icon = config.icon;
              return (
                <div key={status} className="flex items-center gap-1">
                  <Icon className={`w-4 h-4 ${config.color}`} />
                  <span className="text-gray-500">
                    {status === 'idle' ? '等待' : status === 'running' ? '运行' : status === 'completed' ? '完成' : '失败'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          {nodes.map((node, index) => (
            <React.Fragment key={node.id}>
              {renderNode(node)}
              {index < nodes.length - 1 && edges.find((e) => e.from === node.id) && (
                renderEdge(edges.find((e) => e.from === node.id)!)
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedNode(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {selectedNode.nameCn}
                </h4>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <XMarkIcon className="w-5 h-5 text-gray-400" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500">描述</label>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {selectedNode.description}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-500">状态</label>
                    <p className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                      {selectedNode.status}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">耗时</label>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {formatDuration(selectedNode.duration)}
                    </p>
                  </div>
                </div>

                {selectedNode.input && Object.keys(selectedNode.input).length > 0 && (
                  <div>
                    <label className="text-xs text-gray-500">输入</label>
                    <pre className="mt-1 p-3 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-auto max-h-32">
                      {JSON.stringify(selectedNode.input, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedNode.output && Object.keys(selectedNode.output).length > 0 && (
                  <div>
                    <label className="text-xs text-gray-500">输出</label>
                    <pre className="mt-1 p-3 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-auto max-h-32">
                      {JSON.stringify(selectedNode.output, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AgentWorkflowStatus;
