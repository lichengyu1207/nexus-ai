import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  DocumentDuplicateIcon,
  StarIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import type { WorkflowTemplate } from '../types';

interface TemplateMarketplaceProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (template: WorkflowTemplate) => void;
}

const MOCK_TEMPLATES: WorkflowTemplate[] = [
  {
    id: '1',
    name: '房产估值流程',
    description: '自动获取房产信息并进行估值分析',
    workflow: {
      name: '房产估值流程',
      version: 1,
      nodes: [],
      edges: [],
      triggers: [],
      published: true,
    },
    author: '系统管理员',
    downloads: 1234,
    rating: 4.5,
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    name: '风险评估报告',
    description: '生成房产风险评估报告',
    workflow: {
      name: '风险评估报告',
      version: 1,
      nodes: [],
      edges: [],
      triggers: [],
      published: true,
    },
    author: '系统管理员',
    downloads: 856,
    rating: 4.2,
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    name: '市场分析流程',
    description: '分析区域市场趋势和价格走势',
    workflow: {
      name: '市场分析流程',
      version: 1,
      nodes: [],
      edges: [],
      triggers: [],
      published: true,
    },
    author: '系统管理员',
    downloads: 567,
    rating: 4.0,
    createdAt: new Date().toISOString(),
  },
];

export function TemplateMarketplace({ isOpen, onClose, onImport }: TemplateMarketplaceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);

  const filteredTemplates = MOCK_TEMPLATES.filter((t) =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-slate-800 rounded-xl border border-slate-700/50 w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col"
        >
          <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
            <div className="flex items-center gap-2">
              <DocumentDuplicateIcon className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-semibold text-white">模板市场</h2>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 border-b border-slate-700/50">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索模板..."
                className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-2 gap-4">
              {filteredTemplates.map((template) => (
                <motion.div
                  key={template.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedTemplate(template)}
                  className={`
                    p-4 rounded-xl border cursor-pointer transition-colors
                    ${selectedTemplate?.id === template.id
                      ? 'bg-amber-500/10 border-amber-500/30'
                      : 'bg-slate-900/50 border-slate-700/30 hover:border-slate-600'
                    }
                  `}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-medium text-white">{template.name}</h3>
                    <div className="flex items-center gap-1">
                      <StarIcon className="w-3.5 h-3.5 text-amber-400" />
                      <span className="text-xs text-amber-400">{template.rating}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 mb-3 line-clamp-2">{template.description}</p>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{template.author}</span>
                    <span className="flex items-center gap-1">
                      <ArrowDownTrayIcon className="w-3 h-3" />
                      {template.downloads}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="p-4 border-t border-slate-700/50 flex items-center justify-end gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-700/50 text-white rounded-lg text-sm hover:bg-slate-700 transition-colors"
            >
              取消
            </button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => selectedTemplate && onImport(selectedTemplate)}
              disabled={!selectedTemplate}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${selectedTemplate
                  ? 'bg-amber-500 text-slate-900 hover:bg-amber-400'
                  : 'bg-slate-700/50 text-slate-400 cursor-not-allowed'
                }
              `}
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              导入模板
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default TemplateMarketplace;
