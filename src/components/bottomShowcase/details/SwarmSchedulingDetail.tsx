import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import HoneycombGrid, { SwarmNode, SwarmLink } from '../HoneycombGrid';
import { MINISTRIES } from '../SixMinistriesGrid';

interface SwarmSchedulingDetailProps {}

const generateMockNodes = (): SwarmNode[] => {
  const nodes: SwarmNode[] = [
    { id: 'supervisor', name: '主管代理', type: 'supervisor', x: 0.5, y: 0.3, status: 'healthy', load: 0.8, latency: 10, taskCount: 5 },
    { id: 'li', name: '吏部', type: 'ministry', x: 0.2, y: 0.5, status: 'healthy', load: 0.6, latency: 25, taskCount: 3 },
    { id: 'hu', name: '户部', type: 'ministry', x: 0.35, y: 0.65, status: 'healthy', load: 0.4, latency: 30, taskCount: 2 },
    { id: 'li_guan', name: '礼部', type: 'ministry', x: 0.5, y: 0.75, status: 'healthy', load: 0.7, latency: 20, taskCount: 4 },
    { id: 'bing', name: '兵部', type: 'ministry', x: 0.65, y: 0.65, status: 'warning', load: 0.9, latency: 45, taskCount: 6 },
    { id: 'gong', name: '工部', type: 'ministry', x: 0.8, y: 0.5, status: 'healthy', load: 0.5, latency: 35, taskCount: 2 },
    { id: 'xing', name: '刑部', type: 'ministry', x: 0.65, y: 0.35, status: 'healthy', load: 0.3, latency: 28, taskCount: 1 },
    { id: 'red_1', name: '红队-攻击者', type: 'red_team', x: 0.15, y: 0.2, status: 'healthy', load: 0.2, latency: 50, taskCount: 1 },
    { id: 'red_2', name: '红队-渗透者', type: 'red_team', x: 0.85, y: 0.2, status: 'offline', load: 0, latency: 999, taskCount: 0 },
    { id: 'blue_1', name: '蓝队-防御者', type: 'blue_team', x: 0.15, y: 0.8, status: 'healthy', load: 0.6, latency: 40, taskCount: 3 },
    { id: 'blue_2', name: '蓝队-监控者', type: 'blue_team', x: 0.85, y: 0.8, status: 'healthy', load: 0.4, latency: 35, taskCount: 2 },
    { id: 'worker_1', name: '工作节点1', type: 'worker', x: 0.3, y: 0.15, status: 'healthy', load: 0.7, latency: 22, taskCount: 4 },
    { id: 'worker_2', name: '工作节点2', type: 'worker', x: 0.7, y: 0.15, status: 'healthy', load: 0.5, latency: 28, taskCount: 3 },
  ];
  return nodes;
};

const generateMockLinks = (nodes: SwarmNode[]): SwarmLink[] => {
  const links: SwarmLink[] = [
    { from: 'supervisor', to: 'li', latency: 25, active: true },
    { from: 'supervisor', to: 'li_guan', latency: 20, active: true },
    { from: 'supervisor', to: 'bing', latency: 45, active: true },
    { from: 'li', to: 'hu', latency: 15, active: true },
    { from: 'hu', to: 'li_guan', latency: 18, active: false },
    { from: 'li_guan', to: 'bing', latency: 22, active: true },
    { from: 'bing', to: 'gong', latency: 30, active: true },
    { from: 'gong', to: 'xing', latency: 25, active: false },
    { from: 'xing', to: 'li', latency: 20, active: true },
    { from: 'red_1', to: 'supervisor', latency: 50, active: true },
    { from: 'blue_1', to: 'supervisor', latency: 40, active: true },
    { from: 'blue_2', to: 'red_2', latency: 200, active: false },
    { from: 'worker_1', to: 'li', latency: 22, active: true },
    { from: 'worker_2', to: 'gong', latency: 28, active: true },
  ];
  return links;
};

