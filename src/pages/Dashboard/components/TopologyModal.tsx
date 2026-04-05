import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, ArrowsPointIcon } from '@heroicons/react/24/outline';
import type { TopologyData, TopologyNode } from '../types';

interface TopologyModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TopologyData | null;
}

export function TopologyModal({ isOpen, onClose, data }: TopologyModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });

  const getNodeColor = (busyLevel: number) => {
    if (busyLevel < 0.3) return '#22c55e';
    if (busyLevel < 0.7) return '#f59e0b';
    return '#ef4444';
  };

  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2 + offset.x;
    const centerY = height / 2 + offset.y;

    ctx.clearRect(0, 0, width, height);

    const nodePositions: Map<string, { x: number; y: number }> = new Map();
    const nodeCount = data.nodes.length;
    const radius = Math.min(width, height) * 0.35 * scale;

    data.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodeCount - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      nodePositions.set(node.id, { x, y });
    });

    ctx.strokeStyle = 'rgba(245, 158, 11, 0.3)';
    ctx.lineWidth = 1;
    data.links.forEach((link) => {
      const source = nodePositions.get(link.source);
      const target = nodePositions.get(link.target);
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });

    data.nodes.forEach((node) => {
      const pos = nodePositions.get(node.id);
      if (!pos) return;

      const nodeRadius = Math.max(8, Math.min(20, node.taskCount * 2)) * scale;
      
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node.busyLevel);
      ctx.fill();

      ctx.fillStyle = '#ffffff';
      ctx.font = `${10 * scale}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(node.name, pos.x, pos.y + nodeRadius + 14 * scale);
    });
  }, [data, offset, scale]);

  useEffect(() => {
    if (isOpen) {
      drawGraph();
    }
  }, [isOpen, drawGraph]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((s) => Math.max(0.5, Math.min(2, s * delta)));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = { x: e.clientX - offset.x, y: e.clientY - offset.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setOffset({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (!data) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    for (const node of data.nodes) {
      const nodeCount = data.nodes.length;
      const radius = Math.min(canvas.width, canvas.height) * 0.35 * scale;
      const centerX = canvas.width / 2 + offset.x;
      const centerY = canvas.height / 2 + offset.y;
      const angle = (2 * Math.PI * data.nodes.indexOf(node)) / nodeCount - Math.PI / 2;
      const nodeX = centerX + radius * Math.cos(angle);
      const nodeY = centerY + radius * Math.sin(angle);
      const nodeRadius = Math.max(8, Math.min(20, node.taskCount * 2)) * scale;

      const distance = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);
      if (distance < nodeRadius) {
        setSelectedNode(node);
        return;
      }
    }
    setSelectedNode(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-4xl bg-slate-900 rounded-2xl border border-slate-700/50 overflow-hidden"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
              <div className="flex items-center gap-3">
                <ArrowsPointIcon className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-white">智能体集群拓扑</h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            <div className="relative">
              <canvas
                ref={canvasRef}
                width={800}
                height={500}
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onClick={handleCanvasClick}
                className="w-full cursor-move bg-slate-950"
              />

              {selectedNode && (
                <div className="absolute bottom-4 left-4 bg-slate-800/90 backdrop-blur-sm rounded-lg border border-slate-700/50 p-4">
                  <h4 className="text-white font-medium mb-2">{selectedNode.name}</h4>
                  <div className="text-sm text-slate-400 space-y-1">
                    <p>任务数: <span className="text-amber-400">{selectedNode.taskCount}</span></p>
                    <p>繁忙度: <span className={selectedNode.busyLevel < 0.3 ? 'text-green-400' : selectedNode.busyLevel < 0.7 ? 'text-amber-400' : 'text-red-400'}>
                      {Math.round(selectedNode.busyLevel * 100)}%
                    </span></p>
                  </div>
                </div>
              )}

              <div className="absolute top-4 right-4 flex items-center gap-2">
                <button
                  onClick={() => setScale((s) => Math.min(2, s * 1.2))}
                  className="px-3 py-1 bg-slate-700/50 text-slate-400 rounded-lg hover:bg-slate-700 hover:text-white text-sm"
                >
                  +
                </button>
                <span className="text-sm text-slate-400">{Math.round(scale * 100)}%</span>
                <button
                  onClick={() => setScale((s) => Math.max(0.5, s * 0.8))}
                  className="px-3 py-1 bg-slate-700/50 text-slate-400 rounded-lg hover:bg-slate-700 hover:text-white text-sm"
                >
                  -
                </button>
              </div>
            </div>

            <div className="px-6 py-3 border-t border-slate-700/50 flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" /> 健康
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> 繁忙
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" /> 过载
              </span>
              <span className="ml-auto">拖拽平移 · 滚轮缩放 · 点击查看详情</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
