import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import {
  XMarkIcon,
  CodeBracketIcon,
  InformationCircleIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import type { WorkflowNode, NodeType, ErrorHandlingStrategy } from '../types';
import { useWorkflowStore } from '../hooks/useWorkflow';

interface NodeConfigPanelProps {
  node: WorkflowNode | null;
  onUpdate: (id: string, data: Partial<WorkflowNode['data']>) => void;
  onClose: () => void;
}

const NODE_TYPE_LABELS: Record<NodeType, string> = {
  agent: '智能体节点',
  tool: '工具节点',
  condition: '条件分支',
  loop: '循环节点',
  subflow: '子流程',
  trigger: '触发器',
};

const ERROR_HANDLING_OPTIONS: { value: ErrorHandlingStrategy; label: string }[] = [
  { value: 'fail', label: '失败终止' },
  { value: 'retry', label: '重试' },
  { value: 'ignore', label: '忽略继续' },
];

export function NodeConfigPanel({ node, onUpdate, onClose }: NodeConfigPanelProps) {
  const [isJsonMode, setIsJsonMode] = useState(false);
  const [jsonValue, setJsonValue] = useState('');

  const { register, handleSubmit, reset, watch, setValue } = useForm({
    defaultValues: {
      label: node?.data.label || '',
      config: JSON.stringify(node?.data.config || {}, null, 2),
      errorHandling: node?.data.errorHandling || 'fail',
    },
  });

  useEffect(() => {
    if (node) {
      reset({
        label: node.data.label,
        config: JSON.stringify(node.data.config, null, 2),
        errorHandling: node.data.errorHandling || 'fail',
      });
      setJsonValue(JSON.stringify(node.data.config, null, 2));
    }
  }, [node, reset]);

  const onSubmit = (data: { label: string; config: string; errorHandling: ErrorHandlingStrategy }) => {
    if (node) {
      try {
        const parsedConfig = JSON.parse(data.config);
        onUpdate(node.id, {
          label: data.label,
          config: parsedConfig,
          errorHandling: data.errorHandling,
        });
      } catch {
        onUpdate(node.id, {
          label: data.label,
          errorHandling: data.errorHandling,
        });
      }
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonValue(value);
    try {
      JSON.parse(value);
      setValue('config', value);
    } catch {
      // Invalid JSON, keep as string
    }
  };

  if (!node) {
    return (
      <div className="w-80 bg-slate-800/50 backdrop-blur-sm border-l border-slate-700/50 flex items-center justify-center">
        <p className="text-slate-400">选择节点查看配置</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="w-80 bg-slate-800/50 backdrop-blur-sm border-l border-slate-700/50 flex flex-col"
    >
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <InformationCircleIcon className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-medium text-white">节点配置</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsJsonMode(!isJsonMode)}
            className={`p-1.5 rounded text-xs ${isJsonMode ? 'text-amber-400 bg-amber-500/20' : 'text-slate-400 hover:text-white'}`}
          >
            <CodeBracketIcon className="w-3.5 h-3.5" />
          </button>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isJsonMode ? (
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">配置 (JSON)</label>
              <textarea
                value={jsonValue}
                onChange={(e) => handleJsonChange(e.target.value)}
                className="w-full h-48 px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-amber-500/50"
                placeholder='{"key": "value"}'
              />
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">节点名称</label>
              <input
                {...register('label')}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                placeholder="输入节点名称"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">节点类型</label>
              <div className="px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-slate-300">
                {NODE_TYPE_LABELS[node.type]}
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">错误处理</label>
              <div className="grid grid-cols-3 gap-2">
                {ERROR_HANDLING_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setValue('errorHandling', opt.value)}
                    className={`
                      px-3 py-2 rounded-lg text-sm transition-colors
                      ${watch('errorHandling') === opt.value
                        ? 'bg-amber-500 text-slate-900'
                        : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
                      }
                    `}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">配置 (JSON)</label>
              <textarea
                {...register('config')}
                rows={4}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-amber-500/50"
                placeholder='{"key": "value"}'
              />
            </div>
          </form>
        )}
      </div>

      <div className="p-4 border-t border-slate-700/50">
        <button
          type="button"
          onClick={() => useWorkflowStore.getState().deleteNode(node.id)}
          className="flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-500/20 rounded-lg text-sm transition-colors"
        >
          <TrashIcon className="w-4 h-4" />
          删除节点
        </button>
      </div>
    </motion.div>
  );
}

export default NodeConfigPanel;
