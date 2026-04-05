import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import clusterApi, { AgentNode, SwarmLink, ClusterStats } from '../../api/cluster';

interface ClusterHealthProps {
  className?: string;
  showTopology?: boolean;
}

const NODE_TYPE_INFO: Record<AgentNode['type'], { name: string; icon: string; color: string }> = {
  red: { name: '红队', icon: '🔴', color: '#EF4444' },
  blue: { name: '蓝队', icon: '🔵', color: '#3B82F6' },
  supervisor: { name: '主管', icon: '🎯', color: '#D4AF37' },
  collector: { name: '采集', icon: '📊', color: '#10B981' },
  analyst: { name: '分析', icon: '📈', color: '#8B5CF6' },
  memory: { name: '记忆', icon: '🧠', color: '#F59E0B' },
  defense: { name: '防御', icon: '🛡️', color: '#06B6D4' },
  social: { name: '社交', icon: '👥', color: '#EC4899' },
};

const STATUS_INFO: Record<AgentNode['status'], { label: string; color: string }> = {
  healthy: { label: '健康', color: '#10B981' },
  degraded: { label: '降级', color: '#F59E0B' },
  down: { label: '离线', color: '#EF4444' },
  starting: { label: '启动中', color: '#3B82F6' },
};

const ClusterHealth: React.FC<ClusterHealthProps> = ({ className, showTopology = true }) => {
  const [selectedNode, setSelectedNode] = useState<AgentNode | null>(null);
  const [filter, setFilter] = useState<'all' | AgentNode['type'] | AgentNode['status']>('all');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const nodesRef = useRef<Array<{ id: string; x: number; y: number; vx: number; vy: number; node: AgentNode }>>([]);

  const { data: nodes, isLoading: nodesLoading, refetch: refetchNodes } = useQuery({
    queryKey: ['cluster-nodes'],
    queryFn: clusterApi.getNodes,
    refetchInterval: 10000,
  });

  const { data: links } = useQuery({
    queryKey: ['cluster-links'],
    queryFn: clusterApi.getSwarmLinks,
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['cluster-stats'],
    queryFn: clusterApi.getClusterStats,
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (!showTopology || !canvasRef.current || !nodes || !links) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.offsetWidth;
    const height = 400;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const centerX = width / 2;
    const centerY = height / 2;

    if (nodesRef.current.length !== nodes.length) {
      nodesRef.current = nodes.map((node, index) => {
        const angle = (index / nodes.length) * Math.PI * 2;
        const radius = 120 + Math.random() * 40;
        return {
          id: node.id,
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
          node,
        };
      });
    }

    const simulate = () => {
      ctx.clearRect(0, 0, width, height);

      links.forEach((link) => {
        const fromNode = nodesRef.current.find((n) => n.id === link.source);
        const toNode = nodesRef.current.find((n) => n.id === link.target);
        if (!fromNode || !toNode) return;

        const isActive = link.status === 'active';
        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.strokeStyle = isActive
          ? `rgba(16, 185, 129, ${0.3 + link.throughput * 0.01})`
          : 'rgba(156, 163, 175, 0.2)';
        ctx.lineWidth = 1 + link.throughput * 0.05;
        ctx.stroke();
      });

      nodesRef.current.forEach(({ x, y, node }) => {
        const typeInfo = NODE_TYPE_INFO[node.type];
        const statusInfo = STATUS_INFO[node.status];
        const radius = 20 + node.cpu * 0.1;

        ctx.beginPath();
        ctx.arc(x, y, radius + 5, 0, Math.PI * 2);
        ctx.fillStyle = `${statusInfo.color}20`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        const gradient = ctx.createRadialGradient(x - radius / 3, y - radius / 3, 0, x, y, radius);
        gradient.addColorStop(0, typeInfo.color);
        gradient.addColorStop(1, `${typeInfo.color}aa`);
        ctx.fillStyle = gradient;
        ctx.fill();

        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#fff';
        ctx.fillText(typeInfo.icon, x, y + 4);
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    simulate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [showTopology, nodes, links]);

  const filteredNodes = nodes?.filter((node) => {
    if (filter === 'all') return true;
    if (filter in NODE_TYPE_INFO) return node.type === filter;
    if (filter in STATUS_INFO) return node.status === filter;
    return true;
  });

  if (nodesLoading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className || ''}`}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">集群健康监控</h1>
          <p className="text-gray-500 mt-1">智能体节点状态</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as typeof filter)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="all">全部</option>
            <optgroup label="类型">
              {Object.entries(NODE_TYPE_INFO).map(([key, info]) => (
                <option key={key} value={key}>{info.name}</option>
              ))}
            </optgroup>
            <optgroup label="状态">
              {Object.entries(STATUS_INFO).map(([key, info]) => (
                <option key={key} value={key}>{info.label}</option>
              ))}
            </optgroup>
          </select>
          <button
            onClick={() => { refetchNodes(); }}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium"
          >
            刷新
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <span className="text-xl">✅</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.healthyNodes}</p>
                <p className="text-xs text-gray-500">健康节点</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
                <span className="text-xl">⚠️</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.degradedNodes}</p>
                <p className="text-xs text-gray-500">降级节点</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <span className="text-xl">💻</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.avgCpu.toFixed(0)}%</p>
                <p className="text-xs text-gray-500">平均CPU</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <span className="text-xl">📨</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.totalMessagesPerSec}</p>
                <p className="text-xs text-gray-500">消息/秒</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {showTopology && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">集群拓扑</h3>
          <canvas
            ref={canvasRef}
            className="w-full rounded-lg bg-gray-50"
            style={{ height: 400 }}
          />
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">节点</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CPU</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">内存</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">最后心跳</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <AnimatePresence>
              {filteredNodes?.map((node, index) => {
                const typeInfo = NODE_TYPE_INFO[node.type];
                const statusInfo = STATUS_INFO[node.status];

                return (
                  <motion.tr
                    key={node.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: index * 0.02 }}
                    onClick={() => setSelectedNode(selectedNode?.id === node.id ? null : node)}
                    className={`cursor-pointer hover:bg-gray-50 ${selectedNode?.id === node.id ? 'bg-primary-50' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{typeInfo.icon}</span>
                        <span className="font-medium text-gray-900">{node.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded-full text-xs font-medium" style={{ background: `${typeInfo.color}20`, color: typeInfo.color }}>
                        {typeInfo.name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ background: statusInfo.color }} />
                        <span className="text-sm text-gray-600">{statusInfo.label}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${node.cpu}%`, background: node.cpu > 80 ? '#EF4444' : '#10B981' }} />
                        </div>
                        <span className="text-xs text-gray-500">{node.cpu}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${node.memory}%`, background: node.memory > 80 ? '#EF4444' : '#3B82F6' }} />
                        </div>
                        <span className="text-xs text-gray-500">{node.memory}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(node.lastHeartbeat).toLocaleTimeString()}
                    </td>
                  </motion.tr>
                );
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-4 right-4 bg-white rounded-xl border border-gray-200 shadow-lg p-4 max-w-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900">{selectedNode.name}</h4>
              <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">地址</span>
                <span className="text-gray-900 font-mono text-xs">{selectedNode.address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">版本</span>
                <span className="text-gray-900">{selectedNode.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">连接数</span>
                <span className="text-gray-900">{selectedNode.connections}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ClusterHealth;
