import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import taskApi, { CreateTaskRequest, Task } from '../../api/task';

interface TaskInputProps {
  onTaskCreated?: (task: Task) => void;
  placeholder?: string;
  popularTasks?: Array<{ title: string; description: string }>;
  autoFocus?: boolean;
  compact?: boolean;
}

const TaskInput: React.FC<TaskInputProps> = ({
  onTaskCreated,
  placeholder = '输入您的房产咨询需求，例如：深圳南山区100平米学区房，预算1000万',
  popularTasks = [],
  autoFocus = false,
  compact = false,
}) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [typingPlaceholder, setTypingPlaceholder] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const placeholders = [
    '深圳南山区学区房分析',
    '北京朝阳区写字楼评估',
    '上海浦东别墅市场趋势',
    '广州天河区投资回报分析',
  ];

  useEffect(() => {
    let charIndex = 0;
    let currentPlaceholder = placeholders[placeholderIndex];
    
    const typeInterval = setInterval(() => {
      if (charIndex <= currentPlaceholder.length) {
        setTypingPlaceholder(currentPlaceholder.substring(0, charIndex));
        charIndex++;
      } else {
        clearInterval(typeInterval);
        setTimeout(() => {
          setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
          charIndex = 0;
        }, 2000);
      }
    }, 100);

    return () => clearInterval(typeInterval);
  }, [placeholderIndex]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const taskData: CreateTaskRequest = {
        description: input.trim(),
        style: 'balanced',
      };

      const task = await taskApi.createTask(taskData);
      setInput('');
      onTaskCreated?.(task);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '创建任务失败，请重试';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, onTaskCreated]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        width: '100%',
        maxWidth: compact ? '100%' : '700px',
        margin: '0 auto',
      }}
    >
      <div
        style={{
          position: 'relative',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: compact ? '12px' : '20px',
          border: '1px solid rgba(212, 175, 55, 0.2)',
          backdropFilter: 'blur(10px)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: compact ? '8px 12px' : '12px 20px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            background: 'rgba(0, 0, 0, 0.2)',
          }}
        >
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#fbbf24' }} />
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e' }} />
          <span
            style={{
              marginLeft: '12px',
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '12px',
            }}
          >
            智能分析终端
          </span>
        </div>

        <div style={{ padding: compact ? '12px' : '20px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <span
              style={{
                color: '#D4AF37',
                fontFamily: 'monospace',
                fontSize: compact ? '14px' : '16px',
                marginTop: '8px',
              }}
            >
              $
            </span>
            <div style={{ flex: 1, position: 'relative' }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder={typingPlaceholder || placeholder}
                autoFocus={autoFocus}
                rows={compact ? 1 : 2}
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: '#fff',
                  fontSize: compact ? '14px' : '16px',
                  fontFamily: 'monospace',
                  resize: 'none',
                  lineHeight: 1.6,
                }}
              />
              {!input && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: '8px',
                    color: '#D4AF37',
                    fontSize: compact ? '14px' : '16px',
                    fontFamily: 'monospace',
                    pointerEvents: 'none',
                  }}
                >
                  ▋
                </motion.span>
              )}
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '16px',
            }}
          >
            <div style={{ display: 'flex', gap: '8px' }}>
              <span
                style={{
                  padding: '4px 8px',
                  background: 'rgba(212, 175, 55, 0.1)',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: 'rgba(255, 255, 255, 0.5)',
                }}
              >
                Enter 发送
              </span>
              <span
                style={{
                  padding: '4px 8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: 'rgba(255, 255, 255, 0.5)',
                }}
              >
                Shift+Enter 换行
              </span>
            </div>

            <motion.button
              onClick={handleSubmit}
              disabled={isLoading || !input.trim()}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{
                padding: compact ? '8px 16px' : '10px 24px',
                background: isLoading
                  ? 'rgba(212, 175, 55, 0.3)'
                  : 'linear-gradient(135deg, #D4AF37, #B8962E)',
                border: 'none',
                borderRadius: compact ? '8px' : '12px',
                color: '#0f172a',
                fontSize: compact ? '13px' : '14px',
                fontWeight: 600,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                opacity: !input.trim() ? 0.5 : 1,
              }}
            >
              {isLoading ? (
                <>
                  <motion.span
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ display: 'inline-block' }}
                  >
                    ⏳
                  </motion.span>
                  分析中...
                </>
              ) : (
                <>
                  <span>▶</span>
                  开始分析
                </>
              )}
            </motion.button>
          </div>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{
                padding: '12px 20px',
                background: 'rgba(239, 68, 68, 0.1)',
                borderTop: '1px solid rgba(239, 68, 68, 0.2)',
              }}
            >
              <span style={{ color: '#ef4444', fontSize: '13px' }}>⚠️ {error}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {showSuggestions && popularTasks.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            style={{
              marginTop: '12px',
              padding: '12px',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <span
              style={{
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: '12px',
                marginBottom: '8px',
                display: 'block',
              }}
            >
              💡 热门案例
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {popularTasks.map((task, index) => (
                <motion.div
                  key={index}
                  onClick={() => handleSuggestionClick(task.title)}
                  whileHover={{ background: 'rgba(212, 175, 55, 0.1)' }}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <span style={{ color: '#D4AF37', fontSize: '14px' }}>→</span>
                  <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '13px' }}>
                    {task.title}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default TaskInput;
