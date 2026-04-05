/**
 * 记忆网络图组件
 * Memory Graph Component
 * 
 * 使用力导向图展示记忆节点和关联关系
 */

import React, { useState, useEffect, useRef, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type MemoryType = 'episodic' | 'semantic' | 'attack_pattern' | 'defense_pattern' | 'user_profile';

export interface MemoryNode {
  id: string;
  label: string;
  type: MemoryType;
  summary: string;
  importance: number;
  createdAt: Date;
  accessCount: number;
}

export interface MemoryEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  relationType: string;
}

export interface MemoryGraphData {
  nodes: MemoryNode[];
  edges: MemoryEdge[];
}

export interface MemoryGraphProps {
  data: MemoryGraphData;
  onNodeClick?: (node: MemoryNode) => void;
  onNodeDrag?: (nodeId: string, x: number, y: number) => void;
  width?: number;
  height?: number;
  className?: string;
}

interface NodePosition {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fixed: boolean;
}

const typeColors: Record<MemoryType, { bg: string; border: string; text: string }> = {
  episodic: { bg: '#DBEAFE', border: '#3B82F6', text: '#1E40AF' },
  semantic: { bg: '#D1FAE5', border: '#10B981', text: '#065F46' },
  attack_pattern: { bg: '#FEE2E2', border: '#EF4444', text: '#991B1B' },
  defense_pattern: { bg: '#E0E7FF', border: '#6366F1', text: '#3730A3' },
  user_profile: { bg: '#FEF3C7', border: '#F59E0B', text: '#92400E' },
};

const typeLabels: Record<MemoryType, string> = {
  episodic: '情景记忆',
  semantic: '语义记忆',
  attack_pattern: '攻击模式',
  defense_pattern: '防御模式',
  user_profile: '用户画像',
};

const MemoryNodeComponent: React.FC<{
  node: MemoryNode;
  position: NodePosition;
  isSelected: boolean;
  isHighlighted: boolean;
  onMouseDown: (e: React.MouseEvent) => void;
  onClick: () => void;
}> = memo(({ node, position, isSelected, isHighlighted, onMouseDown, onClick }) => {
  const colors = typeColors[node.type];
  const size = 30 + node.importance * 20;
  
  return (
    <motion.g
      style={{ 
        transform: `translate(${position.x}px, ${position.y}px)`,
        cursor: 'grab',
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ 
        scale: isHighlighted ? 1.2 : 1, 
        opacity: 1 
      }}
      whileHover={{ scale: 1.1 }}
      onMouseDown={onMouseDown}
      onClick={onClick}
    >
      <motion.circle
        r={size}
        fill={colors.bg}
        stroke={isSelected ? '#000' : colors.border}
        strokeWidth={isSelected ? 3 : 2}
        animate={{
          boxShadow: isHighlighted 
            ? ['0 0 0 0 rgba(59, 130, 246, 0.4)', '0 0 0 20px rgba(59, 130, 246, 0)']
            : '0 0 0 0 rgba(0, 0, 0, 0)',
        }}
        transition={{ duration: 1, repeat: isHighlighted ? Infinity : 0 }}
        style={{
          filter: isHighlighted ? 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.5))' : 'none',
        }}
      />
      
      <text
        textAnchor="middle"
        dy=".3em"
        fontSize={Math.max(10, size * 0.4)}
        fill={colors.text}
        fontWeight="500"
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        {node.label.slice(0, 4)}
      </text>
      
      {node.importance > 0.7 && (
        <motion.circle
          r={size + 5}
          fill="none"
          stroke={colors.border}
          strokeWidth="1"
          strokeDasharray="4 4"
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          style={{ opacity: 0.3 }}
        />
      )}
    </motion.g>
  );
});

MemoryNodeComponent.displayName = 'MemoryNodeComponent';

