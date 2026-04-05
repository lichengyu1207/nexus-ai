import React, { useCallback, useMemo, Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { Memory, GraphNode, GraphLink, MemoryType } from '../types';

const ForceGraph2D = lazy(() =>
  import('react-force-graph').then((m) => ({ default: m.ForceGraph2D }))
);

interface MemoryGraphViewProps {
  memories: Memory[];
  onNodeClick: (id: string) => void;
  highlightNodeIds?: string[];
}

const typeColors: Record<MemoryType, string> = {
  episodic: '#60a5fa',
  semantic: '#a78bfa',
  procedural: '#4ade80',
};

const LoadingFallback: React.FC = () => (
  <div className="w-full h-full flex items-center justify-center bg-bg-secondary/30">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
      <p className="text-text-secondary">加载图谱...</p>
    </div>
  </div>
);

const EmptyGraph: React.FC = () => (
  <div className="w-full h-full flex items-center justify-center bg-bg-secondary/30">
    <div className="text-center text-text-secondary">
      <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
      <p>暂无图谱数据</p>
    </div>
  </div>
);

export const MemoryGraphView: React.FC<MemoryGraphViewProps> = ({
  memories,
  onNodeClick,
  highlightNodeIds = [],
}) => {
  const graphData = useMemo(() => {
    const nodes: GraphNode[] = memories.map((memory) => ({
      id: memory.id,
      name: memory.title || memory.content.slice(0, 30),
      type: memory.type,
      importance: memory.importance,
      size: 4 + memory.importance * 2,
      color: typeColors[memory.type],
    }));

    const links: GraphLink[] = [];
    const nodeIds = new Set(nodes.map((n) => n.id));

    memories.forEach((memory) => {
      memory.associations.memories.forEach((targetId) => {
        if (nodeIds.has(targetId) && memory.id < targetId) {
          links.push({
            source: memory.id,
            target: targetId,
            value: 1,
          });
        }
      });
    });

    return { nodes, links };
  }, [memories]);

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      onNodeClick(node.id);
    },
    [onNodeClick]
  );

  const paintNode = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const size = node.size;
      const isHighlighted = highlightNodeIds.includes(node.id);

      ctx.beginPath();
      ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI);
      ctx.fillStyle = isHighlighted ? '#d4af37' : node.color;
      ctx.globalAlpha = 0.8;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = isHighlighted ? '#d4af37' : 'rgba(212, 175, 55, 0.5)';
      ctx.lineWidth = isHighlighted ? 2 : 1;
      ctx.stroke();

      if (globalScale > 1.5) {
        ctx.font = `${10 / globalScale}px sans-serif`;
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(node.name.slice(0, 15), node.x || 0, (node.y || 0) + size + 2);
      }
    },
    [highlightNodeIds]
  );

  if (memories.length === 0) {
    return <EmptyGraph />;
  }

  return (
    <div className="w-full h-full bg-bg-secondary/30 rounded-xl overflow-hidden border border-border-light">
      <Suspense fallback={<LoadingFallback />}>
        <ForceGraph2D
          graphData={graphData}
          nodeCanvasObject={paintNode}
          onNodeClick={handleNodeClick}
          nodeRelSize={6}
          linkColor={() => 'rgba(212, 175, 55, 0.3)'}
          linkWidth={1}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          backgroundColor="transparent"
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
        />
      </Suspense>
    </div>
  );
};

export default MemoryGraphView;
