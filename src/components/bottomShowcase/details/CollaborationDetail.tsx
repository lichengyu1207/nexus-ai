import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { mockShowcaseData } from '../showcaseData';
import HoneycombGrid, { SwarmNode, SwarmLink } from '../HoneycombGrid';

const CollaborationDetail: React.FC = () => {
  const [viewMode, setViewMode] = useState<'ministry' | 'swarm'>('ministry');
  const [nodes, setNodes] = useState<SwarmNode[]>([]);
  const [links, setLinks] = useState<SwarmLink[]>([]);
  const agents = mockShowcaseData.collaboration.agents;

  useEffect(() => {
    const ministryNodes: SwarmNode[] = agents.map((agent, i) => {
      const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
      const radius = 0.35;
      return {
        id: agent.id,
        name: agent.name,
        type: 'ministry' as const,
        x: 0.5 + Math.cos(angle) * radius,
        y: 0.5 + Math.sin(angle) * radius,
        status: agent.status === 'done' ? 'healthy' : agent.status === 'working' ? 'warning' : 'offline',
        load: agent.status === 'working' ? 0.8 : agent.status === 'done' ? 0.3 : 0,
        latency: 20 + Math.random() * 30,
        taskCount: agent.status === 'working' ? 2 : agent.status === 'done' ? 1 : 0,
      };
    });

    const swarmNodes: SwarmNode[] = [
      { id: 'supervisor', name: '主管代理', type: 'supervisor', x: 0.5, y: 0.25, status: 'healthy', load: 0.7, latency: 10, taskCount: 3 },
      ...ministryNodes.map((n, i) => ({
        ...n,
        x: 0.2 + (i % 3) * 0.3,
        y: 0.45 + Math.floor(i / 3) * 0.3,
      })),
      { id: 'red_1', name: '红队-攻击者', type: 'red_team', x: 0.1, y: 0.15, status: 'healthy', load: 0.4, latency: 50, taskCount: 1 },
      { id: 'blue_1', name: '蓝队-防御者', type: 'blue_team', x: 0.9, y: 0.15, status: 'healthy', load: 0.5, latency: 35, taskCount: 2 },
      { id: 'worker_1', name: '工作节点', type: 'worker', x: 0.5, y: 0.85, status: 'healthy', load: 0.6, latency: 25, taskCount: 2 },
    ];

    const ministryLinks: SwarmLink[] = [
      { from: 'li', to: 'hu', latency: 15, active: true },
      { from: 'hu', to: 'li_guan', latency: 18, active: true },
      { from: 'li_guan', to: 'bing', latency: 22, active: true },
      { from: 'bing', to: 'gong', latency: 20, active: true },
      { from: 'gong', to: 'xing', latency: 25, active: true },
      { from: 'xing', to: 'li', latency: 15, active: true },
    ];

    const swarmLinks: SwarmLink[] = [
      { from: 'supervisor', to: 'li', latency: 20, active: true },
      { from: 'supervisor', to: 'li_guan', latency: 18, active: true },
      { from: 'supervisor', to: 'bing', latency: 25, active: true },
      ...ministryLinks,
      { from: 'red_1', to: 'supervisor', latency: 50, active: true },
      { from: 'blue_1', to: 'supervisor', latency: 35, active: true },
      { from: 'worker_1', to: 'gong', latency: 25, active: true },
    ];

    setNodes(viewMode === 'ministry' ? ministryNodes : swarmNodes);
    setLinks(viewMode === 'ministry' ? ministryLinks : swarmLinks);
  }, [viewMode, agents]);

  useEffect(() => {
    const interval = setInterval(() => {
      setNodes(prev => prev.map(node => ({
        ...node,
        load: node.status === 'offline' ? 0 : Math.min(1, Math.max(0.1, node.load + (Math.random() - 0.5) * 0.1)),
        latency: Math.max(10, node.latency + Math.floor((Math.random() - 0.5) * 10)),
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.viewToggle}>
        <motion.button
          style={{
            ...styles.toggleButton,
            background: viewMode === 'ministry' ? 'rgba(212, 175, 55, 0.3)' : 'rgba(255, 255, 255, 0.1)',
            borderColor: viewMode === 'ministry' ? '#D4AF37' : 'rgba(255, 255, 255, 0.2)',
          }}
          onClick={() => setViewMode('ministry')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          六部视图
        </motion.button>
        <motion.button
          style={{
            ...styles.toggleButton,
            background: viewMode === 'swarm' ? 'rgba(138, 43, 226, 0.3)' : 'rgba(255, 255, 255, 0.1)',
            borderColor: viewMode === 'swarm' ? '#8A2BE2' : 'rgba(255, 255, 255, 0.2)',
          }}
          onClick={() => setViewMode('swarm')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          蜂群视图
        </motion.button>
      </div>

      <div style={styles.gridContainer}>
        <HoneycombGrid
          nodes={nodes}
          links={links}
          width={380}
          height={280}
        />
      </div>

      <div style={styles.agentsList}>
        {agents.map((agent) => (
          <motion.div
            key={agent.id}
            style={{
              ...styles.agentItem,
              borderColor: agent.status === 'working' ? '#D4AF37' : agent.status === 'done' ? '#22c55e' : 'rgba(255, 255, 255, 0.1)',
            }}
            animate={agent.status === 'working' ? { opacity: [0.7, 1, 0.7] } : {}}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <span style={styles.agentName}>{agent.name}</span>
            <span style={{
              ...styles.agentStatus,
              color: agent.status === 'working' ? '#D4AF37' : agent.status === 'done' ? '#22c55e' : 'rgba(255, 255, 255, 0.5)',
            }}>
              {agent.status === 'working' ? '处理中' : agent.status === 'done' ? '已完成' : '待命'}
            </span>
            <span style={styles.agentTask}>{agent.task}</span>
          </motion.div>
        ))}
      </div>

      <motion.button
        style={styles.viewButton}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        查看实时任务 →
      </motion.button>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  viewToggle: {
    display: 'flex',
    justifyContent: 'center',
    gap: '12px',
  },
  toggleButton: {
    padding: '10px 20px',
    borderRadius: '8px',
    border: '1px solid',
    color: '#fff',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  gridContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '12px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '12px',
  },
  agentsList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
  },
  agentItem: {
    padding: '10px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
    border: '1px solid',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  agentName: {
    fontSize: '13px',
    color: '#fff',
    fontWeight: 'bold',
  },
  agentStatus: {
    fontSize: '11px',
  },
  agentTask: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.4)',
    textAlign: 'center',
  },
  viewButton: {
    padding: '12px 24px',
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    borderRadius: '8px',
    color: '#3B82F6',
    fontSize: '14px',
    cursor: 'pointer',
    alignSelf: 'center',
  },
};

export default CollaborationDetail;
