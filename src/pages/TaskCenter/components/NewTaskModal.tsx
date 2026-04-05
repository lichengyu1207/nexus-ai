import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { NewTaskPayload } from '../types';

interface NewTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: NewTaskPayload) => void;
  isPending: boolean;
  agents: { id: string; name: string }[];
}

export function NewTaskModal({
  isOpen,
  onClose,
  onSubmit,
  isPending,
  agents,
}: NewTaskModalProps) {
  const [name, setName] = useState('');
  const [agentId, setAgentId] = useState('');
  const [inputParams, setInputParams] = useState('{}');
  const [scheduledTime, setScheduledTime] = useState('');
  const [paramsError, setParamsError] = useState('');

  const handleSubmit = () => {
    if (!name.trim() || !agentId) {
      return;
    }

    let parsedParams = {};
    if (inputParams.trim()) {
      try {
        parsedParams = JSON.parse(inputParams);
        setParamsError('');
      } catch {
        setParamsError('JSON 格式错误');
        return;
      }
    }

    onSubmit({
      name: name.trim(),
      agentId,
      inputParams: parsedParams,
      scheduledTime: scheduledTime || undefined,
    });

    resetForm();
  };

  const resetForm = () => {
    setName('');
    setAgentId('');
    setInputParams('{}');
    setScheduledTime('');
    setParamsError('');
  };

  const handleClose = () => {
    resetForm();
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
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
              w-full max-w-lg p-6 rounded-xl bg-slate-800 border border-slate-700 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-task-title"
          >
            <h2 id="new-task-title" className="text-lg font-semibold text-white mb-4">
              新建任务
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  任务名称 <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="请输入任务名称"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                    text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  选择智能体 <span className="text-red-400">*</span>
                </label>
                <select
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                    text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="">请选择智能体</option>
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  输入参数 (JSON)
                </label>
                <textarea
                  value={inputParams}
                  onChange={(e) => setInputParams(e.target.value)}
                  rows={4}
                  placeholder='{"key": "value"}'
                  className={`w-full px-3 py-2 rounded-lg bg-slate-900 border
                    text-white font-mono text-sm focus:outline-none resize-none
                    ${paramsError ? 'border-red-500' : 'border-slate-700 focus:border-amber-500'}`}
                />
                {paramsError && (
                  <p className="text-red-400 text-xs mt-1">{paramsError}</p>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  调度时间（可选）
                </label>
                <input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                    text-white focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={handleClose}
                disabled={isPending}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
                  hover:bg-slate-600 disabled:opacity-50 transition-colors"
              >
                取消
              </button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={isPending || !name.trim() || !agentId}
                className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                  hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isPending ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    创建中...
                  </span>
                ) : (
                  '创建任务'
                )}
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
