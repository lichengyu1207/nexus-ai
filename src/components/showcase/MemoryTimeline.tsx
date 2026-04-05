import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import memoryApi, { Memory, MemorySearchParams } from '../../api/memory';

interface MemoryTimelineProps {
  taskId?: string;
  onMemorySelect?: (memory: Memory) => void;
  onMemoryReplay?: (memory: Memory) => void;
  isActive?: boolean;
  compact?: boolean;
}

const TYPE_COLORS: Record<Memory['type'], string> = {
  event: '#3B82F6',
  fact: '#10B981',
  procedure: '#F59E0B',
  insight: '#8B5CF6',
};

const TYPE_LABELS: Record<Memory['type'], string> = {
  event: '事件',
  fact: '事实',
  procedure: '流程',
  insight: '洞察',
};

const MemoryTimeline: React.FC<MemoryTimelineProps> = ({
  taskId,
  onMemorySelect,
  onMemoryReplay,
  isActive = false,
  compact = false,
}) => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [filter, setFilter] = useState<Memory['type'] | 'all'>('all');
  const [minImportance, setMinImportance] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchMemories = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params: MemorySearchParams = {
        page: 1,
        pageSize: 50,
      };

      if (filter !== 'all') {
        params.type = filter;
      }
      if (minImportance > 0) {
        params.minImportance = minImportance;
      }

      const response = await memoryApi.getMemories(params);
      const sortedMemories = response.memories.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      setMemories(sortedMemories);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载记忆失败');
    } finally {
      setIsLoading(false);
    }
  }, [filter, minImportance]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const handleMemoryClick = useCallback((memory: Memory) => {
    setSelectedMemory(memory);
    onMemorySelect?.(memory);
  }, [onMemorySelect]);

  const handleMemoryDoubleClick = useCallback((memory: Memory) => {
    onMemoryReplay?.(memory);
  }, [onMemoryReplay]);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      const hours = Math.floor(diff / (1000 * 60 * 60));
      if (hours === 0) {
        const minutes = Math.floor(diff / (1000 * 60));
        return `${minutes}分钟前`;
      }
      return `${hours}小时前`;
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
  };

  const getNodeSize = (importance: number) => {
    const baseSize = compact ? 12 : 16;
    const maxSize = compact ? 24 : 32;
    return baseSize + (importance / 10) * (maxSize - baseSize);
  };

  if (isLoading) {
    return (
      <div style={{
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
      }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: '32px',
            height: '32px',
            border: '3px solid rgba(139, 92, 246, 0.2)',
            borderTopColor: '#8B5CF6',
            borderRadius: '50%',
            marginBottom: '12px',
          }}
        />
        <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '13px' }}>
          加载记忆时间轴...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'rgba(239, 68, 68, 0.1)',
        borderRadius: '12px',
      }}>
        <span style={{ fontSize: '32px', marginBottom: '8px' }}>⚠️</span>
        <span style={{ color: '#ef4444', fontSize: '14px' }}>{error}</span>
        <motion.button
          onClick={fetchMemories}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            marginTop: '12px',
            padding: '8px 16px',
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#ef4444',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          重试
        </motion.button>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        overflow: 'hidden',
      }}
    >
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(0, 0, 0, 0.2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '20px' }}>🧠</span>
          <h3 style={{ color: '#8B5CF6', fontSize: '16px', fontWeight: 600, margin: 0 }}>
            海马体记忆时间轴
          </h3>
          <span style={{
            padding: '2px 8px',
            background: 'rgba(139, 92, 246, 0.2)',
            borderRadius: '10px',
            color: '#8B5CF6',
            fontSize: '12px',
          }}>
            {memories.length} 条
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as Memory['type'] | 'all')}
            style={{
              padding: '4px 8px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '12px',
            }}
          >
            <option value="all">全部类型</option>
            <option value="event">事件</option>
            <option value="fact">事实</option>
            <option value="procedure">流程</option>
            <option value="insight">洞察</option>
          </select>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px' }}>
              重要度:
            </span>
            <input
              type="range"
              min="0"
              max="10"
              value={minImportance}
              onChange={(e) => setMinImportance(Number(e.target.value))}
              style={{ width: '60px' }}
            />
            <span style={{ color: '#8B5CF6', fontSize: '11px' }}>
              {minImportance}
            </span>
          </div>
        </div>
      </div>

      <div style={{
        padding: '20px',
        maxHeight: compact ? '300px' : '500px',
        overflow: 'auto',
      }}>
        <div style={{ position: 'relative', paddingLeft: '40px' }}>
          <div style={{
            position: 'absolute',
            left: '15px',
            top: 0,
            bottom: 0,
            width: '2px',
            background: 'linear-gradient(180deg, #8B5CF6, #3B82F6, #10B981)',
            borderRadius: '1px',
          }} />

          <AnimatePresence>
            {memories.map((memory, index) => {
              const isSelected = selectedMemory?.id === memory.id;
              const nodeSize = getNodeSize(memory.importance);
              const typeColor = TYPE_COLORS[memory.type];

              return (
                <motion.div
                  key={memory.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.03 }}
                  style={{
                    position: 'relative',
                    marginBottom: '16px',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleMemoryClick(memory)}
                  onDoubleClick={() => handleMemoryDoubleClick(memory)}
                >
                  <motion.div
                    style={{
                      position: 'absolute',
                      left: '-32px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: `${nodeSize}px`,
                      height: `${nodeSize}px`,
                      borderRadius: '50%',
                      background: typeColor,
                      boxShadow: `0 0 ${isActive ? '15px' : '8px'} ${typeColor}60`,
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                    }}
                    animate={isActive ? {
                      boxShadow: [
                        `0 0 8px ${typeColor}60`,
                        `0 0 20px ${typeColor}80`,
                        `0 0 8px ${typeColor}60`,
                      ],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity }}
                  />

                  <motion.div
                    style={{
                      padding: '12px 16px',
                      background: isSelected
                        ? 'rgba(139, 92, 246, 0.15)'
                        : 'rgba(255, 255, 255, 0.03)',
                      borderRadius: '12px',
                      border: `1px solid ${isSelected ? typeColor : 'rgba(255, 255, 255, 0.1)'}`,
                    }}
                    whileHover={{
                      background: 'rgba(255, 255, 255, 0.06)',
                      borderColor: typeColor,
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      marginBottom: '8px',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          padding: '2px 6px',
                          background: `${typeColor}20`,
                          borderRadius: '4px',
                          color: typeColor,
                          fontSize: '11px',
                          fontWeight: 500,
                        }}>
                          {TYPE_LABELS[memory.type]}
                        </span>
                        <span style={{
                          color: 'rgba(255, 255, 255, 0.5)',
                          fontSize: '11px',
                        }}>
                          重要度: {memory.importance}/10
                        </span>
                      </div>
                      <span style={{
                        color: 'rgba(255, 255, 255, 0.4)',
                        fontSize: '11px',
                      }}>
                        {formatTime(memory.createdAt)}
                      </span>
                    </div>

                    <p style={{
                      margin: 0,
                      color: 'rgba(255, 255, 255, 0.8)',
                      fontSize: '13px',
                      lineHeight: 1.6,
                    }}>
                      {memory.input}
                    </p>

                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        style={{
                          marginTop: '12px',
                          padding: '12px',
                          background: 'rgba(0, 0, 0, 0.2)',
                          borderRadius: '8px',
                          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                        }}
                      >
                        <div style={{
                          color: 'rgba(255, 255, 255, 0.5)',
                          fontSize: '11px',
                          marginBottom: '6px',
                        }}>
                          输出结果:
                        </div>
                        <p style={{
                          margin: 0,
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontSize: '12px',
                          lineHeight: 1.6,
                        }}>
                          {memory.output}
                        </p>

                        {memory.agents && memory.agents.length > 0 && (
                          <div style={{
                            marginTop: '8px',
                            display: 'flex',
                            gap: '6px',
                            flexWrap: 'wrap',
                          }}>
                            {memory.agents.map((agent) => (
                              <span
                                key={agent}
                                style={{
                                  padding: '2px 8px',
                                  background: 'rgba(212, 175, 55, 0.1)',
                                  borderRadius: '4px',
                                  color: '#D4AF37',
                                  fontSize: '10px',
                                }}
                              >
                                {agent}
                              </span>
                            ))}
                          </div>
                        )}

                        <div style={{
                          marginTop: '12px',
                          display: 'flex',
                          gap: '8px',
                        }}>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            style={{
                              padding: '6px 12px',
                              background: 'rgba(139, 92, 246, 0.2)',
                              border: '1px solid rgba(139, 92, 246, 0.3)',
                              borderRadius: '6px',
                              color: '#8B5CF6',
                              fontSize: '11px',
                              cursor: 'pointer',
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMemoryDoubleClick(memory);
                            }}
                          >
                            ▶ 记忆回放
                          </motion.button>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            style={{
                              padding: '6px 12px',
                              background: 'rgba(255, 255, 255, 0.1)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              borderRadius: '6px',
                              color: 'rgba(255, 255, 255, 0.7)',
                              fontSize: '11px',
                              cursor: 'pointer',
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              memoryApi.updateImportance(memory.id, 10);
                            }}
                          >
                            ⭐ 标记重要
                          </motion.button>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {memories.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              color: 'rgba(255, 255, 255, 0.5)',
            }}>
              <span style={{ fontSize: '48px', display: 'block', marginBottom: '12px' }}>📭</span>
              <p style={{ margin: 0, fontSize: '14px' }}>暂无记忆数据</p>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', opacity: 0.6 }}>
                开始分析任务后将自动生成记忆
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoryTimeline;
