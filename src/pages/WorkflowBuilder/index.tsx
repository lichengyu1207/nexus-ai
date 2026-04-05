import { useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useWorkflow, useWorkflowStore } from './hooks/useWorkflow';
import { useWorkflowExecution } from './hooks/useWorkflowExecution';
import { NodeLibrary } from './components/NodeLibrary';
import { WorkflowCanvas } from './components/WorkflowCanvas';
import { NodeConfigPanel } from './components/NodeConfigPanel';
import { Toolbar } from './components/Toolbar';
import { VersionHistoryModal } from './components/VersionHistoryModal';
import { TestRunner } from './components/TestRunner';
import { TemplateMarketplace } from './components/TemplateMarketplace';
import type { WorkflowTemplate, WorkflowVersion, NodeType } from './types';

export default function WorkflowBuilderPage() {
  const { id } = useParams<{ id: string }>();
  const workflowId = id;

  const [showVersions, setShowVersions] = useState(false);
  const [showTestRunner, setShowTestRunner] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);

  const {
    workflow,
    versions,
    isLoading,
    nodes,
    selectedNode,
    hasUnsavedChanges,
    addNode,
    updateNode,
    addEdge,
    save,
    publish,
    isSaving,
    isPublishing,
  } = useWorkflow(workflowId);

  const {
    status: executionStatus,
    nodeStatuses,
    logs,
    startExecution,
    stopExecution,
    resetExecution,
  } = useWorkflowExecution(workflowId);

  const handleDragStart = useCallback(() => {
    // 可以用于设置拖拽状态
  }, []);

  const handleNodeClick = useCallback((type: NodeType) => {
    const newNode = {
      id: `${type}_${Date.now()}`,
      type,
      position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        label: type === 'agent' ? '智能体' : type === 'tool' ? '工具' : type === 'condition' ? '条件' : type === 'loop' ? '循环' : type === 'subflow' ? '子流程' : '触发器',
        config: {},
        inputs: {},
        outputs: {},
        errorHandling: 'fail' as const,
      },
    };
    addNode(newNode);
  }, [addNode]);

  const handleNodeUpdate = useCallback((nodeId: string, data: Record<string, unknown>) => {
    updateNode(nodeId, data);
  }, [updateNode]);

  const handleRollback = useCallback((version: WorkflowVersion) => {
    if (workflow) {
      useWorkflowStore.getState().reset({
        ...workflow,
        nodes: version.nodes,
        edges: version.edges,
      });
    }
    setShowVersions(false);
  }, [workflow]);

  const handleImportTemplate = useCallback((template: WorkflowTemplate) => {
    template.workflow.nodes.forEach((node) => addNode(node));
    template.workflow.edges.forEach((edge) => addEdge(edge));
    setShowTemplates(false);
  }, [addNode, addEdge]);

  const handleAutoLayout = useCallback(() => {
    const nodeMap = new Map<string, { x: number; y: number }>();
    let currentX = 50;
    let currentY = 50;
    const spacing = 150;

    nodes.forEach((node) => {
      nodeMap.set(node.id, { x: currentX, y: currentY });
      currentY += spacing;
      if (currentY > 600) {
        currentY = 50;
        currentX += spacing;
      }
    });

    const updatedNodes = nodes.map((node) => ({
      ...node,
      position: nodeMap.get(node.id) || node.position,
    }));
    useWorkflowStore.getState().setNodes(updatedNodes);
  }, [nodes]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      <Toolbar
        workflowName={workflow?.name || '新工作流'}
        version={workflow?.version || 1}
        hasUnsavedChanges={hasUnsavedChanges}
        isSaving={isSaving}
        isPublishing={isPublishing}
        onSave={save}
        onPublish={publish}
        onTest={() => setShowTestRunner(true)}
        onShowVersions={() => setShowVersions(true)}
        onAutoLayout={handleAutoLayout}
        onShowTemplates={() => setShowTemplates(true)}
      />

      <div className="flex-1 flex overflow-hidden">
        <NodeLibrary
          onDragStart={handleDragStart}
          onNodeClick={handleNodeClick}
        />

        <div className="flex-1 relative">
          <WorkflowCanvas nodeStatuses={nodeStatuses} />
        </div>

        {selectedNode && (
          <NodeConfigPanel
            node={selectedNode}
            onUpdate={handleNodeUpdate}
            onClose={() => {}}
          />
        )}
      </div>

      <VersionHistoryModal
        isOpen={showVersions}
        onClose={() => setShowVersions(false)}
        versions={versions || []}
        currentVersion={workflow?.version || 1}
        onRollback={handleRollback}
        onCompare={() => {}}
      />

      <TestRunner
        isOpen={showTestRunner}
        onClose={() => setShowTestRunner(false)}
        nodeExecutions={nodes.map((n) => ({
          nodeId: n.id,
          status: nodeStatuses[n.id] || 'pending',
          startedAt: new Date().toISOString(),
        }))}
        logs={logs}
        status={executionStatus}
        onStart={startExecution}
        onStop={stopExecution}
        onReset={resetExecution}
      />

      <TemplateMarketplace
        isOpen={showTemplates}
        onClose={() => setShowTemplates(false)}
        onImport={handleImportTemplate}
      />
    </div>
  );
}
