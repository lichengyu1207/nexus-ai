import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChatBubbleLeftRightIcon,
  ListBulletIcon,
  DocumentTextIcon,
  SparklesIcon,
  ArrowRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import toast from '@/utils/toast';

type InputMode = 'natural' | 'structured';

interface ParsedTask {
  type: string;
  confidence: number;
  span: string;
  params: Record<string, unknown>;
  missing_params: string[];
  question: string;
  is_complete: boolean;
}

interface InputModeSwitcherProps {
  onParsed?: (tasks: ParsedTask[], dagInfo?: Record<string, unknown>) => void;
  onSubmit?: (tasks: ParsedTask[]) => void;
  placeholder?: string;
  maxTasks?: number;
}

const MODE_CONFIG = {
  natural: {
    icon: ChatBubbleLeftRightIcon,
    label: '自然语言',
    description: '用日常语言描述您的需求',
    placeholder: '例如：帮我分析深圳南山区的房价走势，顺便查一下杭州最近的政策',
  },
  structured: {
    icon: ListBulletIcon,
    label: '结构化输入',
    description: '使用表单精确指定任务参数',
    placeholder: '填写任务类型和参数',
  },
};

const TASK_TYPE_OPTIONS = [
  { value: 'property_analysis', label: '房产分析', icon: '🏠' },
  { value: 'policy_query', label: '政策查询', icon: '📋' },
  { value: 'mingpan', label: '命理咨询', icon: '🔮' },
  { value: 'emotion', label: '情感陪伴', icon: '💬' },
  { value: 'report_generation', label: '报告生成', icon: '📄' },
];

