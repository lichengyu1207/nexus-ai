import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { WorkflowNode } from '../types';
import { useNodeDetail } from '../hooks/useWorkflowData';

interface NodeDetailDrawerProps {
  agentId: string;
  nodeId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onJumpToLog?: () => void;
}

const statusLabels = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
};

const statusColors = {
  pending: 'text-gray-400',
  running: 'text-primary',
  completed: 'text-green-400',
  failed: 'text-red-400',
};

const formatDuration = (ms?: number): string => {
  if (!ms) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  return `${(ms / 60000).toFixed(2)}min`;
};

const JsonView: React.FC<{ data: unknown; title: string }> = ({ data, title }) => {
  if (!data) return null;

  return (
    <div className="mb-4">
      <h4 className="text-xs text-text-secondary mb-2">{title}</h4>
      <pre className="text-xs text-text-primary p-3 bg-bg-tertiary/50 rounded-lg overflow-x-auto max-h-32 scrollbar-thin">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};

const LoadingState: React.FC = () => (
  <div className="flex items-center justify-center py-8">
    <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
  </div>
);

const ErrorState: React.FC<{ message: string }> = ({ message }) => (
  <div className="text-center py-8 text-red-400">
    <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <p className="text-sm">{message}</p>
  </div>
);

export const NodeDetailDrawer: React.FC<NodeDetailDrawerProps> = ({
  agentId,
  nodeId,
  isOpen,
  onClose,
  onJumpToLog,
}) => {
  const { data: nodeDetail, isLoading, error } = useNodeDetail(agentId, nodeId || '');

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-bg-secondary border-l border-border-light z-50 flex flex-col"
          >
            <div className="flex items-center justify-between p-4 border-b border-border-light">
              <h3 className="text-lg font-semibold text-text-primary">节点详情</h3>
              <button
                onClick={onClose}
                className="p-2 text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-bg-tertiary/50"
                aria-label="关闭"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-bg-tertiary scrollbar-track-transparent">
              {isLoading && <LoadingState />}
              {error && <ErrorState message="加载节点详情失败" />}
              
              {nodeDetail && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="mb-6">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">
                        {nodeDetail.type === 'start' && '▶'}
                        {nodeDetail.type === 'agent' && '🤖'}
                        {nodeDetail.type === 'tool' && '🔧'}
                        {nodeDetail.type === 'end' && '⏹'}
                        {nodeDetail.type === 'decision' && '◇'}
                        {nodeDetail.type === 'parallel' && '⫴'}
                      </span>
                      <h4 className="text-xl font-semibold text-text-primary">
                        {nodeDetail.label}
                      </h4>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className={clsx('flex items-center gap-1', statusColors[nodeDetail.status])}>
                        <span
                          className={clsx(
                            'w-2 h-2 rounded-full',
                            nodeDetail.status === 'running' && 'animate-pulse',
                            nodeDetail.status === 'pending' && 'bg-gray-400',
                            nodeDetail.status === 'running' && 'bg-primary',
                            nodeDetail.status === 'completed' && 'bg-green-400',
                            nodeDetail.status === 'failed' && 'bg-red-400'
                          )}
                        />
                        {statusLabels[nodeDetail.status]}
                      </span>
                      <span className="text-text-secondary">
                        类型: {nodeDetail.type}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-bg-tertiary/30 rounded-lg">
                        <span className="text-xs text-text-secondary block mb-1">节点ID</span>
                        <span className="text-sm font-mono text-text-primary">{nodeDetail.id}</span>
                      </div>
                      <div className="p-3 bg-bg-tertiary/30 rounded-lg">
                        <span className="text-xs text-text-secondary block mb-1">执行耗时</span>
                        <span className="text-sm text-text-primary">
                          {formatDuration(nodeDetail.data?.duration)}
                        </span>
                      </div>
                    </div>

                    {nodeDetail.data?.input && (
                      <JsonView data={nodeDetail.data.input} title="输入参数" />
                    )}

                    {nodeDetail.data?.output && (
                      <JsonView data={nodeDetail.data.output} title="输出结果" />
                    )}

                    {nodeDetail.data?.logs && nodeDetail.data.logs.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-xs text-text-secondary mb-2">执行日志</h4>
                        <div className="space-y-1">
                          {nodeDetail.data.logs.map((log, index) => (
                            <div
                              key={index}
                              className="text-xs font-mono p-2 bg-bg-tertiary/30 rounded text-text-secondary"
                            >
                              {log}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {nodeDetail.status === 'failed' && (
                      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                        <h4 className="text-xs text-red-400 mb-1">执行失败</h4>
                        <p className="text-sm text-red-300">
                          节点执行过程中发生错误，请查看日志获取详细信息。
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </div>

            {nodeDetail && (
              <div className="p-4 border-t border-border-light">
                <button
                  onClick={onJumpToLog}
                  className="w-full py-2.5 bg-primary text-bg-primary rounded-lg hover:bg-primary-dark transition-colors text-sm font-medium"
                >
                  查看完整日志
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default NodeDetailDrawer;
