import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useAgents, useAgent } from './hooks/useAgents';
import { AgentList } from './components/AgentList';
import { WorkflowView } from './components/WorkflowView';
import { ToolPermissionsTable } from './components/ToolPermissionsTable';
import { RunLogsView } from './components/RunLogsView';
import { NodeDetailDrawer } from './components/NodeDetailDrawer';

type TabId = 'workflow' | 'tools' | 'logs';

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  {
    id: 'workflow',
    label: '工作流',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
      </svg>
    ),
  },
  {
    id: 'tools',
    label: '工具权限',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 'logs',
    label: '运行日志',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

const statusColors = {
  healthy: 'text-green-400',
  busy: 'text-yellow-400',
  error: 'text-red-400',
};

const statusLabels = {
  healthy: '健康',
  busy: '繁忙',
  error: '异常',
};

const departmentLabels = {
  san: '三省',
  liu: '六部',
};

const EmptyState: React.FC = () => (
  <div className="h-full flex items-center justify-center">
    <div className="text-center text-text-secondary">
      <svg className="w-24 h-24 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h3 className="text-lg font-medium mb-2">选择一个智能体</h3>
      <p className="text-sm">从左侧列表中选择一个智能体查看详情</p>
    </div>
  </div>
);

export const AgentWorkshop: React.FC = () => {
  const { data: agents = [], isLoading: isLoadingAgents } = useAgents();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('workflow');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const { data: selectedAgent } = useAgent(selectedAgentId || '');

  const isAdmin = true;

  const handleSelectAgent = useCallback((id: string) => {
    setSelectedAgentId(id);
    setActiveTab('workflow');
    setSelectedNodeId(null);
    setIsDrawerOpen(false);
  }, []);

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
    setIsDrawerOpen(true);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setIsDrawerOpen(false);
  }, []);

  const handleJumpToLog = useCallback(() => {
    setIsDrawerOpen(false);
    setActiveTab('logs');
  }, []);

  return (
    <div className="h-screen flex bg-bg-primary">
      <AgentList
        agents={agents}
        selectedAgentId={selectedAgentId || ''}
        onSelectAgent={handleSelectAgent}
        isLoading={isLoadingAgents}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedAgent ? (
          <>
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="px-6 py-4 border-b border-border-light bg-bg-secondary/30"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <h1 className="text-xl font-semibold text-text-primary flex items-center gap-2">
                      {selectedAgent.name}
                      <span
                        className={clsx(
                          'text-xs px-2 py-0.5 rounded-full',
                          statusColors[selectedAgent.status],
                          'bg-current/10'
                        )}
                      >
                        {statusLabels[selectedAgent.status]}
                      </span>
                    </h1>
                    <p className="text-sm text-text-secondary mt-1">
                      {departmentLabels[selectedAgent.department]} · {selectedAgent.description}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm text-text-secondary">
                  <div className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <span>{selectedAgent.currentTasks} 个任务</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-1 mt-4">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-all',
                      activeTab === tab.id
                        ? 'bg-primary/20 text-primary'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                    )}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                ))}
              </div>
            </motion.div>

            <div className="flex-1 overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="h-full p-6"
                >
                  {activeTab === 'workflow' && (
                    <WorkflowView
                      agentId={selectedAgentId!}
                      onNodeClick={handleNodeClick}
                    />
                  )}
                  {activeTab === 'tools' && (
                    <div className="h-full bg-bg-secondary/30 rounded-xl border border-border-light overflow-hidden">
                      <ToolPermissionsTable
                        agentId={selectedAgentId!}
                        isAdmin={isAdmin}
                      />
                    </div>
                  )}
                  {activeTab === 'logs' && (
                    <div className="h-full bg-bg-secondary/30 rounded-xl border border-border-light overflow-hidden">
                      <RunLogsView agentId={selectedAgentId!} />
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </>
        ) : (
          <EmptyState />
        )}
      </div>

      <NodeDetailDrawer
        agentId={selectedAgentId || ''}
        nodeId={selectedNodeId}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onJumpToLog={handleJumpToLog}
      />
    </div>
  );
};

export default AgentWorkshop;
