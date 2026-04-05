import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  BookmarkIcon,
  TagIcon,
  StarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { relationApi } from '@/api/relationApi';
import { useAppContextStore } from '@/store/appContextStore';
import { eventBus, EventTypes } from '@/services/eventBus';
import showToast from '@/utils/toast';

interface SaveMemoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
  taskTitle: string;
  taskContent?: string;
  teamId?: string;
}

const SaveMemoryModal: React.FC<SaveMemoryModalProps> = ({
  isOpen,
  onClose,
  taskId,
  taskTitle,
  taskContent = '',
  teamId,
}) => {
  const { currentTeam } = useAppContextStore();
  
  const [title, setTitle] = useState(taskTitle);
  const [content, setContent] = useState(taskContent.slice(0, 500));
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [importance, setImportance] = useState(3);
  const [isLoading, setIsLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim()) && tags.length < 5) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      showToast.error('请输入标题');
      return;
    }

    setIsLoading(true);
    try {
      await relationApi.saveTaskToMemory(taskId, {
        title,
        content,
        tags,
        importance,
      });
      
      setSaved(true);
      eventBus.emit(EventTypes.MEMORY_CREATED, { taskId, title });
      showToast.success('已保存到记忆系统');
      
      setTimeout(() => {
        onClose();
        setSaved(false);
      }, 1500);
    } catch (error) {
      showToast.error('保存失败');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <BookmarkIcon className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  存入记忆
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  保存关键结论，便于后续追溯
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <XMarkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="p-6 space-y-5">
            {saved ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1, type: 'spring' }}
                  className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircleIcon className="w-10 h-10 text-green-500" />
                </motion.div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  保存成功！
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                  可在记忆系统中查看
                </p>
              </motion.div>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <DocumentTextIcon className="w-4 h-4 inline mr-1" />
                    标题
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="记忆标题"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    关键内容
                  </label>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="提炼关键结论、决策过程、经验教训..."
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <TagIcon className="w-4 h-4 inline mr-1" />
                    标签 (最多5个)
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-sm flex items-center gap-1"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:text-red-500"
                        >
                          <XMarkIcon className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  {tags.length < 5 && (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                        placeholder="添加标签"
                        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      />
                      <button
                        onClick={handleAddTag}
                        className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200"
                      >
                        添加
                      </button>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <StarIcon className="w-4 h-4 inline mr-1" />
                    重要度
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <button
                        key={level}
                        onClick={() => setImportance(level)}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                          level <= importance
                            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-400'
                        }`}
                      >
                        {level} 星
                      </button>
                    ))}
                  </div>
                </div>

                {(teamId || currentTeam) && (
                  <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                    <p className="text-sm text-primary-700 dark:text-primary-300">
                      将关联到团队「{currentTeam?.name || '当前团队'}」
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {!saved && (
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={isLoading || !title.trim()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {isLoading ? '保存中...' : '保存记忆'}
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SaveMemoryModal;
