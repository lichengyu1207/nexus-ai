import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import type { FlameGraphNode } from '../types';

interface FlameGraphProps {
  data: FlameGraphNode | null;
  onNodeClick?: (node: FlameGraphNode) => void;
  width?: number;
  height?: number;
}

const FlameGraphRect = ({
  node,
  x,
  y,
  width,
  depth,
  maxDepth,
  totalTime,
  onNodeClick,
  selectedNode,
}: {
  node: FlameGraphNode;
  x: number;
  y: number;
  width: number;
  depth: number;
  maxDepth: number;
  totalTime: number;
  onNodeClick?: (node: FlameGraphNode) => void;
  selectedNode?: FlameGraphNode;
}) => {
  const isSelected = selectedNode?.name === node.name;
  const hasChildren = node.children && node.children.length > 0;
  const nodeHeight = 25;
  const padding = 2;

  const childWidths = hasChildren
    ? node.children!.reduce((sum, child) => sum + child.value, 0)
    : 0;

  const renderChildren = () => {
    if (!hasChildren) return null;

    let currentX = x;
    return node.children!.map((child) => {
      const childWidth = (child.value / totalTime) * width;
      const rect = (
        <FlameGraphRect
          key={child.name}
          node={child}
          x={currentX}
          y={y + nodeHeight + padding}
          width={childWidth}
          depth={depth + 1}
          maxDepth={maxDepth}
          totalTime={totalTime}
          onNodeClick={onNodeClick}
          selectedNode={selectedNode}
        />
      );
      currentX += childWidth;
      return rect;
    });
  };

  const getHeatColor = (value: number, max: number) => {
    const ratio = value / max;
    if (ratio > 0.8) return 'bg-red-500/80 hover:bg-red-500';
    if (ratio > 0.6) return 'bg-orange-500/80 hover:bg-orange-500';
    if (ratio > 0.4) return 'bg-amber-500/80 hover:bg-amber-500';
    if (ratio > 0.2) return 'bg-yellow-500/80 hover:bg-yellow-500';
    return 'bg-green-500/80 hover:bg-green-500';
  };

  return (
    <>
      <motion.rect
        x={x}
        y={y}
        width={width - padding}
        height={nodeHeight}
        rx={4}
        className={`${getHeatColor(node.value, totalTime)} cursor-pointer transition-colors ${isSelected ? 'ring-2 ring-white' : ''}`}
        onClick={() => onNodeClick?.(node)}
        whileHover={{ opacity: 0.8 }}
      />
      {width > 50 && (
        <text
          x={x + 4}
          y={y + 16}
          className="text-xs fill-white truncate"
          style={{ maxWidth: width - 8 }}
        >
          {node.name.slice(0, Math.floor(width / 8))}
        </text>
      )}
      {depth < maxDepth && renderChildren()}
    </>
  );
};

export function FlameGraph({
  data,
  onNodeClick,
  width = 800,
  height = 400,
}: FlameGraphProps) {
  const [selectedNode, setSelectedNode] = useState<FlameGraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<FlameGraphNode | null>(null);

  const maxDepth = useMemo(() => {
    const getDepth = (node: FlameGraphNode, depth: number): number => {
      if (!node.children || node.children.length === 0) return depth;
      return Math.max(...node.children.map((c) => getDepth(c, depth + 1)));
    };
    return data ? getDepth(data, 0) : 0;
  }, [data]);

  const totalTime = data?.value || 0;

  const handleNodeClick = (node: FlameGraphNode) => {
    setSelectedNode(node);
    onNodeClick?.(node);
  };

  if (!data) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        暂无性能数据
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-900/50">
      <div className="absolute top-2 right-2 z-10 flex items-center gap-2">
        {hoveredNode && (
          <div className="px-2 py-1 bg-slate-800/90 rounded text-xs text-slate-300">
            {hoveredNode.name}: {hoveredNode.value.toFixed(2)}ms
          </div>
        )}
      </div>
      <svg width={width} height={height} className="w-full h-full">
        <FlameGraphRect
          node={data}
          x={0}
          y={0}
          width={width}
          depth={0}
          maxDepth={maxDepth}
          totalTime={totalTime}
          onNodeClick={handleNodeClick}
          selectedNode={selectedNode}
        />
      </svg>
    </div>
  );
}
