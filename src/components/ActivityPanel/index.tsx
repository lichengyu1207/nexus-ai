import { useState, useCallback, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FloatingButton } from './FloatingButton';
import { AgentStatusList } from './AgentStatusList';
import { TaskQueueList } from './TaskQueueList';
import { CallLogList } from './CallLogList';
import { LogDetailModal } from './LogDetailModal';
import { useActivityWebSocket } from './hooks/useActivityWebSocket';
import { useActivitySnapshot } from './hooks/useActivitySnapshot';
import type { AgentStatus, QueueTask, CallLog, ActivityTab } from './types';

const STORAGE_KEY = 'activity_panel_open';
const MAX_LOGS = 200;

const tabs: { key: ActivityTab; label: string; icon: string }[] = [
  { key: 'agents', label: '智能体', icon: '🤖' },
  { key: 'tasks', label: '任务队列', icon: '📋' },
  { key: 'logs', label: '调用日志', icon: '📜' },
];

export default function ActivityPanel() {
  const [isOpen, setIsOpen] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(STORAGE_KEY) === 'true';
  });
  const [activeTab, setActiveTab] = useState<ActivityTab>('agents');
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [tasks, setTasks] = useState<QueueTask[]>([]);
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);

  const { data: snapshot, isLoading, refetch } = useActivitySnapshot(isOpen);

  useEffect(() => {
    if (snapshot) {
      setAgents(snapshot.agents);
      setTasks(snapshot.tasks);
      setLogs(snapshot.logs);
    }
  }, [snapshot]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(isOpen));
    if (isOpen) {
      setUnreadCount(0);
    }
  }, [isOpen]);

  const handleAgentStatusUpdate = useCallback((agent: AgentStatus) => {
    setAgents((prev) => {
      const index = prev.findIndex((a) => a.id === agent.id);
      if (index >= 0) {
        const next = [...prev];
        next[index] = agent;
        return next;
      }
      return [...prev, agent];
    });
  }, []);

  const handleTaskQueueUpdate = useCallback((newTasks: QueueTask[]) => {
    setTasks(newTasks);
  }, []);

  const handleNewCallLog = useCallback((log: CallLog) => {
    setLogs((prev) => {
      const next = [...prev, log];
      if (next.length > MAX_LOGS) {
        return next.slice(-MAX_LOGS);
      }
      return next;
    });
    if (!isOpen) {
      setUnreadCount((prev) => prev + 1);
    }
  }, [isOpen]);

  const { isConnected, isReconnecting, error, reconnect } = useActivityWebSocket({
    onAgentStatusUpdate: handleAgentStatusUpdate,
    onTaskQueueUpdate: handleTaskQueueUpdate,
    onNewCallLog: handleNewCallLog,
    enabled: true,
  });

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
    reconnect();
  }, [refetch, reconnect]);

  const handleLogClick = useCallback((log: CallLog) => {
    setSelectedLog(log);
  }, []);

  const handleCloseModal = useCallback(() => {
    setSelectedLog(null);
  }, []);

  const statusColor = useMemo(() => {
    if (error) return 'bg-red-500';
    if (isReconnecting) return 'bg-yellow-500';
    if (isConnected) return 'bg-green-500';
    return 'bg-gray-500';
  }, [error, isReconnecting, isConnected]);

  return (
    <>
      <AnimatePresence>
        {!isOpen && (
          <FloatingButton
            onClick={handleToggle}
            hasUnread={unreadCount > 0}
            unreadCount={unreadCount}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: 320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 320, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-80 z-40
              bg-slate-900/95 backdrop-blur-xl border-l border-amber-500/20
              shadow-2xl flex flex-col"
            role="region"
            aria-label="智能体活动面板"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-white">智能体活动</h2>
                <div className={`w-2 h-2 rounded-full ${statusColor}`} title={
                  error ? '连接错误' : isReconnecting ? '重连中' : isConnected ? '已连接' : '未连接'
                } />
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRefresh}
                  className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-slate-700"
                  aria-label="刷新"
                  title="刷新"
                >
                  🔄
                </button>
                <button
                  onClick={handleToggle}
                  className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-slate-700"
                  aria-label="关闭面板"
                >
                  ✕
                </button>
              </div>
            </div>

            {error && (
              <div className="px-4 py-2 bg-red-500/20 text-red-400 text-xs text-center">
                连接错误，正在重试...
              </div>
            )}

            {isReconnecting && (
              <div className="px-4 py-2 bg-yellow-500/20 text-yellow-400 text-xs text-center">
                正在重连...
              </div>
            )}

            <div className="flex border-b border-slate-700/50">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 py-2 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? 'text-amber-400 border-b-2 border-amber-500'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <span className="mr-1">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-hidden">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="h-full overflow-y-auto p-4"
                  >
                    {activeTab === 'agents' && <AgentStatusList agents={agents} />}
                    {activeTab === 'tasks' && <TaskQueueList tasks={tasks} />}
                    {activeTab === 'logs' && (
                      <CallLogList
                        logs={logs}
                        onLogClick={handleLogClick}
                        autoScroll={true}
                      />
                    )}
                  </motion.div>
                </AnimatePresence>
              )}
            </div>

            <div className="p-3 border-t border-slate-700/50 bg-slate-900/50">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>智能体: {agents.length}</span>
                <span>队列: {tasks.length}</span>
                <span>日志: {logs.length}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <LogDetailModal
        log={selectedLog}
        isOpen={!!selectedLog}
        onClose={handleCloseModal}
      />
    </>
  );
}