const InputModeSwitcher: React.FC<InputModeSwitcherProps> = ({
  onParsed,
  onSubmit,
  placeholder,
  maxTasks = 10,
}) => {
  const [mode, setMode] = useState<InputMode>('natural');
  const [naturalInput, setNaturalInput] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [parsedTasks, setParsedTasks] = useState<ParsedTask[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [dagInfo, setDagInfo] = useState<Record<string, unknown> | null>(null);

  const [structuredTasks, setStructuredTasks] = useState([
    { id: '1', type: 'property_analysis', params: {} },
  ]);

  const handleModeChange = (newMode: InputMode) => {
    setMode(newMode);
    setParsedTasks([]);
    setShowPreview(false);
    setDagInfo(null);
  };

  const handleParse = useCallback(async () => {
    if (!naturalInput.trim()) {
      toast.warning('请输入您的需求');
      return;
    }

    setIsParsing(true);
    try {
      const response = await api.post('/api/three-provinces/zhongshu/parse_batch', {
        text: naturalInput,
        user_id: 'current_user',
      });

      const tasks = response.data.tasks || [];
      const dag = response.data.dag_info || null;

      setParsedTasks(tasks);
      setDagInfo(dag);
      setShowPreview(true);

      if (tasks.length === 0) {
        toast.warning('未能识别出有效任务，请尝试更具体的描述');
      } else {
        toast.success(`识别出 ${tasks.length} 个任务`);
      }

      onParsed?.(tasks, dag);
    } catch (error) {
      toast.error('解析失败，请稍后重试');
    } finally {
      setIsParsing(false);
    }
  }, [naturalInput, onParsed]);

  const handleAddStructuredTask = () => {
    if (structuredTasks.length >= maxTasks) {
      toast.warning(`最多支持 ${maxTasks} 个任务`);
      return;
    }
    setStructuredTasks([
      ...structuredTasks,
      { id: Date.now().toString(), type: 'property_analysis', params: {} },
    ]);
  };

  const handleRemoveStructuredTask = (id: string) => {
    if (structuredTasks.length <= 1) return;
    setStructuredTasks(structuredTasks.filter(t => t.id !== id));
  };

  const handleTaskTypeChange = (id: string, type: string) => {
    setStructuredTasks(
      structuredTasks.map(t => (t.id === id ? { ...t, type, params: {} } : t))
    );
  };

  const handleTaskParamChange = (id: string, key: string, value: unknown) => {
    setStructuredTasks(
      structuredTasks.map(t =>
        t.id === id ? { ...t, params: { ...t.params, [key]: value } } : t
      )
    );
  };

  const handleSubmit = () => {
    const tasks = mode === 'natural' ? parsedTasks : structuredTasks.map(t => ({
      type: t.type,
      confidence: 1,
      span: '',
      params: t.params,
      missing_params: [],
      question: '',
      is_complete: true,
    }));

    if (tasks.length === 0) {
      toast.warning('请先添加任务');
      return;
    }

    onSubmit?.(tasks);
  };

  const renderNaturalInput = () => (
    <div className="space-y-4">
      <div className="relative">
        <textarea
          value={naturalInput}
          onChange={(e) => setNaturalInput(e.target.value)}
          placeholder={placeholder || MODE_CONFIG.natural.placeholder}
          className="w-full px-4 py-3 pr-24 border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900 dark:text-white placeholder-gray-400 bg-white dark:bg-gray-800"
          rows={4}
        />
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleParse}
          disabled={isParsing || !naturalInput.trim()}
          className="absolute right-3 bottom-3 flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-medium hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isParsing ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
            />
          ) : (
            <SparklesIcon className="w-4 h-4" />
          )}
          解析
        </motion.button>
      </div>

      <AnimatePresence>
        {showPreview && parsedTasks.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  任务预览
                </h4>
                {dagInfo && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    执行层级: {(dagInfo as Record<string, unknown[]>).execution_levels?.length || 1}
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {parsedTasks.map((task, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">
                        {TASK_TYPE_OPTIONS.find(t => t.value === task.type)?.icon || '📌'}
                      </span>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white text-sm">
                          {TASK_TYPE_OPTIONS.find(t => t.value === task.type)?.label || task.type}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {task.span}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {task.is_complete ? (
                        <span className="text-xs text-green-500">完整</span>
                      ) : (
                        <span className="text-xs text-orange-500">
                          缺参数: {task.missing_params.join(', ')}
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        {Math.round(task.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  const renderStructuredInput = () => (
    <div className="space-y-4">
      {structuredTasks.map((task, index) => (
        <motion.div
          key={task.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
              任务 {index + 1}
            </span>
            {structuredTasks.length > 1 && (
              <button
                onClick={() => handleRemoveStructuredTask(task.id)}
                className="text-sm text-red-500 hover:text-red-600"
              >
                删除
              </button>
            )}
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                任务类型
              </label>
              <select
                value={task.type}
                onChange={(e) => handleTaskTypeChange(task.id, e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                {TASK_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.icon} {option.label}
                  </option>
                ))}
              </select>
            </div>

            {task.type === 'property_analysis' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    城市
                  </label>
                  <input
                    type="text"
                    placeholder="如：深圳"
                    onChange={(e) => handleTaskParamChange(task.id, 'city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    区域
                  </label>
                  <input
                    type="text"
                    placeholder="如：南山区"
                    onChange={(e) => handleTaskParamChange(task.id, 'district', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            )}

            {task.type === 'mingpan' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    出生日期
                  </label>
                  <input
                    type="date"
                    onChange={(e) => handleTaskParamChange(task.id, 'birth_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    出生时辰
                  </label>
                  <select
                    onChange={(e) => handleTaskParamChange(task.id, 'birth_time', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="">请选择</option>
                    <option value="子">子时 (23:00-01:00)</option>
                    <option value="丑">丑时 (01:00-03:00)</option>
                    <option value="寅">寅时 (03:00-05:00)</option>
                    <option value="卯">卯时 (05:00-07:00)</option>
                    <option value="辰">辰时 (07:00-09:00)</option>
                    <option value="巳">巳时 (09:00-11:00)</option>
                    <option value="午">午时 (11:00-13:00)</option>
                    <option value="未">未时 (13:00-15:00)</option>
                    <option value="申">申时 (15:00-17:00)</option>
                    <option value="酉">酉时 (17:00-19:00)</option>
                    <option value="戌">戌时 (19:00-21:00)</option>
                    <option value="亥">亥时 (21:00-23:00)</option>
                  </select>
                </div>
              </div>
            )}

            {task.type === 'policy_query' && (
              <div>
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                  城市
                </label>
                <input
                  type="text"
                  placeholder="如：杭州"
                  onChange={(e) => handleTaskParamChange(task.id, 'city', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
            )}
          </div>
        </motion.div>
      ))}

      <button
        onClick={handleAddStructuredTask}
        className="w-full py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-gray-500 dark:text-gray-400 hover:border-blue-500 hover:text-blue-500 transition-colors"
      >
        + 添加任务
      </button>
    </div>
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {(['natural', 'structured'] as InputMode[]).map((m) => {
            const config = MODE_CONFIG[m];
            const Icon = config.icon;
            const isActive = mode === m;

            return (
              <button
                key={m}
                onClick={() => handleModeChange(m)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-blue-500 text-white shadow-lg'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{config.label}</span>
              </button>
            );
          })}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 text-center">
          {MODE_CONFIG[mode].description}
        </p>
      </div>

      <div className="p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0, x: mode === 'natural' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: mode === 'natural' ? 20 : -20 }}
            transition={{ duration: 0.2 }}
          >
            {mode === 'natural' ? renderNaturalInput() : renderStructuredInput()}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="px-4 pb-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSubmit}
          className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow"
        >
          <DocumentTextIcon className="w-5 h-5" />
          提交任务
          <ArrowRightIcon className="w-4 h-4" />
        </motion.button>
      </div>
    </div>
  );
};

export default InputModeSwitcher;
