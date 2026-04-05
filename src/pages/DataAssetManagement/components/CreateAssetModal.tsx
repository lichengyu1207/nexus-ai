import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { Asset, AssetType, DataSourceType } from '../types';
import { ASSET_TYPE_CONFIG, DATA_SOURCE_TYPE_CONFIG } from '../types';

export interface CreateAssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Asset>) => void;
  isLoading?: boolean;
  parentId?: string;
}

const initialFormData: Partial<Asset> & {
  config: {
    type: DataSourceType;
    connection: string;
    syncSchedule: string;
  };
} = {
  name: '',
  type: 'dataset',
  description: '',
  tags: [],
  config: {
    type: 'mysql',
    connection: '',
    syncSchedule: '',
  },
};

export function CreateAssetModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  parentId,
}: CreateAssetModalProps) {
  const [formData, setFormData] = useState(initialFormData);
  const [tagInput, setTagInput] = useState('');

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    if (name.startsWith('config.')) {
      const configKey = name.split('.')[1] as keyof typeof formData.config;
      setFormData((prev) => ({
        ...prev,
        config: {
          ...prev.config,
          [configKey]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags ?? []), tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((t) => t !== tag) ?? [],
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      parentId,
    });
  };

  const handleClose = () => {
    setFormData(initialFormData);
    setTagInput('');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={handleClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">新建资产</h2>
              <button
                onClick={handleClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  资产名称 <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  placeholder="输入资产名称"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  资产类型 <span className="text-red-400">*</span>
                </label>
                <select
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                >
                  {Object.entries(ASSET_TYPE_CONFIG).map(([key, config]) => (
                    <option key={key} value={key} className="bg-gray-800">
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  描述
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 resize-none"
                  placeholder="输入资产描述"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  标签
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                    className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    placeholder="输入标签后按回车添加"
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="px-3 py-2 bg-amber-500/20 text-amber-400 rounded-lg hover:bg-amber-500/30 transition-colors"
                  >
                    添加
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags?.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="hover:text-red-400"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {formData.type === 'datasource' && (
                <div className="space-y-4 p-3 bg-white/5 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-300">数据源配置</h3>

                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      数据源类型
                    </label>
                    <select
                      name="config.type"
                      value={formData.config.type}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    >
                      {Object.entries(DATA_SOURCE_TYPE_CONFIG).map(([key, config]) => (
                        <option key={key} value={key} className="bg-gray-800">
                          {config.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      连接字符串
                    </label>
                    <input
                      type="text"
                      name="config.connection"
                      value={formData.config.connection}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      placeholder="mysql://user:password@host:port/database"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      同步计划 (Cron 表达式)
                    </label>
                    <input
                      type="text"
                      name="config.syncSchedule"
                      value={formData.config.syncSchedule}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      placeholder="0 0 * * * (每天凌晨)"
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !formData.name}
                  className={`
                    flex-1 py-2 text-sm font-medium rounded-lg transition-colors
                    ${
                      isLoading || !formData.name
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-amber-500 text-gray-900 hover:bg-amber-400'
                    }
                  `}
                >
                  {isLoading ? '创建中...' : '创建资产'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
