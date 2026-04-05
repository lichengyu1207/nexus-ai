import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BugAntIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ClockIcon,
  CpuChipIcon,
  ChartBarIcon,
  CodeBracketIcon,
  VariableIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import { AgentSelector } from './components/AgentSelector';
import { LogViewer } from './components/LogViewer';
import { CallStackView } from './components/CallStackView';
import { FlameGraph } from './components/FlameGraph';
import { VariableInspector } from './components/VariableInspector';
import { CommandPanel } from './components/CommandPanel';
import { useAgentList } from './hooks/useAgentList';
import { useDebugWebSocket } from './hooks/useDebugWebSocket';
import type { Agent, LogEntry, StackFrame, ViewMode } from './types';

import { AGENT_STATUS_CONFIG } from './types';



type ViewMode = 'logs' | 'stack' | 'variables' | 'flame' | 'metrics' | 'history';

export default function AgentDebugConsole() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('logs');
  const [selectedFrame, setSelectedFrame] = useState<StackFrame | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const { agents, isLoading: agentsLoading, startAgent, stopAgent } = useAgentList();
  const {
    logs,
    callStack,
    variables,
    flameGraph,
    isConnected,
    sendCommand,
    clearLogs,
  } = useDebugWebSocket({
    agentId: selectedAgentId || '',
    onLog: useCallback((entry) => {
      if (entry.level === 'error' || entry.level === 'critical') {
        console.error(`[${entry.level}] ${entry.source}: ${entry.message}`);
      }
    }, []),
  });

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  const handleAgentSelect = useCallback((agentId: string) => {
    setSelectedAgentId(agentId);
    setSelectedFrame(null);
  }, []);

  const handlePause = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('pause');
    }
  }, [selectedAgentId, sendCommand]);

  const handleResume = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('resume');
    }
  }, [selectedAgentId, sendCommand],
  const handleStep = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('step');
    }
  }, [selectedAgentId, sendCommand],
  const handleContinue = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('continue');
    }
  }, [selectedAgentId, sendCommand],
  const handleRestart = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('restart');
    }
  }, [selectedAgentId, sendCommand]);

  const handleStop = useCallback(() => {
    if (selectedAgentId) {
      sendCommand('stop');
    }
  }, [selectedAgentId, sendCommand]);

  const handleEvaluate = useCallback((expression: string) => {
    if (selectedAgentId) {
      sendCommand('evaluate', { expression });
    }
  }, [selectedAgentId, sendCommand]);

  const viewTabs = [
    { key: 'logs', label: '日志', icon: BugAntIcon },
    { key: 'stack', label: '调用栈', icon: ChevronDownIcon },
    { key: 'variables', label: '变量', icon: VariableIcon },
    { key: 'flame', label: '火焰图', icon: ChartBarIcon },
    { key: 'metrics', label: '指标', icon: CpuChipIcon },
  ];

  return (
    <div className="h-screen bg-slate-900 flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-4">
          <AgentSelector
            agents={agents}
            selectedAgentId={selectedAgentId}
            onSelect={handleAgentSelect}
            onStart={startAgent}
            onStop={stopAgent}
            isLoading={agentsLoading}
          />
          <div className="flex items-center gap-2">
            <div className={`
              flex items-center gap-1 px-2 py-1 rounded-full text-xs
              ${isConnected ? 'bg-green-500' : 'bg-slate-500'}
            `}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-slate-400'}`} />
            </div>
            <span className="text-xs text-slate-400">
              {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="p-2 text-slate-400 hover:text-amber-400 transition-colors"
          >
            <ClockIcon className="w-5 h-5" />
          </button>
        </div>
      </header>

      <nav className="flex items-center gap-1 px-4 py-2 border-b border-slate-700/50 overflow-x-auto">
        {viewTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setViewMode(tab.key)}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors whitespace-nowrap
              ${viewMode === tab.key 
                ? 'bg-amber-500/20 text-amber-400' 
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}
            `}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            {viewMode === 'logs' && (
              <motion.div
              key="logs"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
              >
                <LogViewer
                  logs={logs}
                  onClear={clearLogs}
                  isLoading={!isConnected && agentsLoading}
                />
              </motion.div>
            )}
            {viewMode === 'stack' && (
              <motion.div
              key="stack"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
              >
                <CallStackView
                  stack={callStack}
                  onFrameClick={setSelectedFrame}
                  selectedFrameId={selectedFrame?.id}
                />
              </motion.div>
            )}
            {viewMode === 'variables' && (
              <motion.div
              key="variables"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
              >
                <VariableInspector variables={variables} />
              </motion.div>
            )}
            {viewMode === 'flame' && (
              <motion.div
              key="flame"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full bg-slate-800/50 rounded-xl border border-slate-700/50"
              >
                {flameGraph ? (
                  <FlameGraph
                    data={flameGraph}
                    onNodeClick={setSelectedFrame}
                    width={800}
                    height={400}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500">
                    暂无性能数据
                  </div>
                )}
              </motion.div>
            )}
            {viewMode === 'metrics' && (
              <motion.div
                key="metrics"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full bg-slate-800/50 rounded-xl border border-slate-700/50 p-4"
              >
                <div className="text-slate-400 text-sm mb-4">性能指标</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-amber-400">--</div>
                    <div className="text-xs text-slate-500">CPU 使用率</div>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-400">--</div>
                    <div className="text-xs text-slate-500">内存使用</div>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-400">--</div>
                    <div className="text-xs text-slate-500">网络请求</div>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-400">--</div>
                    <div className="text-xs text-slate-500">执行时间</div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="w-80 border-l border-slate-700/50">
          <DebugControlBar
            onPause={handlePause}
            onResume={handleResume}
            onStep={handleStep}
            onContinue={handleContinue}
            onRestart={handleRestart}
            onStop={handleStop}
            isPaused={selectedAgent?.status === 'paused'}
          />
          <CommandPanel onExecute={handleEvaluate} />
        </div>
      </div>

      <AnimatePresence>
        {isHistoryOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsHistoryOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-2xl bg-slate-800 rounded-xl border border-slate-700/50 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">调试历史</h2>
                <button
                  onClick={() => setIsHistoryOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <div className="text-slate-400 text-sm">暂无历史记录</div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
