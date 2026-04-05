import { useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import type { LineageNode, LineageEdge, AssetType } from '../types';
import { ASSET_TYPE_CONFIG } from '../types';
import { useLineage } from '../hooks/useLineage';

export interface LineageGraphProps {
  assetId: string;
  height?: number;
  depth?: number;
  onNodeClick?: (nodeId: string) => void;
}

const nodeColors: Record<AssetType, string> = {
  datasource: '#3b82f6',
  dataset: '#22c55e',
  knowledgebase: '#f59e0b',
};

const convertToReactFlowNodes = (nodes: LineageNode[]): Node[] => {
  return nodes.map((node) => ({
    id: node.id,
    type: 'default',
    data: {
      label: (
        <div className="flex items-center gap-2 px-2 py-1">
          <span className="text-lg">
            {node.type === 'datasource' && '🗄️'}
            {node.type === 'dataset' && '📊'}
            {node.type === 'knowledgebase' && '📚'}
          </span>
          <span className="text-sm font-medium">{node.name}</span>
        </div>
      ),
    },
    position: { x: 0, y: 0 },
    style: {
      backgroundColor: '#1f2937',
      border: `2px solid ${nodeColors[node.type]}`,
      borderRadius: '8px',
      color: '#fff',
      fontSize: '12px',
    },
  }));
};

const convertToReactFlowEdges = (edges: LineageEdge[]): Edge[] => {
  return edges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#6b7280', strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#6b7280',
    },
  }));
};

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const levelMap = new Map<string, number>();
  const visited = new Set<string>();

  const calculateLevels = (nodeId: string, level: number) => {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);
    levelMap.set(nodeId, level);

    edges
      .filter((e) => e.source === nodeId)
      .forEach((e) => calculateLevels(e.target, level + 1));
  };

  const rootNodes = nodes.filter(
    (n) => !edges.some((e) => e.target === n.id)
  );
  rootNodes.forEach((n) => calculateLevels(n.id, 0));

  const levelGroups = new Map<number, Node[]>();
  nodes.forEach((node) => {
    const level = levelMap.get(node.id) ?? 0;
    if (!levelGroups.has(level)) {
      levelGroups.set(level, []);
    }
    levelGroups.get(level)!.push(node);
  });

  const nodeWidth = 180;
  const nodeHeight = 60;
  const horizontalGap = 100;
  const verticalGap = 50;

  levelGroups.forEach((levelNodes, level) => {
    levelNodes.forEach((node, index) => {
      node.position = {
        x: level * (nodeWidth + horizontalGap),
        y: index * (nodeHeight + verticalGap),
      };
    });
  });

  return { nodes, edges };
};

export function LineageGraph({
  assetId,
  height = 500,
  depth = 2,
  onNodeClick,
}: LineageGraphProps) {
  const { nodes: lineageNodes, edges: lineageEdges, isLoading } = useLineage({
    assetId,
    depth,
  });

  const initialNodes = useMemo(
    () => convertToReactFlowNodes(lineageNodes),
    [lineageNodes]
  );

  const initialEdges = useMemo(
    () => convertToReactFlowEdges(lineageEdges),
    [lineageEdges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useMemo(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges
    );
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-800/50 rounded-lg"
        style={{ height }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (lineageNodes.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-800/50 rounded-lg"
        style={{ height }}
      >
        <p className="text-gray-400">暂无血缘数据</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg overflow-hidden border border-white/10" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        attributionPosition="bottom-left"
        className="bg-gray-900"
      >
        <Background color="#374151" gap={20} />
        <Controls className="bg-gray-800 border border-white/10 rounded-lg" />
        <MiniMap
          className="bg-gray-800 border border-white/10 rounded-lg"
          nodeColor={(node) => {
            const lineageNode = lineageNodes.find((n) => n.id === node.id);
            return lineageNode ? nodeColors[lineageNode.type] : '#6b7280';
          }}
          maskColor="rgba(0, 0, 0, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
