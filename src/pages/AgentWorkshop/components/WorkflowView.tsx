import React, { useCallback, useMemo, Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { WorkflowData, WorkflowNode } from '../types';
import { useWorkflowData } from '../hooks/useWorkflowData';

const ReactFlow = lazy(() => import('reactflow').then((m) => ({ default: m.ReactFlow })));
const Background = lazy(() => import('reactflow').then((m) => ({ default: m.Background })));
const Controls = lazy(() => import('reactflow').then((m) => ({ default: m.Controls })));
const MiniMap = lazy(() => import('reactflow').then((m) => ({ default: m.MiniMap })));

import 'reactflow/dist/style.css';

interface WorkflowViewProps {
  agentId: string;
  onNodeClick: (nodeId: string) => void;
}

const nodeStatusColors = {
  pending: 'border-gray-500 bg-gray-500/10',
  running: 'border-primary bg-primary/10 animate-pulse',
  completed: 'border-green-500 bg-green-500/10',
  failed: 'border-red-500 bg-red-500/10',
};

const nodeTypeIcons: Record<string, string> = {
  start: '▶',
  agent: '🤖',
  tool: '🔧',
  end: '⏹',
  decision: '◇',
  parallel: '⫴',
};

const CustomNode: React.FC<{
  data: WorkflowNode;
  onClick: () => void;
}> = ({ data, onClick }) => {
  return (
    <motion.div
      onClick={onClick}
      className={clsx(
        'px-4 py-3 rounded-lg border-2 cursor-pointer min-w-[120px]',
        'backdrop-blur-md shadow-lg transition-all duration-200',
        'hover:shadow-xl hover:scale-105',
        nodeStatusColors[data.status]
      )}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      role="button"
      tabIndex={0}
      aria-label={`${data.label}, 状态: ${data.status}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg" aria-hidden="true">
          {nodeTypeIcons[data.type] || '●'}
        </span>
        <span className="font-medium text-text-primary text-sm">{data.label}</span>
      </div>
      {data.data?.duration !== undefined && (
        <div className="text-xs text-text-secondary">
          耗时: {(data.data.duration / 1000).toFixed(2)}s
        </div>
      )}
    </motion.div>
  );
};

const LoadingFallback: React.FC = () => (
  <div className="w-full h-full flex items-center justify-center bg-bg-secondary/30">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
      <p className="text-text-secondary">加载工作流...</p>
    </div>
  </div>
);

const WorkflowError: React.FC<{ message: string }> = ({ message }) => (
  <div className="w-full h-full flex items-center justify-center bg-bg-secondary/30">
    <div className="text-center text-red-400">
      <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <p className="text-sm">{message}</p>
    </div>
  </div>
);

const EmptyWorkflow: React.FC = () => (
  <div className="w-full h-full flex items-center justify-center bg-bg-secondary/30">
    <div className="text-center text-text-secondary">
      <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
      </svg>
      <p className="text-sm">暂无工作流数据</p>
    </div>
  </div>
);

export const WorkflowView: React.FC<WorkflowViewProps> = ({ agentId, onNodeClick }) => {
  const { data: workflowData, isLoading, error } = useWorkflowData(agentId);

  const nodes = useMemo(() => {
    if (!workflowData?.nodes) return [];
    return workflowData.nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: node.position || { x: 0, y: 0 },
      data: node,
    }));
  }, [workflowData?.nodes]);

  const edges = useMemo(() => {
    if (!workflowData?.edges) return [];
    return workflowData.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: edge.animated,
      style: { stroke: 'rgba(212, 175, 55, 0.5)', strokeWidth: 2 },
      markerEnd: {
        type: 'arrowclosed' as const,
        color: 'rgba(212, 175, 55, 0.8)',
      },
    }));
  }, [workflowData?.edges]);

  const nodeTypes = useMemo(
    () => ({
      custom: ({ data }: { data: WorkflowNode }) => (
        <CustomNode data={data} onClick={() => onNodeClick(data.id)} />
      ),
    }),
    [onNodeClick]
  );

  if (isLoading) {
    return <LoadingFallback />;
  }

  if (error) {
    return <WorkflowError message="加载工作流失败" />;
  }

  if (!workflowData || workflowData.nodes.length === 0) {
    return <EmptyWorkflow />;
  }

  return (
    <div className="w-full h-full bg-bg-secondary/30 rounded-xl overflow-hidden border border-border-light">
      <Suspense fallback={<LoadingFallback />}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.3}
          maxZoom={2}
          defaultEdgeOptions={{
            style: { stroke: 'rgba(212, 175, 55, 0.5)', strokeWidth: 2 },
          }}
          proOptions={{ hideAttribution: true }}
          className="bg-transparent"
        >
          <Background color="rgba(255,255,255,0.05)" gap={16} />
          <Controls
            className="!bg-bg-secondary/80 !border-border-light !rounded-lg"
            showInteractive={false}
          />
          <MiniMap
            className="!bg-bg-secondary/80 !border-border-light !rounded-lg"
            nodeColor="rgba(212, 175, 55, 0.5)"
            maskColor="rgba(0, 0, 0, 0.8)"
          />
        </ReactFlow>
      </Suspense>
    </div>
  );
};

export default WorkflowView;
