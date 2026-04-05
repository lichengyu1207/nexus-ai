import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { mockShowcaseData } from '../showcaseData';

const MemoryDetail: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const memoryData = mockShowcaseData.memory;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 400;
    canvas.height = 250;

    interface Node {
      id: number;
      x: number;
      y: number;
      label: string;
      connections: number[];
      pulsePhase: number;
    }

    const nodes: Node[] = [
      { id: 0, x: 200, y: 125, label: '核心记忆', connections: [1, 2, 3], pulsePhase: 0 },
      { id: 1, x: 80, y: 60, label: '学区房', connections: [0, 4], pulsePhase: 0.5 },
      { id: 2, x: 320, y: 60, label: '价格分析', connections: [0, 5], pulsePhase: 1 },
      { id: 3, x: 80, y: 190, label: '用户偏好', connections: [0], pulsePhase: 1.5 },
      { id: 4, x: 200, y: 40, label: '教育资源', connections: [1], pulsePhase: 2 },
      { id: 5, x: 320, y: 190, label: '地铁规划', connections: [2], pulsePhase: 2.5 },
    ];

    let time = 0;
    let animationId: number;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      time += 0.02;

      nodes.forEach(node => {
        node.connections.forEach(targetId => {
          const target = nodes.find(n => n.id === targetId);
          if (!target) return;

          const gradient = ctx.createLinearGradient(node.x, node.y, target.x, target.y);
          gradient.addColorStop(0, 'rgba(139, 92, 246, 0.6)');
          gradient.addColorStop(1, 'rgba(139, 92, 246, 0.2)');

          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(target.x, target.y);
          ctx.strokeStyle = gradient;
          ctx.lineWidth = 2;
          ctx.stroke();

          const particlePos = (time + node.pulsePhase) % 1;
          const px = node.x + (target.x - node.x) * particlePos;
          const py = node.y + (target.y - node.y) * particlePos;

          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#8B5CF6';
          ctx.fill();
        });
      });

      nodes.forEach(node => {
        const pulse = Math.sin(time * 2 + node.pulsePhase) * 0.3 + 0.7;
        const radius = node.id === 0 ? 35 : 25;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + 5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139, 92, 246, ${pulse * 0.2})`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.id === 0 ? 'rgba(139, 92, 246, 0.4)' : 'rgba(139, 92, 246, 0.2)';
        ctx.fill();
        ctx.strokeStyle = '#8B5CF6';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = node.id === 0 ? 'bold 14px sans-serif' : '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.label, node.x, node.y);
      });

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.canvasContainer}>
        <canvas ref={canvasRef} style={styles.canvas} />
      </div>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <span style={styles.statValue}>{memoryData.totalMemories.toLocaleString()}</span>
          <span style={styles.statLabel}>记忆总量</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statValue}>{memoryData.importantMemories}</span>
          <span style={styles.statLabel}>重要记忆</span>
        </div>
      </div>

      <div style={styles.connectionsSection}>
        <h4 style={styles.sectionTitle}>最近关联</h4>
        {memoryData.recentConnections.map((conn, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            style={styles.connectionItem}
          >
            <span style={styles.connectionFrom}>{conn.from}</span>
            <div style={styles.connectionLine}>
              <div style={{ ...styles.connectionStrength, width: `${conn.strength * 100}%` }} />
            </div>
            <span style={styles.connectionTo}>{conn.to}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  canvasContainer: {
    display: 'flex',
    justifyContent: 'center',
  },
  canvas: {
    maxWidth: '100%',
    height: 'auto',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
  },
  statCard: {
    padding: '16px',
    background: 'rgba(139, 92, 246, 0.1)',
    borderRadius: '12px',
    border: '1px solid rgba(139, 92, 246, 0.3)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  statValue: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#8B5CF6',
  },
  statLabel: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  connectionsSection: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    padding: '16px',
  },
  sectionTitle: {
    color: '#8B5CF6',
    fontSize: '14px',
    margin: '0 0 12px 0',
  },
  connectionItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '8px 0',
  },
  connectionFrom: {
    fontSize: '12px',
    color: '#fff',
    minWidth: '80px',
  },
  connectionLine: {
    flex: 1,
    height: '4px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  connectionStrength: {
    height: '100%',
    background: 'linear-gradient(90deg, #8B5CF6, #A78BFA)',
    borderRadius: '2px',
  },
  connectionTo: {
    fontSize: '12px',
    color: '#fff',
    minWidth: '80px',
    textAlign: 'right',
  },
};

export default MemoryDetail;
