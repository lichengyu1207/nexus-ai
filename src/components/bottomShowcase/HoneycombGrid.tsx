import React, { useEffect, useRef, useCallback } from 'react';

interface SwarmNode {
  id: string;
  name: string;
  type: 'ministry' | 'red_team' | 'blue_team' | 'supervisor' | 'worker';
  x: number;
  y: number;
  status: 'healthy' | 'warning' | 'offline';
  load: number;
  latency: number;
  taskCount: number;
}

interface SwarmLink {
  from: string;
  to: string;
  latency: number;
  active: boolean;
}

interface HoneycombGridProps {
  nodes: SwarmNode[];
  links: SwarmLink[];
  width?: number;
  height?: number;
  onNodeClick?: (node: SwarmNode) => void;
  onNodeHover?: (node: SwarmNode | null) => void;
  highlightNodes?: string[];
  consensusNodes?: string[];
}

const NODE_COLORS: Record<string, string> = {
  ministry: '#D4AF37',
  red_team: '#EF4444',
  blue_team: '#3B82F6',
  supervisor: '#10B981',
  worker: '#8B5CF6',
};

const STATUS_COLORS: Record<string, string> = {
  healthy: '#22C55E',
  warning: '#F59E0B',
  offline: '#6B7280',
};

const HoneycombGrid: React.FC<HoneycombGridProps> = ({
  nodes,
  links,
  width = 400,
  height = 300,
  onNodeClick,
  onNodeHover,
  highlightNodes = [],
  consensusNodes = [],
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const timeRef = useRef<number>(0);
  const hoveredNodeRef = useRef<SwarmNode | null>(null);

  const getLatencyColor = useCallback((latency: number): string => {
    if (latency < 50) return '#22C55E';
    if (latency < 200) return '#F59E0B';
    return '#EF4444';
  }, []);

  const drawHexagon = useCallback((
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    size: number,
    fillStyle: string,
    strokeStyle: string,
    lineWidth: number = 1
  ) => {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 6;
      const hx = x + size * Math.cos(angle);
      const hy = y + size * Math.sin(angle);
      if (i === 0) {
        ctx.moveTo(hx, hy);
      } else {
        ctx.lineTo(hx, hy);
      }
    }
    ctx.closePath();
    ctx.fillStyle = fillStyle;
    ctx.fill();
    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
  }, []);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    timeRef.current += 0.016;
    const time = timeRef.current;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const hexSize = 30;
    const hexWidth = hexSize * Math.sqrt(3);
    const hexHeight = hexSize * 2;

    for (let row = 0; row < Math.ceil(canvas.height / (hexHeight * 0.75)) + 1; row++) {
      for (let col = 0; col < Math.ceil(canvas.width / hexWidth) + 1; col++) {
        const x = col * hexWidth + (row % 2 === 1 ? hexWidth / 2 : 0);
        const y = row * hexHeight * 0.75;

        drawHexagon(
          ctx,
          x, y, hexSize - 2,
          'rgba(255, 255, 255, 0.02)',
          'rgba(255, 255, 255, 0.05)',
          1
        );
      }
    }

    links.forEach(link => {
      const fromNode = nodes.find(n => n.id === link.from);
      const toNode = nodes.find(n => n.id === link.to);
      if (!fromNode || !toNode) return;

      const fromX = fromNode.x * canvas.width;
      const fromY = fromNode.y * canvas.height;
      const toX = toNode.x * canvas.width;
      const toY = toNode.y * canvas.height;

      const gradient = ctx.createLinearGradient(fromX, fromY, toX, toY);
      const latencyColor = getLatencyColor(link.latency);
      gradient.addColorStop(0, `${latencyColor}40`);
      gradient.addColorStop(1, `${latencyColor}20`);

      ctx.beginPath();
      ctx.moveTo(fromX, fromY);
      ctx.lineTo(toX, toY);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = link.active ? 2 : 1;
      ctx.setLineDash(link.active ? [] : [4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      if (link.active) {
        const particleCount = 2;
        for (let i = 0; i < particleCount; i++) {
          const progress = ((time * 0.3 + i / particleCount) % 1);
          const px = fromX + (toX - fromX) * progress;
          const py = fromY + (toY - fromY) * progress;

          ctx.beginPath();
          ctx.arc(px, py, 3, 0, Math.PI * 2);
          ctx.fillStyle = latencyColor;
          ctx.fill();
        }
      }
    });

    nodes.forEach(node => {
      const x = node.x * canvas.width;
      const y = node.y * canvas.height;
      const baseSize = 15 + node.load * 10;
      const isHighlighted = highlightNodes.includes(node.id);
      const inConsensus = consensusNodes.includes(node.id);
      const isHovered = hoveredNodeRef.current?.id === node.id;

      const nodeColor = NODE_COLORS[node.type] || '#8B5CF6';
      const statusColor = STATUS_COLORS[node.status] || '#6B7280';

      if (isHighlighted || inConsensus) {
        const pulseSize = baseSize + 10 + Math.sin(time * 3) * 5;
        ctx.beginPath();
        ctx.arc(x, y, pulseSize, 0, Math.PI * 2);
        ctx.fillStyle = `${inConsensus ? '#F59E0B' : nodeColor}30`;
        ctx.fill();
      }

      if (isHovered) {
        ctx.beginPath();
        ctx.arc(x, y, baseSize + 15, 0, Math.PI * 2);
        ctx.strokeStyle = nodeColor;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.arc(x, y, baseSize, 0, Math.PI * 2);
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, baseSize);
      gradient.addColorStop(0, `${nodeColor}CC`);
      gradient.addColorStop(0.7, `${nodeColor}80`);
      gradient.addColorStop(1, `${nodeColor}40`);
      ctx.fillStyle = gradient;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(x, y, baseSize + 3, 0, Math.PI * 2);
      ctx.strokeStyle = statusColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      if (node.status === 'healthy') {
        const pulseOpacity = 0.3 + Math.sin(time * 2) * 0.2;
        ctx.beginPath();
        ctx.arc(x, y, baseSize + 8, 0, Math.PI * 2);
        ctx.strokeStyle = `${statusColor}${Math.floor(pulseOpacity * 255).toString(16).padStart(2, '0')}`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const shortName = node.name.substring(0, 2);
      ctx.fillText(shortName, x, y);

      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.font = '9px sans-serif';
      ctx.fillText(`${node.taskCount}`, x, y + baseSize + 12);
    });

    animationRef.current = requestAnimationFrame(draw);
  }, [nodes, links, highlightNodes, consensusNodes, drawHexagon, getLatencyColor]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = width;
    canvas.height = height;

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [width, height, draw]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let foundNode: SwarmNode | null = null;
    for (const node of nodes) {
      const x = node.x * canvas.width;
      const y = node.y * canvas.height;
      const size = 15 + node.load * 10;
      const distance = Math.sqrt((mouseX - x) ** 2 + (mouseY - y) ** 2);
      if (distance < size + 5) {
        foundNode = node;
        break;
      }
    }

    if (foundNode !== hoveredNodeRef.current) {
      hoveredNodeRef.current = foundNode;
      onNodeHover?.(foundNode);
      canvas.style.cursor = foundNode ? 'pointer' : 'default';
    }
  }, [nodes, onNodeHover]);

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (hoveredNodeRef.current) {
      onNodeClick?.(hoveredNodeRef.current);
    }
  }, [onNodeClick]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        maxWidth: `${width}px`,
        maxHeight: `${height}px`,
      }}
      onMouseMove={handleMouseMove}
      onClick={handleClick}
    />
  );
};

export default HoneycombGrid;
export type { SwarmNode, SwarmLink };
