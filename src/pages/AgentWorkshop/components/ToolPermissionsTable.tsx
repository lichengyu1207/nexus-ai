import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { Tool } from '../types';
import { useTools, useUpdateToolPermission } from '../hooks/useTools';

interface ToolPermissionsTableProps {
  agentId: string;
  isAdmin: boolean;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const Toggle: React.FC<{
  enabled: boolean;
  onChange: () => void;
  disabled?: boolean;
}> = ({ enabled, onChange, disabled }) => (
  <button
    onClick={onChange}
    disabled={disabled}
    className={clsx(
      'relative w-11 h-6 rounded-full transition-colors duration-200',
      'focus:outline-none focus:ring-2 focus:ring-primary/50',
      enabled ? 'bg-primary' : 'bg-bg-tertiary',
      disabled && 'opacity-50 cursor-not-allowed'
    )}
    role="switch"
    aria-checked={enabled}
    aria-label={enabled ? '已启用' : '已禁用'}
  >
    <motion.span
      className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow"
      animate={{ x: enabled ? 20 : 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    />
  </button>
);

const EditModal: React.FC<{
  tool: Tool;
  isOpen: boolean;
  onClose: () => void;
  onSave: (parameters: Record<string, unknown>) => void;
}> = ({ tool, isOpen, onClose, onSave }) => {
  const [parameters, setParameters] = useState<Record<string, unknown>>(
    tool.parameters || {}
  );

  const handleSave = () => {
    onSave(parameters);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-bg-secondary border border-border-light rounded-xl p-6 w-full max-w-lg"
        >
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            编辑工具参数 - {tool.name}
          </h3>

          <div className="mb-4">
            <label className="block text-sm text-text-secondary mb-2">
              参数配置 (JSON)
            </label>
            <textarea
              value={JSON.stringify(parameters, null, 2)}
              onChange={(e) => {
                try {
                  setParameters(JSON.parse(e.target.value));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              className="w-full h-40 px-3 py-2 bg-bg-tertiary border border-border-light rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:border-primary/50"
              spellCheck={false}
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm bg-primary text-bg-primary rounded-lg hover:bg-primary-dark transition-colors"
            >
              保存
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const LoadingSkeleton: React.FC = () => (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="h-14 rounded-lg bg-bg-secondary/40 animate-pulse border border-border-light"
      />
    ))}
  </div>
);

export const ToolPermissionsTable: React.FC<ToolPermissionsTableProps> = ({
  agentId,
  isAdmin,
}) => {
  const { data: tools, isLoading, error } = useTools(agentId);
  const updatePermission = useUpdateToolPermission(agentId);

  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'callCount' | 'lastCalled'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const sortedTools = useMemo(() => {
    if (!tools) return [];
    return [...tools].sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'callCount':
          comparison = a.callCount - b.callCount;
          break;
        case 'lastCalled':
          comparison = new Date(a.lastCalled).getTime() - new Date(b.lastCalled).getTime();
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [tools, sortBy, sortOrder]);

  const handleToggle = (toolId: string, currentEnabled: boolean) => {
    updatePermission.mutate({ toolId, enabled: !currentEnabled });
  };

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  if (isLoading) {
    return (
      <div className="p-4">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-400">
        <p>加载工具权限失败</p>
      </div>
    );
  }

  if (!tools || tools.length === 0) {
    return (
      <div className="p-8 text-center text-text-secondary">
        <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p>暂无工具权限数据</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="overflow-x-auto flex-1">
        <table className="w-full">
          <thead className="sticky top-0 bg-bg-secondary/95 backdrop-blur-md border-b border-border-light">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-1">
                  工具名称
                  {sortBy === 'name' && (
                    <span className="text-primary">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                描述
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => handleSort('callCount')}
              >
                <div className="flex items-center gap-1">
                  调用次数
                  {sortBy === 'callCount' && (
                    <span className="text-primary">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => handleSort('lastCalled')}
              >
                <div className="flex items-center gap-1">
                  最近调用
                  {sortBy === 'lastCalled' && (
                    <span className="text-primary">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th scope="col" className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                状态
              </th>
              {isAdmin && (
                <th scope="col" className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                  操作
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-light">
            {sortedTools.map((tool) => (
              <motion.tr
                key={tool.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="hover:bg-bg-tertiary/30 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="font-medium text-text-primary">{tool.name}</span>
                </td>
                <td className="px-4 py-3 text-sm text-text-secondary max-w-xs truncate">
                  {tool.description}
                </td>
                <td className="px-4 py-3 text-sm text-text-secondary">
                  {tool.callCount.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-text-secondary">
                  {formatDate(tool.lastCalled)}
                </td>
                <td className="px-4 py-3 text-center">
                  <Toggle
                    enabled={tool.enabled}
                    onChange={() => handleToggle(tool.id, tool.enabled)}
                    disabled={!isAdmin}
                  />
                </td>
                {isAdmin && (
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => setEditingTool(tool)}
                      className="text-sm text-primary hover:text-primary-dark transition-colors"
                    >
                      编辑
                    </button>
                  </td>
                )}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingTool && (
        <EditModal
          tool={editingTool}
          isOpen={!!editingTool}
          onClose={() => setEditingTool(null)}
          onSave={(parameters) => {
            // Would call updateToolParameters mutation here
            console.log('Save parameters:', parameters);
          }}
        />
      )}
    </div>
  );
};

export default ToolPermissionsTable;
