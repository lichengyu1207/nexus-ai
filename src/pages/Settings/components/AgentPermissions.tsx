import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentPermissions } from '../hooks/useAgentPermissions';
import { ConfirmModal } from './ConfirmModal';
import type { AgentPermission } from '../types';

const mockTools = [
  { id: 'tool-1', name: '数据查询', category: '数据' },
  { id: 'tool-2', name: '报告生成', category: '报告' },
  { id: 'tool-3', name: '估值计算', category: '分析' },
  { id: 'tool-4', name: '风险评估', category: '分析' },
  { id: 'tool-5', name: '地图服务', category: '外部API' },
];

export function AgentPermissions() {
  const { permissions, isLoading, updatePermission, isUpdating } = useAgentPermissions();
  const [searchText, setSearchText] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<AgentPermission | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    agentId: string;
    toolIds: string[];
  }>({ isOpen: false, agentId: '', toolIds: [] });

  const filteredPermissions = permissions.filter(
    (p) =>
      p.agentName.toLowerCase().includes(searchText.toLowerCase()) ||
      p.department.toLowerCase().includes(searchText.toLowerCase())
  );

  const handleEditPermission = (agent: AgentPermission) => {
    setSelectedAgent(agent);
    setSelectedTools(agent.toolIds);
    setIsModalOpen(true);
  };

  const handleToolToggle = (toolId: string) => {
    setSelectedTools((prev) =>
      prev.includes(toolId) ? prev.filter((id) => id !== toolId) : [...prev, toolId]
    );
  };

  const handleSavePermission = () => {
    if (selectedAgent) {
      setConfirmModal({
        isOpen: true,
        agentId: selectedAgent.agentId,
        toolIds: selectedTools,
      });
    }
  };

  const handleConfirmSave = async () => {
    await updatePermission(confirmModal.agentId, confirmModal.toolIds);
    setIsModalOpen(false);
    setConfirmModal({ isOpen: false, agentId: '', toolIds: [] });
    setSelectedAgent(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-700/50 pb-4">
        <h2 className="text-xl font-semibold text-white">智能体权限管理</h2>
        <p className="text-gray-400 text-sm mt-1">配置每个智能体可调用的工具集</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="搜索智能体..."
            className="w-full px-4 py-2 pl-10 rounded-lg bg-slate-800 border border-slate-700
              text-white focus:outline-none focus:border-amber-500"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
        </div>
      </div>

      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-900/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">智能体</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">部门</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">工具权限</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {filteredPermissions.map((permission) => (
              <motion.tr
                key={permission.agentId}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="hover:bg-slate-700/30 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="text-white font-medium">{permission.agentName}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-400">{permission.department}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {permission.toolIds.slice(0, 3).map((toolId) => {
                      const tool = mockTools.find((t) => t.id === toolId);
                      return (
                        <span
                          key={toolId}
                          className="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400"
                        >
                          {tool?.name || toolId}
                        </span>
                      );
                    })}
                    {permission.toolIds.length > 3 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-gray-400">
                        +{permission.toolIds.length - 3}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleEditPermission(permission)}
                    className="px-3 py-1.5 rounded-lg bg-slate-700 text-gray-300 text-sm
                      hover:bg-slate-600 transition-colors"
                  >
                    编辑权限
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      <AnimatePresence>
        {isModalOpen && selectedAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-800 rounded-xl p-6 w-full max-w-lg border border-slate-700"
            >
              <h3 className="text-lg font-semibold text-white mb-4">
                编辑权限 - {selectedAgent.agentName}
              </h3>

              <div className="space-y-4 max-h-80 overflow-y-auto">
                {Object.entries(
                  mockTools.reduce((acc, tool) => {
                    if (!acc[tool.category]) acc[tool.category] = [];
                    acc[tool.category].push(tool);
                    return acc;
                  }, {} as Record<string, typeof mockTools>)
                ).map(([category, tools]) => (
                  <div key={category}>
                    <p className="text-sm text-gray-500 mb-2">{category}</p>
                    <div className="space-y-2">
                      {tools.map((tool) => (
                        <label
                          key={tool.id}
                          className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/50 cursor-pointer
                            hover:bg-slate-900/70 transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={selectedTools.includes(tool.id)}
                            onChange={() => handleToolToggle(tool.id)}
                            className="w-4 h-4 rounded text-amber-500 bg-slate-700 border-slate-600"
                          />
                          <span className="text-white">{tool.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-700">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600"
                >
                  取消
                </button>
                <button
                  onClick={handleSavePermission}
                  disabled={isUpdating}
                  className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                    hover:bg-amber-400 disabled:opacity-50"
                >
                  {isUpdating ? '保存中...' : '保存'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        title="确认修改权限"
        message={`确认修改该智能体的工具权限吗？将授予 ${confirmModal.toolIds.length} 个工具的访问权限。`}
        onConfirm={handleConfirmSave}
        onCancel={() => setConfirmModal({ isOpen: false, agentId: '', toolIds: [] })}
        isPending={isUpdating}
      />
    </div>
  );
}
