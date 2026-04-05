import React, { useState } from 'react';
import { motion } from 'framer-motion';
import WorkflowGraph from '@/components/WorkflowGraph';
import MonitoringDashboard from '@/components/MonitoringDashboard';

const FunctionalIntegrationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'workflow' | 'monitoring'>('dashboard');
  const [taskId, setTaskId] = useState('');

  return (
    <div className="p-6">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex justify-between items-center mb-6"
      >
        <div>
          <h1 className="text-2xl font-bold text-text-primary">功能级融合平台</h1>
          <p className="text-sm text-text-secondary mt-1">
            工作流 · 治理 · 执行 · 数据 · 协同 · 输出
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'dashboard'
                ? 'bg-accent-gold text-gray-900'
                : 'bg-bg-tertiary text-text-secondary hover:bg-white/5'
            }`}
            onClick={() => setActiveTab('dashboard')}
          >
            仪表盘
          </button>
          <button
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'workflow'
                ? 'bg-accent-gold text-gray-900'
                : 'bg-bg-tertiary text-text-secondary hover:bg-white/5'
            }`}
            onClick={() => setActiveTab('workflow')}
          >
            工作流
          </button>
          <button
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'monitoring'
                ? 'bg-accent-gold text-gray-900'
                : 'bg-bg-tertiary text-text-secondary hover:bg-white/5'
            }`}
            onClick={() => setActiveTab('monitoring')}
          >
            监控
          </button>
        </div>
      </motion.header>

      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-bg-secondary rounded-lg p-6">
                <h3 className="text-sm font-medium text-text-secondary">任务统计</h3>
                <p className="text-3xl font-bold text-accent-gold mt-2">100</p>
                <p className="text-sm text-text-secondary mt-1">总任务数</p>
              </div>
              <div className="bg-bg-secondary rounded-lg p-6">
                <h3 className="text-sm font-medium text-text-secondary">成功率</h3>
                <p className="text-3xl font-bold text-status-success mt-2">85%</p>
                <p className="text-sm text-text-secondary mt-1">任务成功率</p>
              </div>
              <div className="bg-bg-secondary rounded-lg p-6">
                <h3 className="text-sm font-medium text-text-secondary">智能体状态</h3>
                <p className="text-3xl font-bold text-status-info mt-2">5/5</p>
                <p className="text-sm text-text-secondary mt-1">在线智能体</p>
              </div>
            </div>

            <div className="bg-bg-secondary rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 text-text-primary">功能概览</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">工作流融合</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    任务规格生成 · DAG调度 · 工作流可视化
                  </p>
                </div>
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">治理融合</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    工具注册 · 权限管理 · 分布式追踪
                  </p>
                </div>
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">执行底座</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    原子动作 · 执行器 · 补偿队列
                  </p>
                </div>
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">数据治理</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    数据资产目录 · 统一访问代理
                  </p>
                </div>
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">协同架构</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    gRPC通信 · 服务发现 · 负载均衡
                  </p>
                </div>
                <div className="border border-border-light rounded-lg p-4">
                  <h3 className="font-medium text-text-primary">输出融合</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    任务报告 · 实时监控面板
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'workflow' && (
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-text-primary">工作流可视化</h2>
            <div className="flex gap-4 mb-4">
              <input
                type="text"
                placeholder="输入任务ID"
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                className="flex-1 px-4 py-2 border border-border-light rounded-lg focus:outline-none focus:border-accent-gold text-text-primary"
              />
              <button
                onClick={() => {}}
                className="px-6 py-2 bg-accent-gold text-gray-900 rounded-lg hover:opacity-90 transition-opacity"
              >
                加载任务
              </button>
            </div>
            <WorkflowGraph taskId={taskId} />
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-text-primary">实时监控面板</h2>
            <MonitoringDashboard />
          </div>
        )}
      </motion.main>
    </div>
  );
};

export default FunctionalIntegrationPage;
