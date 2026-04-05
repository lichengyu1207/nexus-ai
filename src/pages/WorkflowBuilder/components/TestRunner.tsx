import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayIcon,
  StopIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import type { NodeExecution } from '../types';

interface ExecutionLog {
  timestamp: string;
  nodeId?: string;
  message: string;
  type: 'info' | 'error' | 'warning' | 'success';
}

interface TestRunnerProps {
  isOpen: boolean;
  onClose: () => void;
  nodeExecutions: NodeExecution[];
  logs: ExecutionLog[];
  status: 'idle' | 'running' | 'completed' | 'failed';
  onStart: (inputs: unknown) => void;
  onStop: () => void;
  onReset: () => void;
}

export function TestRunner({
  isOpen,
  onClose,
  nodeExecutions,
  logs,
  status,
  onStart,
  onStop,
  onReset,
}: TestRunnerProps) {
  const [inputs, setInputs] = useState<string>('');
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);

  const handleStart = useCallback(() => {
    try {
      const parsed = JSON.parse(inputs || '{}');
      onStart(parsed);
    } catch {
      onStart({});
    }
  }, [inputs, onStart]);

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) =>
      prev.includes(nodeId)
        ? prev.filter((id) => id !== nodeId)
        : [...prev, nodeId]
    );
  }, []);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-slate-800 rounded-xl border border-slate-700/50 w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col"
        >
          <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
            <div className="flex items-center gap-2">
              <PlayIcon className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-semibold text-white">测试运行</h2>
              <span className={`
                px-2 py-0.5 text-xs rounded
                ${status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                  status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  'bg-slate-700/50 text-slate-400'}
              `}>
                {status === 'idle' ? '待机' :
                 status === 'running' ? '运行中' :
                 status === 'completed' ? '已完成' :
                 '失败'}
              </span>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 flex overflow-hidden">
            <div className="w-1/2 border-r border-slate-700/50 flex flex-col">
              <div className="p-4 border-b border-slate-700/50">
                <h3 className="text-sm font-medium text-white mb-2">输入参数</h3>
                <textarea
                  value={inputs}
                  onChange={(e) => setInputs(e.target.value)}
                  disabled={status === 'running'}
                  className="w-full h-24 px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-amber-500/50 disabled:opacity-50"
                  placeholder='{"key": "value"}'
                />
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                <h3 className="text-sm font-medium text-white mb-2">执行日志</h3>
                <div className="space-y-1">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className={`
                        text-xs p-2 rounded
                        ${log.type === 'error' ? 'bg-red-500/10 text-red-400' :
                          log.type === 'warning' ? 'bg-yellow-500/10 text-yellow-400' :
                          log.type === 'success' ? 'bg-green-500/10 text-green-400' :
                          'bg-slate-700/30 text-slate-300'}
                      `}
                    >
                      <span className="text-slate-500 mr-2">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      {log.message}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="w-1/2 flex flex-col">
              <div className="p-4 border-b border-slate-700/50">
                <h3 className="text-sm font-medium text-white mb-2">节点执行状态</h3>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-2">
                  {nodeExecutions.map((nodeExec) => (
                    <div key={nodeExec.nodeId} className="bg-slate-900/50 rounded-lg border border-slate-700/30">
                      <button
                        onClick={() => toggleNode(nodeExec.nodeId)}
                        className="w-full flex items-center justify-between p-3 text-left"
                      >
                        <div className="flex items-center gap-2">
                          <span className={`
                            w-2 h-2 rounded-full
                            ${nodeExec.status === 'completed' ? 'bg-green-500' :
                              nodeExec.status === 'running' ? 'bg-blue-500 animate-pulse' :
                              nodeExec.status === 'failed' ? 'bg-red-500' :
                              'bg-slate-500'}
                          `} />
                          <span className="text-sm text-white">{nodeExec.nodeId}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`
                            text-xs
                            ${nodeExec.status === 'completed' ? 'text-green-400' :
                              nodeExec.status === 'running' ? 'text-blue-400' :
                              nodeExec.status === 'failed' ? 'text-red-400' :
                              'text-slate-400'}
                          `}>
                            {nodeExec.status}
                          </span>
                          {expandedNodes.includes(nodeExec.nodeId) ? (
                            <ChevronDownIcon className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronRightIcon className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      </button>

                      <AnimatePresence>
                        {expandedNodes.includes(nodeExec.nodeId) && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="px-3 pb-3 space-y-2"
                          >
                            <div>
                              <h4 className="text-xs text-slate-400 mb-1">输入</h4>
                              <pre className="text-xs text-slate-300 bg-slate-800/50 p-2 rounded overflow-x-auto">
                                {JSON.stringify(nodeExec.input, null, 2)}
                              </pre>
                            </div>
                            {nodeExec.output && (
                              <div>
                                <h4 className="text-xs text-slate-400 mb-1">输出</h4>
                                <pre className="text-xs text-slate-300 bg-slate-800/50 p-2 rounded overflow-x-auto">
                                  {JSON.stringify(nodeExec.output, null, 2)}
                                </pre>
                              </div>
                            )}
                            {nodeExec.error && (
                              <div>
                                <h4 className="text-xs text-red-400 mb-1">错误</h4>
                                <p className="text-xs text-red-300">{nodeExec.error}</p>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-slate-700/50 flex items-center justify-end gap-2">
            {status === 'idle' && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStart}
                className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium hover:bg-amber-400 transition-colors"
              >
                <PlayIcon className="w-4 h-4" />
                开始测试
              </motion.button>
            )}
            {status === 'running' && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onStop}
                className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm font-medium hover:bg-red-500/30 transition-colors"
              >
                <StopIcon className="w-4 h-4" />
                停止
              </motion.button>
            )}
            {(status === 'completed' || status === 'failed') && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onReset}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 text-white rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors"
              >
                重新测试
              </motion.button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default TestRunner;
