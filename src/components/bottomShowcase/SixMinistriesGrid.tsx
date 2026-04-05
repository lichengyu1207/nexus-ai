import React, { useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';

interface Ministry {
  id: string;
  name: string;
  icon: string;
  color: string;
  role: string;
}

interface DataFlow {
  from: string;
  to: string;
  label?: string;
}

interface SixMinistriesGridProps {
  activeMinistries?: string[];
  dataFlows?: DataFlow[];
  showLabels?: boolean;
  showDataFlow?: boolean;
  onMinistryClick?: (id: string) => void;
}

const MINISTRIES: Ministry[] = [
  { id: 'li', name: '吏部', icon: '吏', color: '#6366f1', role: '人事调度' },
  { id: 'hu', name: '户部', icon: '户', color: '#10b981', role: '资源管理' },
  { id: 'li_guan', name: '礼部', icon: '礼', color: '#3b82f6', role: '需求接收' },
  { id: 'bing', name: '兵部', icon: '兵', color: '#f59e0b', role: '策略执行' },
  { id: 'gong', name: '工部', icon: '工', color: '#ef4444', role: '建设维护' },
  { id: 'xing', name: '刑部', icon: '刑', color: '#8b5cf6', role: '审计合规' },
];

const SixMinistriesGrid: React.FC<SixMinistriesGridProps> = ({
  activeMinistries = [],
  dataFlows = [],
  showLabels = true,
  showDataFlow = true,
  onMinistryClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Array<{
    x: number;
    y: number;
    targetX: number;
    targetY: number;
    progress: number;
    color: string;
  }>>([]);

  const getMinistryPosition = useCallback((id: string, containerWidth: number, containerHeight: number) => {
    const index = MINISTRIES.findIndex(m => m.id === id);
    const cols = 3;
    const rows = 2;
    const cellWidth = containerWidth / cols;
    const cellHeight = containerHeight / rows;
    const col = index % cols;
    const row = Math.floor(index / cols);
    return {
      x: cellWidth * (col + 0.5),
      y: cellHeight * (row + 0.5),
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !showDataFlow) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.parentElement?.getBoundingClientRect();
    if (!rect) return;

    canvas.width = rect.width;
    canvas.height = rect.height;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      dataFlows.forEach(flow => {
        const fromPos = getMinistryPosition(flow.from, canvas.width, canvas.height);
        const toPos = getMinistryPosition(flow.to, canvas.width, canvas.height);

        const gradient = ctx.createLinearGradient(fromPos.x, fromPos.y, toPos.x, toPos.y);
        const fromMinistry = MINISTRIES.find(m => m.id === flow.from);
        const toMinistry = MINISTRIES.find(m => m.id === flow.to);
        gradient.addColorStop(0, `${fromMinistry?.color || '#fff'}40`);
        gradient.addColorStop(1, `${toMinistry?.color || '#fff'}40`);

        ctx.beginPath();
        ctx.moveTo(fromPos.x, fromPos.y);
        ctx.lineTo(toPos.x, toPos.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.stroke();
        ctx.setLineDash([]);

        const time = Date.now() / 1000;
        const particleCount = 3;
        for (let i = 0; i < particleCount; i++) {
          const progress = ((time * 0.5 + i / particleCount) % 1);
          const px = fromPos.x + (toPos.x - fromPos.x) * progress;
          const py = fromPos.y + (toPos.y - fromPos.y) * progress;

          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fillStyle = fromMinistry?.color || '#fff';
          ctx.fill();

          ctx.beginPath();
          ctx.arc(px, py, 8, 0, Math.PI * 2);
          ctx.fillStyle = `${fromMinistry?.color || '#fff'}30`;
          ctx.fill();
        }
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [dataFlows, showDataFlow, getMinistryPosition]);

  return (
    <div style={styles.container}>
      <canvas ref={canvasRef} style={styles.canvas} />
      <div style={styles.grid}>
        {MINISTRIES.map((ministry) => {
          const isActive = activeMinistries.includes(ministry.id);
          const hasFlow = dataFlows.some(f => f.from === ministry.id || f.to === ministry.id);

          return (
            <motion.div
              key={ministry.id}
              style={{
                ...styles.ministryCard,
                borderColor: isActive ? ministry.color : 'rgba(255, 255, 255, 0.1)',
                background: isActive 
                  ? `linear-gradient(135deg, ${ministry.color}20, ${ministry.color}10)`
                  : 'rgba(255, 255, 255, 0.03)',
              }}
              whileHover={{ scale: 1.05, y: -5 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onMinistryClick?.(ministry.id)}
            >
              {isActive && (
                <motion.div
                  style={{ ...styles.activeRing, borderColor: ministry.color }}
                  animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}

              <motion.div
                style={{ ...styles.iconContainer, background: ministry.color }}
                animate={isActive ? { 
                  boxShadow: [`0 0 20px ${ministry.color}50`, `0 0 40px ${ministry.color}80`, `0 0 20px ${ministry.color}50`]
                } : {}}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <span style={styles.icon}>{ministry.icon}</span>
              </motion.div>

              {showLabels && (
                <>
                  <span style={styles.name}>{ministry.name}</span>
                  <span style={styles.role}>{ministry.role}</span>
                </>
              )}

              {hasFlow && (
                <motion.div
                  style={{ ...styles.flowIndicator, background: ministry.color }}
                  animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
    width: '100%',
    height: '100%',
    minHeight: '200px',
  },
  canvas: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    zIndex: 1,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gridTemplateRows: 'repeat(2, 1fr)',
    gap: '12px',
    position: 'relative',
    zIndex: 2,
    height: '100%',
  },
  ministryCard: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '16px 8px',
    borderRadius: '12px',
    border: '2px solid',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  activeRing: {
    position: 'absolute',
    inset: '-4px',
    borderRadius: '16px',
    border: '2px solid',
    pointerEvents: 'none',
  },
  iconContainer: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '8px',
  },
  icon: {
    fontSize: '24px',
    color: '#fff',
    fontFamily: 'serif',
    fontWeight: 'bold',
  },
  name: {
    fontSize: '14px',
    color: '#fff',
    fontWeight: 'bold',
    marginBottom: '2px',
  },
  role: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  flowIndicator: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
};

export default SixMinistriesGrid;
export { MINISTRIES };
