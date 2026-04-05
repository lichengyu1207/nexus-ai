import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { AlertRule, AlertCondition } from '../types';
import { AVAILABLE_METRICS } from '../types';

interface AlertRuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AlertRuleFormData) => void;
  rule?: AlertRule | null;
  channels: { id: string; name: string }[];
  isLoading?: boolean;
}

export interface AlertRuleFormData {
  name: string;
  metric: string;
  condition: AlertCondition;
  threshold: number;
  duration: number;
  channels: string[];
  silenceMinutes: number;
}

export function AlertRuleModal({
  isOpen,
  onClose,
  onSubmit,
  rule,
  channels,
  isLoading,
}: AlertRuleModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<AlertRuleFormData>({
    defaultValues: {
      name: '',
      metric: '',
      condition: '>',
      threshold: 0,
      duration: 60,
      channels: [],
      silenceMinutes: 5,
    },
  });

  useEffect(() => {
    if (rule) {
      reset({
        name: rule.name,
        metric: rule.metric,
        condition: rule.condition,
        threshold: rule.threshold,
        duration: rule.duration,
        channels: rule.channels,
        silenceMinutes: rule.silenceMinutes,
      });
    } else {
      reset({
        name: '',
        metric: '',
        condition: '>',
        threshold: 0,
        duration: 60,
        channels: [],
        silenceMinutes: 5,
      });
    }
  }, [rule, reset]);

  const selectedChannels = watch('channels');

  const handleChannelToggle = (channelId: string) => {
    const newChannels = selectedChannels.includes(channelId)
      ? selectedChannels.filter((id) => id !== channelId)
      : [...selectedChannels, channelId];
    setValue('channels', newChannels);
  };

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
          className="bg-slate-800 border border-slate-700/50 rounded-xl w-full max-w-lg overflow-hidden"
        >
          <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
            <h2 className="text-lg font-semibold text-white">
              {rule ? '编辑告警规则' : '创建告警规则'}
            </h2>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="p-4 space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">规则名称</label>
              <input
                {...register('name', { required: '请输入规则名称' })}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                placeholder="输入规则名称"
              />
              {errors.name && (
                <p className="text-xs text-red-400 mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">监控指标</label>
              <select
                {...register('metric', { required: '请选择监控指标' })}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
              >
                <option value="">选择指标</option>
                {AVAILABLE_METRICS.map((metric) => (
                  <option key={metric.id} value={metric.id}>
                    {metric.name} ({metric.unit})
                  </option>
                ))}
              </select>
              {errors.metric && (
                <p className="text-xs text-red-400 mt-1">{errors.metric.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">条件</label>
                <select
                  {...register('condition')}
                  className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                >
                  <option value=">">大于</option>
                  <option value="<">小于</option>
                  <option value=">=">大于等于</option>
                  <option value="<=">小于等于</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">阈值</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('threshold', {
                    required: '请输入阈值',
                    valueAsNumber: true,
                  })}
                  className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                />
                {errors.threshold && (
                  <p className="text-xs text-red-400 mt-1">{errors.threshold.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">持续时间（秒）</label>
                <input
                  type="number"
                  {...register('duration', {
                    required: '请输入持续时间',
                    valueAsNumber: true,
                    min: { value: 0, message: '持续时间不能为负' },
                  })}
                  className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                />
                {errors.duration && (
                  <p className="text-xs text-red-400 mt-1">{errors.duration.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">静默时间（分钟）</label>
                <input
                  type="number"
                  {...register('silenceMinutes', {
                    required: '请输入静默时间',
                    valueAsNumber: true,
                    min: { value: 0, message: '静默时间不能为负' },
                  })}
                  className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">通知渠道</label>
              <div className="flex flex-wrap gap-2">
                {channels.map((channel) => (
                  <button
                    key={channel.id}
                    type="button"
                    onClick={() => handleChannelToggle(channel.id)}
                    className={`
                      px-3 py-1.5 rounded-lg text-sm transition-colors
                      ${selectedChannels.includes(channel.id)
                        ? 'bg-amber-500 text-slate-900'
                        : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
                      }
                    `}
                  >
                    {channel.name}
                  </button>
                ))}
                {channels.length === 0 && (
                  <span className="text-sm text-slate-500">暂无可用通知渠道</span>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-700/50">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-700/50 text-white rounded-lg text-sm hover:bg-slate-700 transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium hover:bg-amber-400 transition-colors disabled:opacity-50"
              >
                {isLoading ? '保存中...' : rule ? '更新' : '创建'}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default AlertRuleModal;