const MemoryEdgeComponent: React.FC<{
  edge: MemoryEdge;
  sourcePos: NodePosition;
  targetPos: NodePosition;
  isHighlighted: boolean;
}> = memo(({ edge, sourcePos, targetPos, isHighlighted }) => (
  <motion.line
    x1={sourcePos.x}
    y1={sourcePos.y}
    x2={targetPos.x}
    y2={targetPos.y}
    stroke={isHighlighted ? '#3B82F6' : '#CBD5E1'}
    strokeWidth={isHighlighted ? 3 : 1 + edge.weight}
    strokeOpacity={isHighlighted ? 1 : 0.5}
    initial={{ pathLength: 0, opacity: 0 }}
    animate={{ pathLength: 1, opacity: 1 }}
    transition={{ duration: 0.5 }}
  />
));

MemoryEdgeComponent.displayName = 'MemoryEdgeComponent';

const NodeDetailModal: React.FC<{
  node: MemoryNode;
  position: { x: number; y: number };
  onClose: () => void;
}> = memo(({ node, position, onClose }) => {
  const colors = typeColors[node.type];
  
  return (
    <motion.div
      className="absolute z-50 bg-white rounded-xl shadow-2xl p-4 w-72"
      style={{
        left: Math.min(position.x + 50, window.innerWidth - 300),
        top: Math.min(position.y - 50, window.innerHeight - 250),
      }}
      initial={{ opacity: 0, scale: 0.9, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: colors.border }}
          />
          <span className="text-xs text-gray-500">{typeLabels[node.type]}</span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500"
        >
          ✕
        </button>
      </div>
      
      <h3 className="font-bold text-gray-800 mb-2">{node.label}</h3>
      <p className="text-sm text-gray-600 mb-3">{node.summary}</p>
      
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">重要性</span>
          <div className="flex items-center gap-1 mt-1">
            <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: colors.border }}
                initial={{ width: 0 }}
                animate={{ width: `${node.importance * 100}%` }}
              />
            </div>
            <span className="text-gray-700">{(node.importance * 100).toFixed(0)}%</span>
          </div>
        </div>
        
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">访问次数</span>
          <div className="text-gray-700 font-medium mt-1">{node.accessCount}</div>
        </div>
      </div>
      
      <div className="mt-3 text-xs text-gray-400">
        创建于 {node.createdAt.toLocaleString()}
      </div>
    </motion.div>
  );
});

NodeDetailModal.displayName = 'NodeDetailModal';

