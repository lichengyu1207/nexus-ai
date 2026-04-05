import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMCPTools } from '../hooks/useMCPTools';
import { ConfirmModal } from './ConfirmModal';
import type { AuthType } from '../types';

const authTypeConfig: Record<AuthType, string> = {
  none: '无认证',
  apiKey: 'API Key',
  oauth: 'OAuth',
};

export function MCPToolManagement() {
  const { tools, isLoading, createTool, deleteTool, toggleTool, isCreating, isDeleting, isToggling } = useMCPTools();
  const [searchText, setSearchText] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; toolId: string }>({
    isOpen: false,
    toolId: '',
  });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    endpoint: '',
    authType: 'none' as AuthType,
    parametersSchema: '',
  });

  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(searchText.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchText.toLowerCase())
  );

  const handleCreate = async () => {
    try {
      const schema = formData.parametersSchema
        ? JSON.parse(formData.parametersSchema)
        : undefined;
      await createTool({
        name: formData.name,
        description: formData.description,
        endpoint: formData.endpoint,
        authType: formData.authType,
        parametersSchema: schema,
      });
      setIsModalOpen(false);
      setFormData({
        name: '',
        description: '',
        endpoint: '',
        authType: 'none',
        parametersSchema: '',
      });
    } catch (e) {
      console.error('Failed to create tool:', e);
    }
  };

  const handleDelete = (toolId: string) => {
    setConfirmModal({ isOpen: true, toolId });
  };

  const handleConfirmDelete = async () => {
    await deleteTool(confirmModal.toolId);
    setConfirmModal({ isOpen: false, toolId: '' });
  };

  const handleToggle = async (toolId: string) => {
    await toggleTool(toolId);
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
        <h2 className="text-xl font-semibold text-white">MCP工具管理</h2>
        <p className="text-gray-400 text-sm mt-1">管理外部工具和API集成</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="搜索工具..."
            className="w-full px-4 py-2 pl-10 rounded-lg bg-slate-800 border border-slate-700
              text-white focus:outline-none focus:border-amber-500"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
            hover:bg-amber-400 transition-colors"
        >
          + 新建工具
        </button>
      </div>

      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-900/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">工具名称</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">描述</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">调用次数</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">认证方式</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">状态</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {filteredTools.map((tool) => (
              <motion.tr
                key={tool.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="hover:bg-slate-700/30 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="text-white font-medium">{tool.name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-400 text-sm truncate max-w-[200px] block">
                    {tool.description}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-amber-400">{tool.callCount.toLocaleString()}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-300">{authTypeConfig[tool.authType]}</span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      tool.enabled
                        ? 'text-green-400 bg-green-500/20'
                        : 'text-gray-400 bg-gray-500/20'
                    }`}
                  >
                    {tool.enabled ? '已启用' : '已禁用'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleToggle(tool.id)}
                      disabled={isToggling}
                      className="px-2 py-1 rounded text-xs bg-slate-700 text-gray-300
                        hover:bg-slate-600 transition-colors"
                    >
                      {tool.enabled ? '禁用' : '启用'}
                    </button>
                    <button
                      onClick={() => handleDelete(tool.id)}
                      disabled={isDeleting}
                      className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400
                        hover:bg-red-500/30 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      <AnimatePresence>
        {isModalOpen && (
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
              <h3 className="text-lg font-semibold text-white mb-4">新建工具</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">工具名称</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                      text-white focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                      text-white focus:outline-none focus:border-amber-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">调用地址</label>
                  <input
                    type="url"
                    value={formData.endpoint}
                    onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                      text-white focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">认证方式</label>
                  <select
                    value={formData.authType}
                    onChange={(e) => setFormData({ ...formData, authType: e.target.value as AuthType })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                      text-white focus:outline-none focus:border-amber-500"
                  >
                    <option value="none">无认证</option>
                    <option value="apiKey">API Key</option>
                    <option value="oauth">OAuth</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">参数定义 (JSON Schema)</label>
                  <textarea
                    value={formData.parametersSchema}
                    onChange={(e) => setFormData({ ...formData, parametersSchema: e.target.value })}
                    rows={4}
                    placeholder='{"type": "object", "properties": {...}}'
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                      text-white font-mono text-sm focus:outline-none focus:border-amber-500 resize-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-700">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={isCreating || !formData.name || !formData.endpoint}
                  className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                    hover:bg-amber-400 disabled:opacity-50"
                >
                  {isCreating ? '创建中...' : '创建'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        title="确认删除工具"
        message="删除后该工具将无法被智能体调用，此操作不可恢复。"
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmModal({ isOpen: false, toolId: '' })}
        isPending={isDeleting}
        isDanger
      />
    </div>
  );
}
