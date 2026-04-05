import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';
import knowledgeGraphData from '../../data/knowledgeGraph.json';

interface GraphNode {
  id: string;
  label: string;
  type: 'userMemory' | 'businessData' | 'externalKnowledge';
  importance: number;
  summary: string;
  position: { x: number; y: number };
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  strength: number;
  label: string;
}

interface KnowledgeGraphProps {
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  isMining?: boolean;
  highlightedNodes?: string[];
}

const typeColors = {
  userMemory: theme.colors.memory.userMemory,
  businessData: theme.colors.memory.businessData,
  externalKnowledge: theme.colors.memory.externalKnowledge,
};

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  width = 600,
  height = 400,
  onNodeClick,
  isMining = false,
  highlightedNodes = [],
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [pulseNodes, setPulseNodes] = useState<Set<string>>(new Set());
  const animationRef = useRef<number>();
  const mousePos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const initializedNodes = knowledgeGraphData.nodes.map(node => ({
      ...node,
      x: node.position.x + width / 2 - 250,
      y: node.position.y + height / 2 - 150,
      vx: 0,
      vy: 0,
    }));
    setNodes(initializedNodes);
    setEdges(knowledgeGraphData.edges);
  }, [width, height]);

  useEffect(() => {
    if (isMining) {
      const miningInterval = setInterval(() => {
        const randomNodes = nodes
          .sort(() => Math.random() - 0.5)
          .slice(0, 2);
        
        randomNodes.forEach(node => {
          setPulseNodes(prev => new Set(prev).add(node.id));
          ParticleManager.createBurst('probe', node.x || 0, node.y || 0, 5);
        });
        
        SoundEffects.playMiningSuccess();
        
        setTimeout(() => {
          setPulseNodes(prev => {
            const next = new Set(prev);
            randomNodes.forEach(n => next.delete(n.id));
            return next;
          });
        }, 1000);
      }, 2000);
      
      return () => clearInterval(miningInterval);
    }
  }, [isMining, nodes]);

  const applyForces = useCallback(() => {
    const centerX = width / 2;
    const centerY = height / 2;
    
    setNodes(prevNodes => {
      const newNodes = prevNodes.map(node => {
        let fx = 0, fy = 0;
        
        fx += (centerX - (node.x || 0)) * 0.01;
        fy += (centerY - (node.y || 0)) * 0.01;
        
        prevNodes.forEach(other => {
          if (other.id === node.id) return;
          
          const dx = (node.x || 0) - (other.x || 0);
          const dy = (node.y || 0) - (other.y || 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          
          if (dist < 100) {
            fx += (dx / dist) * (100 - dist) * 0.05;
            fy += (dy / dist) * (100 - dist) * 0.05;
          }
        });
        
        edges.forEach(edge => {
          if (edge.source === node.id || edge.target === node.id) {
            const otherId = edge.source === node.id ? edge.target : edge.source;
            const other = prevNodes.find(n => n.id === otherId);
            
            if (other) {
              const dx = (other.x || 0) - (node.x || 0);
              const dy = (other.y || 0) - (node.y || 0);
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const targetDist = 150;
              
              fx += (dx / dist) * (dist - targetDist) * 0.02 * edge.strength;
              fy += (dy / dist) * (dist - targetDist) * 0.02 * edge.strength;
            }
          }
        });
        
        const vx = ((node.vx || 0) + fx) * 0.8;
        const vy = ((node.vy || 0) + fy) * 0.8;
        
        return {
          ...node,
          x: (node.x || 0) + vx,
          y: (node.y || 0) + vy,
          vx,
          vy,
        };
      });
      
      return newNodes;
    });
  }, [edges, width, height]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, width, height);
    
    edges.forEach(edge => {
      const source = nodes.find(n => n.id === edge.source);
      const target = nodes.find(n => n.id === edge.target);
      
      if (source && target && source.x !== undefined && source.y !== undefined && target.x !== undefined && target.y !== undefined) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(212, 175, 55, ${edge.strength * 0.5})`;
        ctx.lineWidth = edge.strength * 3;
        ctx.stroke();
        
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        ctx.fillStyle = 'rgba(212, 175, 55, 0.6)';
        ctx.font = '10px sans-serif';
        ctx.fillText(edge.label, midX, midY);
      }
    });
    
    nodes.forEach(node => {
      if (node.x === undefined || node.y === undefined) return;
      
      const isHovered = hoveredNode?.id === node.id;
      const isSelected = selectedNode?.id === node.id;
      const isPulsing = pulseNodes.has(node.id);
      const isHighlighted = highlightedNodes.includes(node.id);
      
      const baseRadius = 20 + node.importance * 15;
      const radius = isHovered ? baseRadius * 1.2 : baseRadius;
      
      if (isPulsing || isHighlighted) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + 10, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(212, 175, 55, ${0.3 + Math.sin(Date.now() / 200) * 0.2})`;
        ctx.fill();
      }
      
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
      
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, radius
      );
      gradient.addColorStop(0, typeColors[node.type]);
      gradient.addColorStop(1, `${typeColors[node.type]}80`);
      
      ctx.fillStyle = gradient;
      ctx.fill();
      
      if (isHovered || isSelected) {
        ctx.strokeStyle = theme.colors.primary.gold;
        ctx.lineWidth = 3;
        ctx.stroke();
      }
      
      ctx.fillStyle = '#fff';
      ctx.font = `${isHovered ? 14 : 12}px "Microsoft YaHei", sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, node.x, node.y);
    });
    
    animationRef.current = requestAnimationFrame(() => {
      applyForces();
      draw();
    });
  }, [nodes, edges, hoveredNode, selectedNode, pulseNodes, highlightedNodes, width, height, applyForces]);

  useEffect(() => {
    draw();
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [draw]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    mousePos.current = { x, y };
    
    const hovered = nodes.find(node => {
      if (node.x === undefined || node.y === undefined) return false;
      const dx = x - node.x;
      const dy = y - node.y;
      const radius = 20 + node.importance * 15;
      return dx * dx + dy * dy < radius * radius;
    });
    
    setHoveredNode(hovered || null);
    canvas.style.cursor = hovered ? 'pointer' : 'default';
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (hoveredNode) {
      setSelectedNode(hoveredNode);
      SoundEffects.playTone(600, 0.1);
      ParticleManager.createBurst('memory', hoveredNode.x || 0, hoveredNode.y || 0, 10);
      onNodeClick?.(hoveredNode);
    }
  };

  return (
    <div style={{ ...styles.container, width, height }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        style={styles.canvas}
      />
      
      <AnimatePresence>
        {hoveredNode && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            style={{
              ...styles.tooltip,
              left: mousePos.current.x + 15,
              top: mousePos.current.y + 15,
            }}
          >
            <div style={styles.tooltipTitle}>{hoveredNode.label}</div>
            <div style={styles.tooltipSummary}>{hoveredNode.summary}</div>
            <div style={styles.tooltipMeta}>
              <span style={{ color: typeColors[hoveredNode.type] }}>
                {hoveredNode.type === 'userMemory' ? '用户记忆' : 
                 hoveredNode.type === 'businessData' ? '业务数据' : '外部知识'}
              </span>
              <span>重要度: {Math.round(hoveredNode.importance * 100)}%</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: typeColors.userMemory }} />
          <span>用户记忆</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: typeColors.businessData }} />
          <span>业务数据</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: typeColors.externalKnowledge }} />
          <span>外部知识</span>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
    background: 'rgba(10, 35, 66, 0.9)',
    borderRadius: theme.borderRadius.xl,
    border: `1px solid ${theme.colors.primary.gold}40`,
    overflow: 'hidden',
  },
  canvas: {
    display: 'block',
  },
  tooltip: {
    position: 'absolute',
    padding: '12px 16px',
    background: 'rgba(10, 35, 66, 0.95)',
    borderRadius: theme.borderRadius.lg,
    border: `1px solid ${theme.colors.primary.gold}60`,
    boxShadow: theme.shadows.lg,
    pointerEvents: 'none',
    maxWidth: '200px',
    zIndex: 100,
  },
  tooltipTitle: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.base,
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  tooltipSummary: {
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
    marginBottom: '8px',
  },
  tooltipMeta: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.primary.goldLight,
  },
  legend: {
    position: 'absolute',
    bottom: '10px',
    right: '10px',
    display: 'flex',
    gap: '12px',
    padding: '8px 12px',
    background: 'rgba(0, 0, 0, 0.5)',
    borderRadius: theme.borderRadius.md,
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    color: '#fff',
    fontSize: theme.typography.fontSize.xs,
  },
  legendDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
};

export default KnowledgeGraph;
