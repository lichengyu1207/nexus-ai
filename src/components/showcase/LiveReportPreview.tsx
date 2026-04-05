import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import taskApi, { Task, TaskResult, ChartData } from '../../api/task';
import TypingQueue, { TypingQueueItem } from '../reportGenerator/TypingQueue';
import ProgressiveChart from '../reportGenerator/ProgressiveChart';

interface LiveReportPreviewProps {
  taskId: string;
  onComplete?: () => void;
  compact?: boolean;
}

const LiveReportPreview: React.FC<LiveReportPreviewProps> = ({
  taskId,
  onComplete,
  compact = false,
}) => {
  const [task, setTask] = useState<Task | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const fetchTask = async () => {
      try {
        setIsLoading(true);
        const taskData = await taskApi.getTask(taskId);
        setTask(taskData);

        if (taskData.status === 'completed' && taskData.result) {
          setResult(taskData.result);
          onComplete?.();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载报告失败');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTask();

    const pollInterval = setInterval(async () => {
      if (task?.status !== 'completed') {
        try {
          const status = await taskApi.getTaskStatus(taskId);
          setProgress(status.progress);

          if (status.status === 'completed') {
            const taskData = await taskApi.getTask(taskId);
            setTask(taskData);
            if (taskData.result) {
              setResult(taskData.result);
            }
            onComplete?.();
            clearInterval(pollInterval);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [taskId, onComplete, task?.status]);

  const typingQueueItems = useMemo((): TypingQueueItem[] => {
    if (!result) return [];

    const items: TypingQueueItem[] = [];

    items.push({
      id: 'report-title',
      text: task?.title || '房产分析报告',
      type: 'title',
      speed: 30,
    });

    if (result.summary) {
      items.push({
        id: 'report-summary',
        text: result.summary,
        type: 'summary',
        speed: 20,
      });
    }

    result.findings.forEach((finding, index) => {
      items.push({
        id: `finding-${index}`,
        text: finding,
        type: 'insight',
        speed: 25,
      });
    });

    return items;
  }, [result, task?.title]);

  const handleProgress = useCallback((current: number, total: number) => {
    setProgress((current / total) * 100);
  }, []);

  const handleTypingComplete = useCallback(() => {
    setIsPlaying(false);
  }, []);

  if (isLoading) {
    return (
      <div style={{
        padding: '40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '16px',
      }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(212, 175, 55, 0.2)',
            borderTopColor: '#D4AF37',
            borderRadius: '50%',
            marginBottom: '16px',
          }}
        />
        <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '14px' }}>
          正在加载报告...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'rgba(239, 68, 68, 0.1)',
        borderRadius: '16px',
        border: '1px solid rgba(239, 68, 68, 0.3)',
      }}>
        <span style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</span>
        <span style={{ color: '#ef4444', fontSize: '16px', marginBottom: '8px' }}>
          加载失败
        </span>
        <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '13px' }}>
          {error}
        </span>
      </div>
    );
  }

  if (!result && task?.status !== 'completed') {
    return (
      <div style={{
        padding: '40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '16px',
      }}>
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{ fontSize: '48px', marginBottom: '16px' }}
        >
          📝
        </motion.div>
        <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '16px', marginBottom: '8px' }}>
          报告生成中...
        </span>
        <div style={{
          width: '200px',
          height: '4px',
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '2px',
          overflow: 'hidden',
        }}>
          <motion.div
            style={{
              height: '100%',
              background: 'linear-gradient(90deg, #D4AF37, #F59E0B)',
            }}
            animate={{ width: `${progress}%` }}
          />
        </div>
        <span style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: '12px', marginTop: '8px' }}>
          {Math.round(progress)}% 完成
        </span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <motion.div
            animate={{ rotate: isPlaying ? 360 : 0 }}
            transition={{ duration: 2, repeat: isPlaying ? Infinity : 0, ease: 'linear' }}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
            }}
          >
            📊
          </motion.div>
          <div>
            <h3 style={{ color: '#fff', margin: 0, fontSize: '16px', fontWeight: 600 }}>
              实时报告预览
            </h3>
            <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '12px' }}>
              {isPlaying ? '生成中...' : '已完成'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            style={{
              padding: '4px 8px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '12px',
            }}
          >
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>
          <motion.button
            onClick={() => setIsPlaying(!isPlaying)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: '6px 12px',
              background: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              border: `1px solid ${isPlaying ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
              borderRadius: '6px',
              color: isPlaying ? '#ef4444' : '#10B981',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            {isPlaying ? '⏸ 暂停' : '▶ 播放'}
          </motion.button>
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        <AnimatePresence mode="wait">
          {typingQueueItems.length > 0 && (
            <motion.div
              key="typing-queue"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <TypingQueue
                items={typingQueueItems}
                isPlaying={isPlaying}
                speed={speed}
                onProgress={handleProgress}
                onComplete={handleTypingComplete}
                renderTitle={(text, isTyping) => (
                  <h1 style={{
                    color: '#D4AF37',
                    fontSize: compact ? '20px' : '24px',
                    fontWeight: 700,
                    textAlign: 'center',
                    margin: 0,
                    textShadow: '0 0 20px rgba(212, 175, 55, 0.3)',
                  }}>
                    {text}
                    {isTyping && (
                      <motion.span
                        animate={{ opacity: [0, 1, 1, 0] }}
                        transition={{ duration: 0.6, repeat: Infinity }}
                        style={{ marginLeft: '2px', color: '#D4AF37' }}
                      >
                        |
                      </motion.span>
                    )}
                  </h1>
                )}
                renderSummary={(text, isTyping) => (
                  <div style={{
                    marginTop: '16px',
                    padding: '16px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '12px',
                    borderLeft: '3px solid #3B82F6',
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '8px',
                    }}>
                      <span style={{ color: '#3B82F6' }}>📋</span>
                      <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '13px', fontWeight: 500 }}>
                        报告摘要
                      </span>
                    </div>
                    <p style={{
                      margin: 0,
                      fontSize: '14px',
                      lineHeight: 1.8,
                      color: 'rgba(255, 255, 255, 0.8)',
                    }}>
                      {text}
                      {isTyping && (
                        <motion.span
                          animate={{ opacity: [0, 1, 1, 0] }}
                          transition={{ duration: 0.6, repeat: Infinity }}
                          style={{ marginLeft: '1px', color: '#3B82F6' }}
                        >
                          |
                        </motion.span>
                      )}
                    </p>
                  </div>
                )}
                renderInsight={(text, isTyping) => (
                  <div style={{
                    marginTop: '12px',
                    padding: '12px 16px',
                    background: 'rgba(212, 175, 55, 0.05)',
                    borderRadius: '8px',
                    borderLeft: '3px solid #D4AF37',
                  }}>
                    <p style={{
                      margin: 0,
                      fontSize: '14px',
                      lineHeight: 1.6,
                      color: 'rgba(255, 255, 255, 0.85)',
                    }}>
                      ✓ {text}
                      {isTyping && (
                        <motion.span
                          animate={{ opacity: [0, 1, 1, 0] }}
                          transition={{ duration: 0.6, repeat: Infinity }}
                          style={{ marginLeft: '1px', color: '#D4AF37' }}
                        >
                          |
                        </motion.span>
                      )}
                    </p>
                  </div>
                )}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {result?.charts && result.charts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            style={{ marginTop: '24px' }}
          >
            <h4 style={{
              color: '#10B981',
              fontSize: '16px',
              fontWeight: 600,
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <span>📈</span> 数据图表
            </h4>
            <div style={{
              display: 'grid',
              gridTemplateColumns: compact ? '1fr' : 'repeat(2, 1fr)',
              gap: '16px',
            }}>
              {result.charts.map((chart, index) => (
                <ProgressiveChart
                  key={chart.chartId}
                  chartData={chart}
                  progress={100}
                  isPlaying={false}
                  animationDuration={1500}
                  showAgentTooltip={false}
                />
              ))}
            </div>
          </motion.div>
        )}

        {result?.recommendations && result.recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            style={{ marginTop: '24px' }}
          >
            <h4 style={{
              color: '#8B5CF6',
              fontSize: '16px',
              fontWeight: 600,
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <span>💡</span> 投资建议
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.recommendations.map((rec, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  style={{
                    padding: '12px 16px',
                    background: 'rgba(139, 92, 246, 0.1)',
                    borderRadius: '8px',
                    borderLeft: '3px solid #8B5CF6',
                  }}
                >
                  <span style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '14px' }}>
                    {rec}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            style={{
              marginTop: '24px',
              padding: '16px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
              borderRadius: '12px',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>✅</span>
              <div>
                <p style={{ margin: 0, color: '#10B981', fontSize: '16px', fontWeight: 600 }}>
                  报告生成完成
                </p>
                <p style={{ margin: '4px 0 0 0', color: 'rgba(255, 255, 255, 0.5)', fontSize: '12px' }}>
                  置信度: {(result.confidence * 100).toFixed(1)}% · 风险等级: {result.riskLevel === 'low' ? '低' : result.riskLevel === 'medium' ? '中' : '高'}
                </p>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              style={{
                padding: '10px 20px',
                background: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
                border: 'none',
                borderRadius: '8px',
                color: '#0f172a',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              查看完整报告 →
            </motion.button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default LiveReportPreview;