const SwarmSchedulingDetail: React.FC<SwarmSchedulingDetailProps> = () => {
  const [nodes, setNodes] = useState<SwarmNode[]>([]);
  const [links, setLinks] = useState<SwarmLink[]>([]);
  const [selectedNode, setSelectedNode] = useState<SwarmNode | null>(null);
  const [consensusNodes, setConsensusNodes] = useState<string[]>([]);
  const [consensusPhase, setConsensusPhase] = useState<string>('');
  const [showConsensus, setShowConsensus] = useState(false);
  const [stats, setStats] = useState({
    totalNodes: 0,
    activeNodes: 0,
    totalTasks: 0,
    avgLatency: 0,
  });

  useEffect(() => {
    const mockNodes = generateMockNodes();
    const mockLinks = generateMockLinks(mockNodes);
    setNodes(mockNodes);
    setLinks(mockLinks);

    const activeNodes = mockNodes.filter(n => n.status !== 'offline');
    setStats({
      totalNodes: mockNodes.length,
      activeNodes: activeNodes.length,
      totalTasks: mockNodes.reduce((sum, n) => sum + n.taskCount, 0),
      avgLatency: Math.round(activeNodes.reduce((sum, n) => sum + n.latency, 0) / activeNodes.length),
    });

    const interval = setInterval(() => {
      setNodes(prev => prev.map(node => ({
        ...node,
        load: node.status === 'offline' ? 0 : Math.min(1, Math.max(0, node.load + (Math.random() - 0.5) * 0.1)),
        latency: node.status === 'offline' ? 999 : Math.max(10, node.latency + Math.floor((Math.random() - 0.5) * 10)),
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const runConsensusDemo = useCallback(() => {
    setShowConsensus(true);
    setConsensusPhase('Pre-Prepare');

    const consensusParticipants = ['supervisor', 'li', 'hu', 'li_guan', 'bing'];
    
    setTimeout(() => {
      setConsensusNodes(consensusParticipants);
      setConsensusPhase('Prepare');
    }, 500);

    setTimeout(() => {
      setConsensusPhase('Commit');
    }, 1500);

    setTimeout(() => {
      setConsensusPhase('完成');
      setTimeout(() => {
        setConsensusNodes([]);
        setShowConsensus(false);
        setConsensusPhase('');
      }, 1000);
    }, 2500);
  }, []);

  const handleNodeClick = useCallback((node: SwarmNode) => {
    setSelectedNode(node);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.statsBar}>
        <div style={styles.statItem}>
          <span style={styles.statValue}>{stats.totalNodes}</span>
          <span style={styles.statLabel}>总节点</span>
        </div>
        <div style={styles.statItem}>
          <span style={{ ...styles.statValue, color: '#22C55E' }}>{stats.activeNodes}</span>
          <span style={styles.statLabel}>在线</span>
        </div>
        <div style={styles.statItem}>
          <span style={styles.statValue}>{stats.totalTasks}</span>
          <span style={styles.statLabel}>任务数</span>
        </div>
        <div style={styles.statItem}>
          <span style={{ ...styles.statValue, color: stats.avgLatency < 50 ? '#22C55E' : '#F59E0B' }}>
            {stats.avgLatency}ms
          </span>
          <span style={styles.statLabel}>平均延迟</span>
        </div>
      </div>

      <div style={styles.gridContainer}>
        <HoneycombGrid
          nodes={nodes}
          links={links}
          width={380}
          height={250}
          onNodeClick={handleNodeClick}
          consensusNodes={consensusNodes}
        />
      </div>

      {showConsensus && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={styles.consensusBar}
        >
          <span style={styles.consensusIcon}>🔄</span>
          <span style={styles.consensusText}>PBFT共识: {consensusPhase}</span>
          <div style={styles.consensusProgress}>
            <motion.div
              style={styles.consensusProgressFill}
              animate={{ width: consensusPhase === '完成' ? '100%' : consensusPhase === 'Commit' ? '66%' : consensusPhase === 'Prepare' ? '33%' : '0%' }}
            />
          </div>
        </motion.div>
      )}

      <div style={styles.actions}>
        <motion.button
          style={styles.demoButton}
          onClick={runConsensusDemo}
          disabled={showConsensus}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          🔄 演示共识过程
        </motion.button>
      </div>

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            style={styles.nodePanel}
          >
            <div style={styles.nodePanelHeader}>
              <span style={styles.nodePanelTitle}>{selectedNode.name}</span>
              <button style={styles.closeButton} onClick={() => setSelectedNode(null)}>✕</button>
            </div>
            <div style={styles.nodePanelContent}>
              <div style={styles.nodeInfoRow}>
                <span style={styles.nodeInfoLabel}>类型</span>
                <span style={styles.nodeInfoValue}>{selectedNode.type}</span>
              </div>
              <div style={styles.nodeInfoRow}>
                <span style={styles.nodeInfoLabel}>状态</span>
                <span style={{ 
                  ...styles.nodeInfoValue, 
                  color: selectedNode.status === 'healthy' ? '#22C55E' : selectedNode.status === 'warning' ? '#F59E0B' : '#6B7280'
                }}>
                  {selectedNode.status === 'healthy' ? '健康' : selectedNode.status === 'warning' ? '警告' : '离线'}
                </span>
              </div>
              <div style={styles.nodeInfoRow}>
                <span style={styles.nodeInfoLabel}>负载</span>
                <div style={styles.loadBar}>
                  <div style={{ ...styles.loadFill, width: `${selectedNode.load * 100}%` }} />
                </div>
                <span style={styles.loadText}>{Math.round(selectedNode.load * 100)}%</span>
              </div>
              <div style={styles.nodeInfoRow}>
                <span style={styles.nodeInfoLabel}>延迟</span>
                <span style={styles.nodeInfoValue}>{selectedNode.latency}ms</span>
              </div>
              <div style={styles.nodeInfoRow}>
                <span style={styles.nodeInfoLabel}>任务数</span>
                <span style={styles.nodeInfoValue}>{selectedNode.taskCount}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: '#D4AF37' }} />
          <span>六部</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: '#EF4444' }} />
          <span>红队</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: '#3B82F6' }} />
          <span>蓝队</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: '#10B981' }} />
          <span>主管</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, background: '#8B5CF6' }} />
          <span>工作节点</span>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  statsBar: {
    display: 'flex',
    justifyContent: 'space-around',
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  statValue: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  gridContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '8px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '12px',
  },
  consensusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    background: 'rgba(245, 158, 11, 0.1)',
    borderRadius: '8px',
    border: '1px solid rgba(245, 158, 11, 0.3)',
  },
  consensusIcon: {
    fontSize: '20px',
  },
  consensusText: {
    flex: 1,
    color: '#F59E0B',
    fontSize: '14px',
  },
  consensusProgress: {
    width: '100px',
    height: '4px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  consensusProgressFill: {
    height: '100%',
    background: '#F59E0B',
    borderRadius: '2px',
  },
  actions: {
    display: 'flex',
    justifyContent: 'center',
  },
  demoButton: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #8A2BE2, #7C3AED)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  nodePanel: {
    position: 'absolute',
    right: '16px',
    top: '50%',
    transform: 'translateY(-50%)',
    width: '200px',
    background: 'rgba(10, 35, 66, 0.95)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    overflow: 'hidden',
  },
  nodePanelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  nodePanelTitle: {
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  closeButton: {
    background: 'transparent',
    border: 'none',
    color: 'rgba(255, 255, 255, 0.5)',
    cursor: 'pointer',
    fontSize: '16px',
  },
  nodePanelContent: {
    padding: '12px 16px',
  },
  nodeInfoRow: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '8px',
  },
  nodeInfoLabel: {
    width: '50px',
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  nodeInfoValue: {
    fontSize: '12px',
    color: '#fff',
  },
  loadBar: {
    flex: 1,
    height: '6px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '3px',
    overflow: 'hidden',
    margin: '0 8px',
  },
  loadFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #22C55E, #F59E0B)',
    borderRadius: '3px',
  },
  loadText: {
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.7)',
    minWidth: '35px',
    textAlign: 'right',
  },
  legend: {
    display: 'flex',
    justifyContent: 'center',
    gap: '16px',
    flexWrap: 'wrap',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  legendDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
  },
};

export default SwarmSchedulingDetail;
