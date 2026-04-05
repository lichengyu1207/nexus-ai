import { useCallback, lazy, Suspense } from 'react';
import type { Node, Edge, Connection } from 'reactflow';

const ReactFlow = lazy(() => import('reactflow').then((m) => ({ default: m.ReactFlow })));
const Controls = lazy(() => import('reactflow').then((m) => ({ default: m.Controls })));
const Background = lazy(() => import('reactflow').then((m) => ({ default: m.Background })));
const MiniMap = lazy(() => import('reactflow').then((m) => ({ default: m.MiniMap })));

import 'reactflow/dist/style.css';
import type { NodeType, WorkflowNode } from '../types';
import { useWorkflowStore } from '../hooks/useWorkflow';

const nodeTypes = {
  agent: createCustomNode('agent', '智能体', '#f59e0b'),
  tool: createCustomNode('tool', '工具', '#3b82f6'),
  condition: createCustomNode('condition', '条件', '#f97316'),
  loop: createCustomNode('loop', '循环', '#a855f7'),
  subflow: createCustomNode('subflow', '子流程', '#14b8a6'),
  trigger: createCustomNode('trigger', '触发器', '#22c55e'),
};

function createCustomNode(type: string, label: string, color: string) {
  return function CustomNode({ data, selected }: { data: { label: string }; selected: boolean }) {
    return (
      <div
        className={`
          px-4 py-3 rounded-xl border-2 min-w-[140px]
          ${selected ? 'shadow-lg' : ''}
          bg-slate-800/80 backdrop-blur-sm
        `}
        style={{ borderColor: selected ? color : `${color}80` }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${color}20` }}
          >
            <span style={{ color }}>{label[0]}</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">{data.label}</p>
            <p className="text-xs text-slate-400">{label}节点</p>
          </div>
        </div>
      </div>
    );
  };
}

export function WorkflowCanvas() {
  const { nodes, edges, setNodes, setEdges, addEdge: addStoreEdge, setSelectedNodeId } = useWorkflowStore();

  const onConnect = useCallback(
    (connection: Connection) => {
      const newEdge: Edge = {
        id: `edge_${connection.source}_${connection.target}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
      };
      addStoreEdge(newEdge);
    },
    [addStoreEdge]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
    },
    [setSelectedNodeId]
  );

  const onNodesChange = useCallback(
    () => {
      setNodes(nodes);
    },
    [nodes, setNodes]
  );

  const onEdgesChange = useCallback(
    () => {
      setEdges(edges);
    },
    [edges, setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('nodeType') as NodeType;
      if (!type) return;

      const bounds = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - bounds.left;
      const y = event.clientY - bounds.top;

      const newNode: WorkflowNode = {
        id: `${type}_${Date.now()}`,
        type,
        position: { x, y },
        data: {
          label: type === 'agent' ? '智能体' : type === 'tool' ? '工具' : type === 'condition' ? '条件' : type === 'loop' ? '循环' : type === 'subflow' ? '子流程' : '触发器',
          config: {},
          inputs: {},
          outputs: {},
          errorHandling: 'fail',
        },
      };

      useWorkflowStore.getState().addNode(newNode);
    },
    []
  );

  return (
    <div
      className="flex-1 h-full"
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      <Suspense fallback={<div className="flex items-center justify-center h-full">加载中...</div>}>
        <ReactFlow
          nodes={nodes.map((n) => ({
            id: n.id,
            type: n.type,
            position: n.position,
            data: n.data,
          }))}
          edges={edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
            label: e.label,
          }))}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttributions: true }}
        >
          <Background color="#334155" gap={16} />
          <MiniMap
            nodeColor="#334155"
            maskColor="rgb(51, 65, 85)"
          />
          <Controls />
        </ReactFlow>
      </Suspense>
    </div>
  );
}

export default WorkflowCanvas;
