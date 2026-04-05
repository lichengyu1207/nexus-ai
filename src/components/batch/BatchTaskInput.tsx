import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm, useFieldArray } from 'react-hook-form';
import {
  SparklesIcon,
  DocumentTextIcon,
  PlusIcon,
  TrashIcon,
  ArrowRightIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ArrowUpTrayIcon,
  XMarkIcon,
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

interface BatchTaskInputProps {
  onSubmit?: (taskIds: string[], parentId: string) => void;
  onCancel?: () => void;
}

const TASK_TYPES = [
  { value: 'property_analysis', label: '房产分析', icon: '🏠' },
  { value: 'policy_query', label: '政策查询', icon: '📋' },
  { value: 'mingpan', label: '命理咨询', icon: '🔮' },
  { value: 'emotion', label: '情感陪伴', icon: '💬' },
  { value: 'report_generation', label: '报告生成', icon: '📄' },
];

const TASK_PARAMS: Record<string, { name: string; label: string; type: string; required: boolean }[]> = {
  property_analysis: [
    { name: 'city', label: '城市', type: 'text', required: true },
    { name: 'district', label: '区域', type: 'text', required: false },
    { name: 'price_range', label: '预算', type: 'text', required: false },
    { name: 'area', label: '面积', type: 'text', required: false },
  ],
  policy_query: [
    { name: 'city', label: '城市', type: 'text', required: true },
    { name: 'policy_type', label: '政策类型', type: 'select', required: false },
  ],
  mingpan: [
    { name: 'birth_date', label: '出生日期', type: 'date', required: true },
    { name: 'birth_time', label: '出生时辰', type: 'text', required: false },
    { name: 'gender', label: '性别', type: 'select', required: false },
  ],
  emotion: [
    { name: 'topic', label: '话题', type: 'text', required: false },
  ],
  report_generation: [
    { name: 'task_id', label: '任务ID', type: 'text', required: true },
    { name: 'format', label: '格式', type: 'select', required: false },
  ],
};

const BatchTaskInput: React.FC<BatchTaskInputProps> = ({ onSubmit, onCancel }) => {
  const [inputMode, setInputMode] = useState<InputMode>('natural');
  const [naturalInput, setNaturalInput] = useState('');
  const [parsedTasks, setParsedTasks] = useState<ParsedTask[]>([]);
  const [isParsing, setIsParsing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const { register, control, handleSubmit, watch, reset } = useForm({
    defaultValues: {
      tasks: [{ task_type: 'property_analysis', params: {} }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'tasks',
  });

  const watchTasks = watch('tasks');

  const parseNaturalLanguage = useCallback(async () => {
    if (!naturalInput.trim()) {
      toast.error('请输入任务描述');
      return;
    }

    setIsParsing(true);
    try {
      const response = await api.post('/api/tasks/parse', {
        mode: 'natural_language',
        natural_language: { text: naturalInput },
      });

      setParsedTasks(response.data.tasks);
      setShowPreview(true);

      if (response.data.can_submit) {
        toast.success(`成功解析 ${response.data.tasks.length} 个任务`);
      } else {
        toast.warning('部分任务缺少必要参数，请补充');
      }
    } catch {
      toast.error('解析失败，请重试');
    } finally {
      setIsParsing(false);
    }
  }, [naturalInput]);

  const submitBatchTasks = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const response = await api.post('/api/tasks/batch', {
        mode: 'natural_language',
        natural_language: { text: naturalInput },
        skip_invalid: true,
      });

      toast.success(response.data.message);
      onSubmit?.(response.data.task_ids, response.data.parent_task_id);
      setShowPreview(false);
      setNaturalInput('');
      setParsedTasks([]);
    } catch {
      toast.error('提交失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  }, [naturalInput, onSubmit]);

  const submitStructuredTasks = useCallback(async (data: { tasks: Array<{ task_type: string; params: Record<string, unknown> }> }) => {
    setIsSubmitting(true);
    try {
      const response = await api.post('/api/tasks/batch', {
        mode: 'structured',
        structured_tasks: data.tasks,
        skip_invalid: true,
      });

      toast.success(response.data.message);
      onSubmit?.(response.data.task_ids, response.data.parent_task_id);
      reset();
    } catch {
      toast.error('提交失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  }, [onSubmit, reset]);

  const handleFileUpload = useCallback((file: File) => {
    setUploadFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        if (file.name.endsWith('.json')) {
          const tasks = JSON.parse(content);
          if (Array.isArray(tasks)) {
            reset({ tasks });
            toast.success(`已加载 ${tasks.length} 个任务`);
          }
        } else if (file.name.endsWith('.csv')) {
          const lines = content.split('\n').filter(Boolean);
          const headers = lines[0].split(',');
          const taskData = lines.slice(1).map((line) => {
            const values = line.split(',');
            const params: Record<string, string> = {};
            headers.forEach((h, i) => {
              params[h.trim()] = values[i]?.trim() || '';
            });
            return { task_type: 'property_analysis', params };
          });
          reset({ tasks: taskData });
          toast.success(`已加载 ${taskData.length} 个任务`);
        }
      } catch {
        toast.error('文件解析失败');
      }
    };
    reader.readAsText(file);
  }, [reset]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                批量任务创建
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                支持自然语言输入或结构化表单
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-xl p-1">
            <button
              onClick={() => setInputMode('natural')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                inputMode === 'natural'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              自然语言
            </button>
            <button
              onClick={() => setInputMode('structured')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                inputMode === 'structured'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              结构化输入
            </button>
          </div>
        </div>
      </div>

      <div className="p-6">
        <AnimatePresence mode="wait">
          {inputMode === 'natural' ? (
            <motion.div
              key="natural"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  输入任务描述
                </label>
                <textarea
                  value={naturalInput}
                  onChange={(e) => setNaturalInput(e.target.value)}
                  placeholder="例如：帮我分析深圳南山区的房价走势，顺便查一下杭州最近的政策，再给我算一下我的命盘事业运"
                  rows={4}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white placeholder-gray-400 resize-none"
                />
              </div>

              <div className="flex items-center gap-3">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={parseNaturalLanguage}
                  disabled={isParsing || !naturalInput.trim()}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isParsing ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                    />
                  ) : (
                    <SparklesIcon className="w-5 h-5" />
                  )}
                  解析任务
                </motion.button>

                <button
                  onClick={() => setNaturalInput('')}
                  className="px-4 py-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  清空
                </button>
              </div>

              <AnimatePresence>
                {showPreview && parsedTasks.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-6 space-y-4"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      解析结果预览
                    </h3>

                    <div className="space-y-3">
                      {parsedTasks.map((task, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className={`p-4 rounded-xl border ${
                            task.is_complete
                              ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                              : 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <span className="text-2xl">
                                {TASK_TYPES.find((t) => t.value === task.type)?.icon || '📝'}
                              </span>
                              <div>
                                <div className="font-medium text-gray-900 dark:text-white">
                                  {TASK_TYPES.find((t) => t.value === task.type)?.label || task.type}
                                </div>
                                <div className="text-sm text-gray-500">{task.span}</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {task.is_complete ? (
                                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                              ) : (
                                <ExclamationCircleIcon className="w-5 h-5 text-yellow-500" />
                              )}
                              <span className="text-xs text-gray-400">
                                {Math.round(task.confidence * 100)}%
                              </span>
                            </div>
                          </div>

                          {!task.is_complete && task.question && (
                            <div className="mt-3 p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg text-sm text-yellow-700 dark:text-yellow-300">
                              {task.question}
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => setShowPreview(false)}
                        className="px-4 py-2 text-gray-500 hover:text-gray-700 dark:text-gray-400"
                      >
                        取消
                      </button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={submitBatchTasks}
                        disabled={isSubmitting}
                        className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow disabled:opacity-50"
                      >
                        {isSubmitting ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                            className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                          />
                        ) : (
                          <ArrowRightIcon className="w-4 h-4" />
                        )}
                        提交任务
                      </motion.button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ) : (
            <motion.div
              key="structured"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <form onSubmit={handleSubmit(submitStructuredTasks)} className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <label className="relative cursor-pointer">
                      <input
                        type="file"
                        accept=".json,.csv"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileUpload(file);
                        }}
                      />
                      <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                        <ArrowUpTrayIcon className="w-4 h-4" />
                        导入文件
                      </div>
                    </label>
                    {uploadFile && (
                      <span className="text-sm text-gray-500">{uploadFile.name}</span>
                    )}
                  </div>

                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => append({ task_type: 'property_analysis', params: {} })}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg text-sm font-medium"
                  >
                    <PlusIcon className="w-4 h-4" />
                    添加任务
                  </motion.button>
                </div>

                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {fields.map((field, index) => (
                    <motion.div
                      key={field.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm font-medium text-gray-500">
                          任务 {index + 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">任务类型</label>
                          <select
                            {...register(`tasks.${index}.task_type`)}
                            className="w-full px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm"
                          >
                            {TASK_TYPES.map((type) => (
                              <option key={type.value} value={type.value}>
                                {type.icon} {type.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        {TASK_PARAMS[watchTasks?.[index]?.task_type || 'property_analysis']?.map((param) => (
                          <div key={param.name}>
                            <label className="block text-xs text-gray-500 mb-1">
                              {param.label}
                              {param.required && <span className="text-red-500">*</span>}
                            </label>
                            {param.type === 'select' ? (
                              <select
                                {...register(`tasks.${index}.params.${param.name}`)}
                                className="w-full px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm"
                              >
                                <option value="">请选择</option>
                                {param.name === 'policy_type' && (
                                  <>
                                    <option value="限购">限购</option>
                                    <option value="贷款">贷款</option>
                                    <option value="公积金">公积金</option>
                                    <option value="契税">契税</option>
                                  </>
                                )}
                                {param.name === 'gender' && (
                                  <>
                                    <option value="male">男</option>
                                    <option value="female">女</option>
                                  </>
                                )}
                                {param.name === 'format' && (
                                  <>
                                    <option value="pdf">PDF</option>
                                    <option value="html">HTML</option>
                                    <option value="markdown">Markdown</option>
                                  </>
                                )}
                              </select>
                            ) : (
                              <input
                                type={param.type === 'date' ? 'date' : 'text'}
                                {...register(`tasks.${index}.params.${param.name}`)}
                                className="w-full px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm"
                                placeholder={`输入${param.label}`}
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    type="button"
                    onClick={onCancel}
                    className="px-4 py-2 text-gray-500 hover:text-gray-700 dark:text-gray-400"
                  >
                    取消
                  </button>
                  <motion.button
                    type="submit"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={isSubmitting || fields.length === 0}
                    className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                      />
                    ) : (
                      <DocumentTextIcon className="w-4 h-4" />
                    )}
                    提交 {fields.length} 个任务
                  </motion.button>
                </div>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default BatchTaskInput;
