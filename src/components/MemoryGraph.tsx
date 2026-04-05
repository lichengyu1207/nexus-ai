import React, { useEffect, useRef, useState, useCallback } from 'react';
import { motion } from 'framer-motion';

interface GraphNode {
  id: string;
  label: string;
  category: string;
  importance: number;
  created_at?: string;
  x?: number;
  y?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

interface MemoryGraphProps {
  data: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  onNodeClick?: (node: GraphNode) => void;
  width?: number;
  height?: number;
}

const categoryColors: Record<string, string> = {
  fact: '#3b82f6',
  preference: '#22c55e',
  event: '#eab308',
  session_summary: '#a855f7',
  agent: '#f97316',
  default: '#6b7280',
};

const MemoryGraph: React.FC<MemoryGraphProps> = ({
  data,
  onNodeClick,
  width = 800,
  height = 600,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [draggingNode, setDraggingNode] = useState<GraphNode | null>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);

  useEffect(() => {
    if (!data.nodes.length) return;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;

    const initializedNodes = data.nodes.map((node, index) => {
      const angle = (2 * Math.PI * index) / data.nodes.length;
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    setNodes(initializedNodes);
  }, [data, width, height]);

  const getNodeRadius = useCallback((importance: number) => {
    return Math.max(15, importance * 2) * scale;
  }, [scale]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);
    ctx.save();
    ctx.translate(offset.x, offset.y);
    ctx.scale(scale, scale);

    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.6;

    data.edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      if (sourceNode && targetNode && sourceNode.x && sourceNode.y && targetNode.x && targetNode.y) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x, sourceNode.y);
        ctx.lineTo(targetNode.x, targetNode.y);
        ctx.stroke();
      }
    });

    ctx.globalAlpha = 1;

    nodes.forEach(node => {
      if (!node.x || !node.y) return;

      const radius = getNodeRadius(node.importance);
      const color = categoryColors[node.category] || categoryColors.default;

      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.globalAlpha = hoveredNode?.id === node.id ? 1 : 0.85;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.globalAlpha = 1;
      ctx.fillStyle = '#374151';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      const label = node.label.length > 12 ? node.label.slice(0, 12) + '...' : node.label;
      ctx.fillText(label, node.x, node.y + radius + 15);
    });

    ctx.restore();
  }, [nodes, data.edges, width, height, offset, scale, hoveredNode, getNodeRadius]);

  useEffect(() => {
    draw();
  }, [draw]);

  const getMousePos = useCallback((e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - offset.x) / scale,
      y: (e.clientY - rect.top - offset.y) / scale,
    };
  }, [offset, scale]);

  const findNodeAtPosition = useCallback((x: number, y: number) => {
    for (const node of nodes) {
      if (!node.x || !node.y) continue;
      const radius = getNodeRadius(node.importance);
      const dx = x - node.x;
      const dy = y - node.y;
      if (dx * dx + dy * dy <= radius * radius) {
        return node;
      }
    }
    return null;
  }, [nodes, getNodeRadius]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const pos = getMousePos(e);
    const node = findNodeAtPosition(pos.x, pos.y);
    setHoveredNode(node);

    if (draggingNode && draggingNode.x !== undefined && draggingNode.y !== undefined) {
      setNodes(prev => prev.map(n => 
        n.id === draggingNode.id 
          ? { ...n, x: pos.x, y: pos.y }
          : n
      ));
    }
  }, [getMousePos, findNodeAtPosition, draggingNode]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const pos = getMousePos(e);
    const node = findNodeAtPosition(pos.x, pos.y);
    if (node) {
      setDraggingNode(node);
    }
  }, [getMousePos, findNodeAtPosition]);

  const handleMouseUp = useCallback(() => {
    setDraggingNode(null);
  }, []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    const pos = getMousePos(e);
    const node = findNodeAtPosition(pos.x, pos.y);
    if (node) {
      setSelectedNode(node);
      onNodeClick?.(node);
    }
  }, [getMousePos, findNodeAtPosition, onNodeClick]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale(prev => Math.min(4, Math.max(0.1, prev * delta)));
  }, []);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="bg-gray-50 rounded-lg border border-gray-200 cursor-move"
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
        onWheel={handleWheel}
      />

      {hoveredNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-3 pointer-events-none z-10"
        >
          <p className="font-medium text-gray-900">{hoveredNode.label}</p>
          <p className="text-sm text-gray-500 mt-1">
            类别: {hoveredNode.category}
          </p>
          <p className="text-sm text-gray-500">
            重要度: {hoveredNode.importance.toFixed(1)}
          </p>
        </motion.div>
      )}

      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-10 max-w-xs"
        >
          <div className="flex items-start justify-between">
            <h3 className="font-medium text-gray-900">{selectedNode.label}</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="mt-2 space-y-1 text-sm text-gray-600">
            <p>类别: <span className="font-medium">{selectedNode.category}</span></p>
            <p>重要度: <span className="font-medium">{selectedNode.importance.toFixed(1)}</span></p>
            {selectedNode.created_at && (
              <p>创建时间: {new Date(selectedNode.created_at).toLocaleString('zh-CN')}</p>
            )}
          </div>
        </motion.div>
      )}

      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow p-2 z-10">
        <p className="text-xs text-gray-500 mb-2">图例</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(categoryColors).map(([cat, color]) => (
            <div key={cat} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-600">{cat}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="absolute top-4 right-4 bg-white rounded-lg shadow p-2 z-10">
        <p className="text-xs text-gray-500">缩放: {(scale * 100).toFixed(0)}%</p>
      </div>
    </div>
  );
};

export default MemoryGraph;
