import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useMemoryDetail, useMemoryVersions } from '../hooks/useMemoryDetail';

interface MemoryDetailDrawerProps {
  memoryId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onNavigateToMemory?: (id: string) => void;
  onNavigateToTask?: (id: string) => void;
  onNavigateToAgent?: (id: string) => void;
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const LoadingState: React.FC = () => (
  <div className="flex items-center justify-center py-16">
    <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
  </div>
);

const ErrorState: React.FC = () => (
  <div className="text-center py-16 text-red-400">
    <p>加载记忆详情失败</p>
  </div>
);

export const MemoryDetailDrawer: React.FC<MemoryDetailDrawerProps> = ({
  memoryId,
  isOpen,
  onClose,
  onNavigateToMemory,
  onNavigateToTask,
  onNavigateToAgent,
}) => {
  const { data: memory, isLoading, error } = useMemoryDetail(memoryId);
  const { data: versions } = useMemoryVersions(memoryId);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-xl bg-bg-secondary border-l border-border-light z-50 flex flex-col"
          >
            <div className="flex items-center justify-between p-4 border-b border-border-light">
              <h3 className="text-lg font-semibold text-text-primary">记忆详情</h3>
              <button
                onClick={onClose}
                className="p-2 text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-bg-tertiary/50"
                aria-label="关闭"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
              {isLoading && <LoadingState />}
              {error && <ErrorState />}

              {memory && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">
                        {memory.type === 'episodic' && '📅'}
                        {memory.type === 'semantic' && '🧠'}
                        {memory.type === 'procedural' && '⚙️'}
                      </span>
                      <span className={clsx(
                        'text-xs px-2 py-0.5 rounded-full',
                        memory.type === 'episodic' && 'text-blue-400 bg-blue-400/10',
                        memory.type === 'semantic' && 'text-purple-400 bg-purple-400/10',
                        memory.type === 'procedural' && 'text-green-400 bg-green-400/10'
                      )}>
                        {memory.type === 'episodic' && '情景记忆'}
                        {memory.type === 'semantic' && '语义记忆'}
                        {memory.type === 'procedural' && '程序性记忆'}
                      </span>
                      <div className="ml-auto flex items-center gap-0.5">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <span
                            key={star}
                            className={clsx(
                              'text-sm',
                              star <= memory.importance ? 'text-primary' : 'text-text-secondary/30'
                            )}
                          >
                            ★
                          </span>
                        ))}
                      </div>
                    </div>

                    {memory.title && (
                      <h2 className="text-xl font-semibold text-text-primary mb-2">
                        {memory.title}
                      </h2>
                    )}

                    <div className="flex items-center gap-4 text-xs text-text-secondary">
                      <span>创建于 {formatDate(memory.createdAt)}</span>
                      <span>版本 {memory.version}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                      内容
                    </h4>
                    <div className="p-4 bg-bg-tertiary/30 rounded-lg">
                      <pre className="text-sm text-text-primary whitespace-pre-wrap font-sans">
                        {memory.content}
                      </pre>
                    </div>
                  </div>

                  {memory.tags.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        标签
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {memory.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-3 py-1 text-sm bg-primary/10 text-primary rounded-full"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {(memory.associations.memories.length > 0 ||
                    memory.associations.tasks.length > 0 ||
                    memory.associations.agents.length > 0) && (
                    <div>
                      <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        关联网络
                      </h4>
                      <div className="space-y-2">
                        {memory.associations.memories.length > 0 && (
                          <div>
                            <span className="text-xs text-text-secondary">关联记忆:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {memory.associations.memories.slice(0, 5).map((id) => (
                                <button
                                  key={id}
                                  onClick={() => onNavigateToMemory?.(id)}
                                  className="text-xs px-2 py-1 bg-bg-tertiary/50 text-text-primary rounded hover:bg-primary/10 hover:text-primary transition-colors"
                                >
                                  {id.slice(0, 8)}...
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        {memory.associations.tasks.length > 0 && (
                          <div>
                            <span className="text-xs text-text-secondary">关联任务:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {memory.associations.tasks.slice(0, 5).map((id) => (
                                <button
                                  key={id}
                                  onClick={() => onNavigateToTask?.(id)}
                                  className="text-xs px-2 py-1 bg-bg-tertiary/50 text-text-primary rounded hover:bg-primary/10 hover:text-primary transition-colors"
                                >
                                  {id.slice(0, 8)}...
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        {memory.associations.agents.length > 0 && (
                          <div>
                            <span className="text-xs text-text-secondary">关联智能体:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {memory.associations.agents.slice(0, 5).map((id) => (
                                <button
                                  key={id}
                                  onClick={() => onNavigateToAgent?.(id)}
                                  className="text-xs px-2 py-1 bg-bg-tertiary/50 text-text-primary rounded hover:bg-primary/10 hover:text-primary transition-colors"
                                >
                                  {id}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {versions && versions.length > 1 && (
                    <div>
                      <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                        版本历史
                      </h4>
                      <div className="space-y-2">
                        {versions.map((version, index) => (
                          <div
                            key={version.version}
                            className={clsx(
                              'p-3 rounded-lg border',
                              version.version === memory.version
                                ? 'bg-primary/10 border-primary/30'
                                : 'bg-bg-tertiary/30 border-border-light'
                            )}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-text-primary">
                                版本 {version.version}
                              </span>
                              <span className="text-xs text-text-secondary">
                                {formatDate(version.updatedAt)}
                              </span>
                            </div>
                            {version.changeSummary && (
                              <p className="text-xs text-text-secondary">
                                {version.changeSummary}
                              </p>
                            )}
                            <p className="text-xs text-text-secondary mt-1">
                              修改者: {version.updatedBy}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </div>

            {memory && (
              <div className="p-4 border-t border-border-light flex gap-2">
                <button
                  className="flex-1 py-2 text-sm text-text-secondary border border-border-light rounded-lg hover:border-primary/30 hover:text-primary transition-colors"
                >
                  导出
                </button>
                <button
                  className="flex-1 py-2 text-sm bg-primary text-bg-primary rounded-lg hover:bg-primary-dark transition-colors"
                >
                  编辑
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MemoryDetailDrawer;
