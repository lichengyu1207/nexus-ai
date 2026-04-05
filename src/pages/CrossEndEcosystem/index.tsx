import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EndTabs } from './components/EndTabs';
import { EndStatisticsCards } from './components/EndStatisticsCards';
import { CollaborationTimeline } from './components/CollaborationTimeline';
import { CrossEndMessaging } from './components/CrossEndMessaging';
import { EndInfoSidebar } from './components/EndInfoSidebar';
import { useWebSocket } from './hooks/useWebSocket';
import type { End, EndName, WebSocketMessage } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const defaultEnds: End[] = [
  { id: 'university', name: 'university', displayName: '院校端', unreadCount: 3 },
  { id: 'enterprise', name: 'enterprise', displayName: '企业端', unreadCount: 0 },
  { id: 'government', name: 'government', displayName: '政府端', unreadCount: 5 },
  { id: 'association', name: 'association', displayName: '协会端', unreadCount: 0 },
  { id: 'public', name: 'public', displayName: '公众端', unreadCount: 2 },
];

const pageVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

function CrossEndEcosystemContent() {
  const [ends, setEnds] = useState<End[]>(defaultEnds);
  const [selectedEndId, setSelectedEndId] = useState<string>('university');
  const [activeSection, setActiveSection] = useState<'timeline' | 'messages'>('timeline');

  const selectedEnd = ends.find((e) => e.id === selectedEndId);
  const selectedEndName = selectedEnd?.name as EndName;

  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    if (data.type === 'new_message') {
      const message = data.payload;
      if ('fromEnd' in message) {
        setEnds((prevEnds) =>
          prevEnds.map((end) => {
            if (end.name === message.fromEnd) {
              return { ...end, unreadCount: end.unreadCount + 1 };
            }
            return end;
          })
        );
      }
    } else if (data.type === 'messageRead') {
      const message = data.payload;
      if ('fromEnd' in message) {
        setEnds((prevEnds) =>
          prevEnds.map((end) => {
            if (end.name === message.fromEnd && end.unreadCount > 0) {
              return { ...end, unreadCount: end.unreadCount - 1 };
            }
            return end;
          })
        );
      }
    }
  }, []);

  const { isConnected, isReconnecting, error: wsError } = useWebSocket({
    endId: selectedEndName,
    onMessage: handleWebSocketMessage,
  });

  const handleSelectEnd = (endId: string) => {
    setSelectedEndId(endId);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-[1600px] mx-auto">
        <header className="px-6 py-4 border-b border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">五端协同生态</h1>
              <p className="text-gray-400 text-sm mt-1">
                院校 · 企业 · 政府 · 协会 · 公众 跨端协作枢纽
              </p>
            </div>
            <div className="flex items-center gap-3">
              {wsError && (
                <span className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm">
                  连接错误
                </span>
              )}
              {isReconnecting && (
                <span className="px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-sm">
                  重连中...
                </span>
              )}
              {isConnected && (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm">
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  实时连接
                </span>
              )}
            </div>
          </div>
        </header>

        <EndTabs
          ends={ends}
          selectedEndId={selectedEndId}
          onSelectEnd={handleSelectEnd}
        />

        <div className="flex">
          <main className="flex-1 p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedEndId}
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.2 }}
              >
                <EndStatisticsCards endId={selectedEndName} />

                <div className="mb-4">
                  <div className="flex gap-2 p-1 rounded-lg bg-slate-800/50 w-fit">
                    <button
                      onClick={() => setActiveSection('timeline')}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeSection === 'timeline'
                          ? 'bg-amber-500 text-slate-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      协同事件
                    </button>
                    <button
                      onClick={() => setActiveSection('messages')}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeSection === 'messages'
                          ? 'bg-amber-500 text-slate-900'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      跨端消息
                    </button>
                  </div>
                </div>

                <AnimatePresence mode="wait">
                  {activeSection === 'timeline' ? (
                    <motion.div
                      key="timeline"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <CollaborationTimeline endId={selectedEndName} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="messages"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <CrossEndMessaging endId={selectedEndName} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </AnimatePresence>
          </main>

          <EndInfoSidebar endId={selectedEndName} />
        </div>
      </div>
    </div>
  );
}

export default function CrossEndEcosystem() {
  return (
    <QueryClientProvider client={queryClient}>
      <CrossEndEcosystemContent />
    </QueryClientProvider>
  );
}