const MemoryGraph: React.FC<MemoryGraphProps> = memo(({
  data,
  onNodeClick,
  onNodeDrag,
  width = 800,
  height = 600,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodePositions, setNodePositions] = useState<Record<string, NodePosition>>({});
  const [selectedNode, setSelectedNode] = useState<MemoryNode | null>(null);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const positions: Record<string, NodePosition> = {};
    const centerX = width / 2;
    const centerY = height / 2;
    
    data.nodes.forEach((node, index) => {
      const angle = (index / data.nodes.length) * 2 * Math.PI;
      const radius = 150 + Math.random() * 100;
      positions[node.id] = {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        fixed: false,
      };
    });
    
    setNodePositions(positions);
  }, [data.nodes, width, height]);

  useEffect(() => {
    const simulate = () => {
      setNodePositions(prev => {
        const newPositions = { ...prev };
        const nodes = Object.keys(newPositions);
        const alpha = 0.1;
        const repulsion = 5000;
        const attraction = 0.01;
        const damping = 0.9;
        
        nodes.forEach(id1 => {
          if (newPositions[id1].fixed) return;
          
          let fx = 0, fy = 0;
          
          nodes.forEach(id2 => {
            if (id1 === id2) return;
            
            const p1 = newPositions[id1];
            const p2 = newPositions[id2];
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            fx += (dx / dist) * repulsion / (dist * dist);
            fy += (dy / dist) * repulsion / (dist * dist);
          });
          
          data.edges.forEach(edge => {
            let otherId: string | null = null;
            if (edge.source === id1) otherId = edge.target;
            else if (edge.target === id1) otherId = edge.source;
            
            if (otherId && newPositions[otherId]) {
              const p1 = newPositions[id1];
              const p2 = newPositions[otherId];
              const dx = p2.x - p1.x;
              const dy = p2.y - p1.y;
              fx += dx * attraction;
              fy += dy * attraction;
            }
          });
          
          const centerX = width / 2;
          const centerY = height / 2;
          fx += (centerX - newPositions[id1].x) * 0.001;
          fy += (centerY - newPositions[id1].y) * 0.001;
          
          newPositions[id1] = {
            ...newPositions[id1],
            vx: (newPositions[id1].vx + fx * alpha) * damping,
            vy: (newPositions[id1].vy + fy * alpha) * damping,
            x: Math.max(50, Math.min(width - 50, newPositions[id1].x + newPositions[id1].vx)),
            y: Math.max(50, Math.min(height - 50, newPositions[id1].y + newPositions[id1].vy)),
          };
        });
        
        return newPositions;
      });
      
      animationRef.current = requestAnimationFrame(simulate);
    };
    
    animationRef.current = requestAnimationFrame(simulate);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [data.edges, width, height]);

  const handleNodeMouseDown = useCallback((nodeId: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setDraggingNode(nodeId);
    setNodePositions(prev => ({
      ...prev,
      [nodeId]: { ...prev[nodeId], fixed: true },
    }));
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!draggingNode || !svgRef.current) return;
    
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setNodePositions(prev => ({
      ...prev,
      [draggingNode]: { ...prev[draggingNode], x, y },
    }));
    
    onNodeDrag?.(draggingNode, x, y);
  }, [draggingNode, onNodeDrag]);

  const handleMouseUp = useCallback(() => {
    if (draggingNode) {
      setNodePositions(prev => ({
        ...prev,
        [draggingNode]: { ...prev[draggingNode], fixed: false },
      }));
      setDraggingNode(null);
    }
  }, [draggingNode]);

  const handleNodeClick = useCallback((node: MemoryNode) => {
    setSelectedNode(node);
    
    const relatedNodes = new Set<string>();
    relatedNodes.add(node.id);
    data.edges.forEach(edge => {
      if (edge.source === node.id) relatedNodes.add(edge.target);
      if (edge.target === node.id) relatedNodes.add(edge.source);
    });
    setHighlightedNodes(relatedNodes);
    
    onNodeClick?.(node);
  }, [data.edges, onNodeClick]);

  const handleCloseDetail = useCallback(() => {
    setSelectedNode(null);
    setHighlightedNodes(new Set());
  }, []);

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        <g className="edges">
          {data.edges.map(edge => {
            const sourcePos = nodePositions[edge.source];
            const targetPos = nodePositions[edge.target];
            if (!sourcePos || !targetPos) return null;
            
            return (
              <MemoryEdgeComponent
                key={edge.id}
                edge={edge}
                sourcePos={sourcePos}
                targetPos={targetPos}
                isHighlighted={highlightedNodes.has(edge.source) && highlightedNodes.has(edge.target)}
              />
            );
          })}
        </g>
        
        <g className="nodes">
          {data.nodes.map(node => {
            const position = nodePositions[node.id];
            if (!position) return null;
            
            return (
              <MemoryNodeComponent
                key={node.id}
                node={node}
                position={position}
                isSelected={selectedNode?.id === node.id}
                isHighlighted={highlightedNodes.has(node.id)}
                onMouseDown={handleNodeMouseDown(node.id)}
                onClick={() => handleNodeClick(node)}
              />
            );
          })}
        </g>
      </svg>
      
      <AnimatePresence>
        {selectedNode && nodePositions[selectedNode.id] && (
          <NodeDetailModal
            node={selectedNode}
            position={{
              x: nodePositions[selectedNode.id].x,
              y: nodePositions[selectedNode.id].y,
            }}
            onClose={handleCloseDetail}
          />
        )}
      </AnimatePresence>
      
      <div className="absolute bottom-4 left-4 flex gap-2 flex-wrap">
        {Object.entries(typeLabels).map(([type, label]) => (
          <div key={type} className="flex items-center gap-1 text-xs">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: typeColors[type as MemoryType].border }}
            />
            <span className="text-gray-600">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
});

MemoryGraph.displayName = 'MemoryGraph';

export default MemoryGraph;
