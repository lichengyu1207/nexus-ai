import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import memoryApi, { MemoryGraph as MemoryGraphType, MemoryGraphNode, MemoryGraphEdge, Memory } from '../../api/memory';

interface MemoryGraphVisualizationProps {
  taskId?: string;
  onNodeSelect?: (memory: Memory) => void;
  onNodeActivate?: (nodeId: string) => void;
  isActive?: boolean;
  compact?: boolean;
  width?: number;
  height?: number;
}

const TYPE_COLORS: Record<string, string> = {
  event: '#3B82F6',
  fact: '#10B981',
  procedure: '#F59E0B',
  insight: '#8B5CF6',
};

const MemoryGraphVisualization: React.FC<MemoryGraphVisualizationProps> = ({
  taskId,
  onNodeSelect,
  onNodeActivate,
  isActive = false,
  compact = false,
  width,
  height,
}) => {
  const [graph, setGraph] = useState<MemoryGraphType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<MemoryGraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [pulseNodes, setPulseNodes] = useState<Set<string>>(new Set());

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number | null>(null);
  const nodesRef = useRef<Array<{ id: string; x: number; y: number; vx: number; vy: number; node: MemoryGraphNode }>>([]);

  const dimensions = useMemo(() => ({
    width: width || (compact ? 400 : 600),
    height: height || (compact ? 300 : 400),
  }), [width, height, compact]);

  const fetchGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const graphData = await memoryApi.getMemoryGraph({
        maxNodes: compact ? 30 : 50,
      });

      setGraph(graphData);

      const centerX = dimensions.width / 2;
      const centerY = dimensions.height / 2;

      nodesRef.current = graphData.nodes.map((node, index) => {
        const angle = (index / graphData.nodes.length) * Math.PI * 2;
        const radius = 100 + Math.random() * 100;

        return {
          id: node.id,
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
          node,
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载图谱失败');
    } finally {
      setIsLoading(false);
    }
  }, [dimensions, compact]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !graph) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    const simulate = () => {
      const k = 0.01;
      const repulsion = 5000;
      const damping = 0.9;

      nodesRef.current.forEach((n1, i) => {
        let fx = 0;
        let fy = 0;

        const dx = centerX - n1.x;
        const dy = centerY - n1.y;
        fx += dx * k;
        fy += dy * k;

        nodesRef.current.forEach((n2, j) => {
          if (i === j) return;

          const ddx = n1.x - n2.x;
          const ddy = n1.y - n2.y;
          const dist = Math.sqrt(ddx * ddx + ddy * ddy) || 1;
          const force = repulsion / (dist * dist);

          fx += (ddx / dist) * force;
          fy += (ddy / dist) * force;
        });

        n1.vx = (n1.vx + fx) * damping;
        n1.vy = (n1.vy + fy) * damping;

        n1.x += n1.vx;
        n1.y += n1.vy;

        const margin = 30;
        n1.x = Math.max(margin, Math.min(dimensions.width - margin, n1.x));
        n1.y = Math.max(margin, Math.min(dimensions.height - margin, n1.y));
      });

      ctx.clearRect(0, 0, dimensions.width, dimensions.height);

      graph.edges.forEach((edge) => {
        const fromNode = nodesRef.current.find((n) => n.id === edge.from);
        const toNode = nodesRef.current.find((n) => n.id === edge.to);

        if (!fromNode || !toNode) return;

        const isActive = activeNodes.has(edge.from) || activeNodes.has(edge.to);

        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);

        const gradient = ctx.createLinearGradient(fromNode.x, fromNode.y, toNode.x, toNode.y);
        const fromColor = TYPE_COLORS[fromNode.node.type] || '#666';
        const toColor = TYPE_COLORS[toNode.node.type] || '#666';

        gradient.addColorStop(0, isActive ? fromColor : `${fromColor}40`);
        gradient.addColorStop(1, isActive ? toColor : `${toColor}40`);

        ctx.strokeStyle = gradient;
        ctx.lineWidth = isActive ? edge.strength * 3 : edge.strength;
        ctx.stroke();
      });

      nodesRef.current.forEach(({ id, x, y, node }) => {
        const isSelected = selectedNode?.id === id;
        const isHovered = hoveredNode === id;
        const isActiveNode = activeNodes.has(id);
        const isPulsing = pulseNodes.has(id);

        const baseRadius = 8 + node.importance;
        let radius = baseRadius;

        if (isSelected || isHovered) {
          radius = baseRadius * 1.3;
        }

        if (isPulsing && animationRef.current) {
          const time = Date.now() / 1000;
          radius = baseRadius * (1 + 0.3 * Math.sin(time * 5));
        }

        const color = TYPE_COLORS[node.type] || '#666';

        if (isActiveNode || isPulsing) {
          ctx.beginPath();
          ctx.arc(x, y, radius + 10, 0, Math.PI * 2);
          ctx.fillStyle = `${color}30`;
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);

        const gradient = ctx.createRadialGradient(x - radius / 3, y - radius / 3, 0, x, y, radius);
        gradient.addColorStop(0, `${color}ff`);
        gradient.addColorStop(1, `${color}aa`);

        ctx.fillStyle = gradient;
        ctx.fill();

        if (isSelected || isHovered) {
          ctx.strokeStyle = '#fff';
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        if (!compact && (isHovered || isSelected)) {
          ctx.font = '11px sans-serif';
          ctx.fillStyle = '#fff';
          ctx.textAlign = 'center';
          ctx.fillText(node.label.substring(0, 15), x, y + radius + 14);
        }
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    simulate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [graph, selectedNode, hoveredNode, activeNodes, pulseNodes, dimensions, compact]);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const clickedNode = nodesRef.current.find(({ x: nx, y: ny, node }) => {
      const radius = 8 + node.importance;
      const dist = Math.sqrt((x - nx) ** 2 + (y - ny) ** 2);
      return dist <= radius * 1.5;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode.node);
      memoryApi.getMemory(clickedNode.id).then((memory) => {
        onNodeSelect?.(memory);
      });
    } else {
      setSelectedNode(null);
    }
  }, [onNodeSelect]);

  const handleCanvasDoubleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const clickedNode = nodesRef.current.find(({ x: nx, y: ny, node }) => {
      const radius = 8 + node.importance;
      const dist = Math.sqrt((x - nx) ** 2 + (y - ny) ** 2);
      return dist <= radius * 1.5;
    });

    if (clickedNode) {
      const connectedNodes = new Set<string>();
      connectedNodes.add(clickedNode.id);

      graph?.edges.forEach((edge) => {
        if (edge.from === clickedNode.id) connectedNodes.add(edge.to);
        if (edge.to === clickedNode.id) connectedNodes.add(edge.from);
      });

      setActiveNodes(connectedNodes);
      setPulseNodes(new Set([clickedNode.id]));

      onNodeActivate?.(clickedNode.id);

      setTimeout(() => {
        setPulseNodes(new Set());
      }, 2000);
    }
  }, [graph, onNodeActivate]);

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const hoveredNodeData = nodesRef.current.find(({ x: nx, y: ny, node }) => {
      const radius = 8 + node.importance;
      const dist = Math.sqrt((x - nx) ** 2 + (y - ny) ** 2);
      return dist <= radius * 1.5;
    });

    setHoveredNode(hoveredNodeData?.id || null);
  }, []);

  if (isLoading) {
    return (
      <div style={{
        width: dimensions.width,
        height: dimensions.height,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '12px',
      }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: '32px',
            height: '32px',
            border: '3px solid rgba(139, 92, 246, 0.2)',
            borderTopColor: '#8B5CF6',
            borderRadius: '50%',
            marginBottom: '12px',
          }}
        />
        <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '13px' }}>
          加载记忆图谱...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        width: dimensions.width,
        height: dimensions.height,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(239, 68, 68, 0.1)',
        borderRadius: '12px',
      }}>
        <span style={{ fontSize: '32px', marginBottom: '8px' }}>⚠️</span>
        <span style={{ color: '#ef4444', fontSize: '14px' }}>{error}</span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        overflow: 'hidden',
      }}
    >
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(0, 0, 0, 0.2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🕸️</span>
          <h3 style={{ color: '#8B5CF6', fontSize: '14px', fontWeight: 600, margin: 0 }}>
            记忆关联图谱
          </h3>
          {graph?.stats && (
            <span style={{
              padding: '2px 8px',
              background: 'rgba(139, 92, 246, 0.2)',
              borderRadius: '10px',
              color: '#8B5CF6',
              fontSize: '11px',
            }}>
              {graph.stats.totalNodes} 节点 · {graph.stats.totalEdges} 连接
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: color,
              }} />
              <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '10px' }}>
                {type}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ position: 'relative' }}>
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          onDoubleClick={handleCanvasDoubleClick}
          onMouseMove={handleCanvasMouseMove}
          style={{
            width: dimensions.width,
            height: dimensions.height,
            cursor: hoveredNode ? 'pointer' : 'default',
          }}
        />

        <AnimatePresence>
          {hoveredNode && !compact && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '12px',
                padding: '8px 12px',
                background: 'rgba(0, 0, 0, 0.8)',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '11px' }}>
                                双击节点激活关联 · 拖拽移动
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default MemoryGraphVisualization;
