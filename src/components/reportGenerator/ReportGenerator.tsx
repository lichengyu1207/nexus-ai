import React, { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReportGeneratorStore } from './reportGeneratorStore';
import AgentContributor from './AgentContributor';
import PlaybackControls from './PlaybackControls';
import ProgressiveChart from './ProgressiveChart';
import TypingQueue, { TypingQueueItem } from './TypingQueue';
import AgentProcessingAnimation from './AgentProcessingAnimation';
import { getAgentInfo } from './types/reportStream';

interface ReportGeneratorProps {
  autoPlay?: boolean;
  height?: number | string;
  showHeader?: boolean;
  compact?: boolean;
}

const EXAMPLE_CASES = [
  {
    id: 'shenzhen-house',
    title: '深圳南山区学区房分析',
    description: '分析深圳南山区学区房投资价值',
    icon: '🏠',
  },
  {
    id: 'beijing-office',
    title: '北京朝阳区写字楼评估',
    description: '评估北京朝阳区商业地产投资回报',
    icon: '🏢',
  },
  {
    id: 'shanghai-villa',
    title: '上海浦东别墅市场分析',
    description: '分析上海浦东高端别墅市场趋势',
    icon: '🏡',
  },
];

const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  autoPlay = false,
  height = 600,
  showHeader = true,
  compact = false,
}) => {
  const {
    title,
    summary,
    sections,
    insights,
    charts,
    chartProgress,
    typingRecords,
    references,
    disclaimer,
    copyright,
    progress,
    isComplete,
    isPlaying,
    speed,
    currentTime,
    totalDuration,
    agentContributions,
    activeAgent,
    initStreamPlayer,
    play,
    pause,
    reset,
    setSpeed,
    seekToProgress,
  } = useReportGeneratorStore();

  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  const [showCaseSelector, setShowCaseSelector] = useState(true);
  const [showProcessing, setShowProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (!hasInitialized.current && selectedCase && processingComplete) {
      initStreamPlayer();
      hasInitialized.current = true;
      setTimeout(() => play(), 500);
    }
  }, [initStreamPlayer, play, selectedCase, processingComplete]);

  const handlePlayPause = () => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  };

  const handleReplay = () => {
    reset();
    setProcessingComplete(false);
    setShowProcessing(true);
    hasInitialized.current = false;
  };

  const handleProgressChange = (newProgress: number) => {
    seekToProgress(newProgress);
  };

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
  };

  const handleSelectCase = (caseId: string) => {
    setSelectedCase(caseId);
    setShowCaseSelector(false);
    setShowProcessing(true);
  };

  const handleProcessingComplete = () => {
    setShowProcessing(false);
    setProcessingComplete(true);
  };

  const handleBackToCases = () => {
    reset();
    setSelectedCase(null);
    setShowCaseSelector(true);
    setShowProcessing(false);
    setProcessingComplete(false);
    hasInitialized.current = false;
  };

  const chartsArray = useMemo(() => {
    return Array.from(charts.values());
  }, [charts]);

  const contributionsArray = useMemo(() => {
    return agentContributions;
  }, [agentContributions]);

  const totalParagraphs = useMemo(() => {
    return sections.reduce((sum, section) => sum + section.paragraphs.length, 0);
  }, [sections]);

  const typingQueueItems = useMemo((): TypingQueueItem[] => {
    const items: TypingQueueItem[] = [];
    
    if (title) {
      items.push({
        id: 'main-title',
        text: title,
        type: 'title',
        speed: 40,
      });
    }
    
    if (summary) {
      items.push({
        id: 'summary',
        text: summary,
        type: 'summary',
        speed: 25,
      });
    }
    
    sections.forEach((section, sIndex) => {
      items.push({
        id: `section-title-${sIndex}`,
        text: section.title,
        type: 'section-title',
        speed: 30,
      });
      
      section.paragraphs.forEach((para, pIndex) => {
        items.push({
          id: para.id || `para-${sIndex}-${pIndex}`,
          text: para.text,
          type: 'paragraph',
          speed: 15,
          metadata: { sectionIndex: sIndex, paraIndex: pIndex },
        });
      });
    });
    
    return items;
  }, [title, summary, sections]);

  const showContent = title || (isPlaying && !showProcessing);

  return (
    <div 
      style={{ 
        height, 
        display: 'flex', 
        flexDirection: 'column',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))',
        borderRadius: compact ? '0' : '16px',
        overflow: 'hidden',
        border: compact ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      {showHeader && (
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
              animate={{ 
                rotate: isPlaying ? 360 : 0,
              }}
              transition={{ duration: 2, repeat: isPlaying ? Infinity : 0, ease: 'linear' }}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '16px',
              }}
            >
              📊
            </motion.div>
            <div>
              <h3 style={{ 
                color: '#fff', 
                margin: 0, 
                fontSize: '16px',
                fontWeight: 600,
              }}>
                动态报告生成器
              </h3>
              <span style={{ 
                color: 'rgba(255, 255, 255, 0.5)', 
                fontSize: '12px',
              }}>
                实时流式渲染
              </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {selectedCase && !showCaseSelector && (
              <motion.button
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={handleBackToCases}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '6px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                ← 切换案例
              </motion.button>
            )}
            <motion.div
              animate={{
                background: isPlaying 
                  ? ['#3B82F6', '#10B981', '#3B82F6']
                  : 'rgba(255, 255, 255, 0.1)',
              }}
              transition={{ duration: 2, repeat: isPlaying ? Infinity : 0 }}
              style={{
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                color: isPlaying ? '#fff' : 'rgba(255, 255, 255, 0.5)',
              }}
            >
              {showProcessing ? '处理中...' : isPlaying ? '生成中...' : isComplete ? '已完成' : '就绪'}
            </motion.div>
          </div>
        </div>
      )}

      <div style={{ 
        display: 'flex', 
        flex: 1, 
        overflow: 'hidden',
      }}>
        <div style={{
          width: compact ? '200px' : '240px',
          borderRight: '1px solid rgba(255, 255, 255, 0.05)',
          overflow: 'auto',
          padding: '12px',
        }}>
          <AgentContributor
            contributions={contributionsArray}
            activeAgent={activeAgent || undefined}
            showParticles={true}
          />
        </div>

        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '20px',
        }}>
          <AnimatePresence mode="wait">
            {showCaseSelector && (
              <motion.div
                key="case-selector"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                }}
              >
                <div style={{
                  textAlign: 'center',
                  marginBottom: '32px',
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                  <h3 style={{ 
                    color: '#fff', 
                    margin: 0, 
                    fontSize: '20px',
                    fontWeight: 600,
                  }}>
                    选择示例案例
                  </h3>
                  <p style={{ 
                    color: 'rgba(255, 255, 255, 0.5)', 
                    fontSize: '14px',
                    margin: '8px 0 0 0',
                  }}>
                    观看智能体协作生成完整分析报告
                  </p>
                </div>
                
                <div style={{
                  display: 'flex',
                  gap: '16px',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                }}>
                  {EXAMPLE_CASES.map((exampleCase, index) => (
                    <motion.div
                      key={exampleCase.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => handleSelectCase(exampleCase.id)}
                      style={{
                        width: '200px',
                        padding: '20px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: '12px',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        cursor: 'pointer',
                        textAlign: 'center',
                      }}
                      whileHover={{ 
                        scale: 1.02, 
                        borderColor: 'rgba(59, 130, 246, 0.5)',
                        background: 'rgba(59, 130, 246, 0.05)',
                      }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div style={{ fontSize: '32px', marginBottom: '12px' }}>
                        {exampleCase.icon}
                      </div>
                      <h4 style={{ 
                        color: '#fff', 
                        margin: 0, 
                        fontSize: '14px',
                        fontWeight: 600,
                      }}>
                        {exampleCase.title}
                      </h4>
                      <p style={{ 
                        color: 'rgba(255, 255, 255, 0.5)', 
                        fontSize: '12px',
                        margin: '8px 0 0 0',
                      }}>
                        {exampleCase.description}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {showProcessing && (
              <motion.div
                key="processing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ height: '100%' }}
              >
                <AgentProcessingAnimation
                  isActive={true}
                  currentAgent={activeAgent}
                  onComplete={handleProcessingComplete}
                  duration={4000}
                />
              </motion.div>
            )}

            {!showCaseSelector && !showProcessing && !showContent && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: 'rgba(255, 255, 255, 0.4)',
                }}
              >
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
                <p style={{ margin: 0, fontSize: '16px' }}>点击播放开始生成报告</p>
                <p style={{ margin: '8px 0 0 0', fontSize: '12px', opacity: 0.6 }}>
                  观看智能体协作生成完整分析报告
                </p>
              </motion.div>
            )}

            {showContent && !showCaseSelector && !showProcessing && (
              <motion.div
                key="content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
              >
                {typingQueueItems.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                      padding: '20px',
                      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1))',
                      borderRadius: '12px',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                    }}
                  >
                    <TypingQueue
                      items={typingQueueItems}
                      isPlaying={isPlaying}
                      speed={speed}
                      onProgress={(current, total) => {
                        const newProgress = (current / total) * 70;
                        useReportGeneratorStore.getState().setProgress(newProgress);
                      }}
                      renderTitle={(text, isTyping) => (
                        <h1 style={{ 
                          color: '#fff', 
                          margin: 0, 
                          fontSize: '24px',
                          fontWeight: 700,
                          textAlign: 'center',
                        }}>
                          {text}
                          {isTyping && (
                            <motion.span
                              animate={{ opacity: [0, 1, 1, 0] }}
                              transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
                              style={{ marginLeft: '2px', color: '#3B82F6' }}
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
                          borderRadius: '8px',
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
                            color: 'rgba(255, 255, 255, 0.8)' 
                          }}>
                            {text}
                            {isTyping && (
                              <motion.span
                                animate={{ opacity: [0, 1, 1, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
                                style={{ marginLeft: '1px', color: '#3B82F6' }}
                              >
                                |
                              </motion.span>
                            )}
                          </p>
                        </div>
                      )}
                      renderSectionTitle={(text, isTyping) => (
                        <div style={{
                          marginTop: '24px',
                          marginBottom: '16px',
                          padding: '16px 20px',
                          background: 'rgba(255, 255, 255, 0.02)',
                          borderRadius: '12px',
                          border: '1px solid rgba(255, 255, 255, 0.05)',
                        }}>
                          <h2 style={{
                            color: '#fff',
                            fontSize: '18px',
                            fontWeight: 600,
                            margin: 0,
                            paddingBottom: '12px',
                            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                          }}>
                            {text}
                            {isTyping && (
                              <motion.span
                                animate={{ opacity: [0, 1, 1, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
                                style={{ marginLeft: '2px', color: '#8B5CF6' }}
                              >
                                |
                              </motion.span>
                            )}
                          </h2>
                        </div>
                      )}
                      renderParagraph={(text, isTyping) => (
                        <div style={{
                          padding: '12px 16px',
                          background: 'rgba(255, 255, 255, 0.01)',
                          borderRadius: '8px',
                          marginBottom: '12px',
                        }}>
                          <p style={{ 
                            margin: 0, 
                            fontSize: '14px', 
                            lineHeight: 1.9, 
                            color: 'rgba(255, 255, 255, 0.85)',
                            textIndent: '2em',
                          }}>
                            {text}
                            {isTyping && (
                              <motion.span
                                animate={{ opacity: [0, 1, 1, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
                                style={{ marginLeft: '1px', color: '#10B981' }}
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

                {typingRecords.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}>
                      <span style={{ color: '#8B5CF6' }}>⌨️</span>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.7)', 
                        fontSize: '14px',
                        fontWeight: 500,
                      }}>
                        实时生成记录
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <AnimatePresence>
                        {typingRecords.map((record, index) => {
                          const agentInfo = getAgentInfo(record.agent);
                          return (
                            <motion.div
                              key={record.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.05 }}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 12px',
                                background: 'rgba(255, 255, 255, 0.03)',
                                borderRadius: '6px',
                                borderLeft: `2px solid ${agentInfo.color}`,
                              }}
                            >
                              <span style={{ fontSize: '14px' }}>{agentInfo.icon}</span>
                              <span style={{ 
                                flex: 1, 
                                fontSize: '12px',
                                color: 'rgba(255, 255, 255, 0.7)',
                              }}>
                                {record.content}
                              </span>
                              {record.source && (
                                <span style={{
                                  fontSize: '10px',
                                  color: 'rgba(255, 255, 255, 0.4)',
                                }}>
                                  {record.source}
                                </span>
                              )}
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                )}

                {insights.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}>
                      <span style={{ color: '#F59E0B' }}>💡</span>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.7)', 
                        fontSize: '14px',
                        fontWeight: 500,
                      }}>
                        核心洞察 ({insights.length})
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <AnimatePresence>
                        {insights.map((insight, index) => {
                          const agentInfo = getAgentInfo(insight.agent);
                          return (
                            <motion.div
                              key={insight.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '12px',
                                padding: '12px',
                                background: `${agentInfo.color}10`,
                                borderRadius: '8px',
                                borderLeft: `3px solid ${agentInfo.color}`,
                              }}
                            >
                              <span style={{ fontSize: '16px' }}>{agentInfo.icon}</span>
                              <div style={{ flex: 1 }}>
                                <p style={{ 
                                  margin: 0, 
                                  fontSize: '14px', 
                                  lineHeight: 1.6, 
                                  color: 'rgba(255, 255, 255, 0.85)' 
                                }}>
                                  {insight.text}
                                </p>
                              </div>
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                )}

                {chartsArray.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}>
                      <span style={{ color: '#10B981' }}>📈</span>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.7)', 
                        fontSize: '14px',
                        fontWeight: 500,
                      }}>
                        数据图表 ({chartsArray.length})
                      </span>
                    </div>
                    <AnimatePresence>
                      {chartsArray.map((chart, index) => (
                        <motion.div
                          key={chart.chartId}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.2 }}
                        >
                          <ProgressiveChart
                            chartData={chart}
                            progress={chartProgress.get(chart.chartId) || 0}
                            isPlaying={isPlaying}
                            animationDuration={2000}
                            showAgentTooltip={true}
                            onComplete={() => {
                              useReportGeneratorStore.getState().updateChartProgress(chart.chartId, 100);
                            }}
                          />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </motion.div>
                )}

                {references.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}>
                      <span style={{ color: '#06B6D4' }}>📚</span>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.7)', 
                        fontSize: '14px',
                        fontWeight: 500,
                      }}>
                        引用来源 ({references.length})
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <AnimatePresence>
                        {references.map((ref, index) => {
                          const agentInfo = ref.agent ? getAgentInfo(ref.agent) : null;
                          return (
                            <motion.div
                              key={ref.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.05 }}
                              style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '12px',
                                padding: '10px 12px',
                                background: 'rgba(6, 182, 212, 0.05)',
                                borderRadius: '8px',
                                borderLeft: '2px solid #06B6D4',
                              }}
                            >
                              <span style={{ 
                                fontSize: '12px',
                                fontWeight: 'bold',
                                color: '#06B6D4',
                                minWidth: '20px',
                              }}>
                                [{index + 1}]
                              </span>
                              <div style={{ flex: 1 }}>
                                <p style={{ 
                                  margin: 0, 
                                  fontSize: '13px',
                                  color: 'rgba(255, 255, 255, 0.8)',
                                }}>
                                  {ref.title}
                                </p>
                                <div style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '8px',
                                  marginTop: '4px',
                                  flexWrap: 'wrap',
                                }}>
                                  <span style={{
                                    fontSize: '11px',
                                    color: 'rgba(255, 255, 255, 0.5)',
                                  }}>
                                    {ref.source}
                                  </span>
                                  {ref.publishDate && (
                                    <span style={{
                                      fontSize: '10px',
                                      color: 'rgba(255, 255, 255, 0.4)',
                                    }}>
                                      {ref.publishDate}
                                    </span>
                                  )}
                                  {agentInfo && (
                                    <span style={{
                                      fontSize: '10px',
                                      padding: '1px 4px',
                                      background: `${agentInfo.color}20`,
                                      borderRadius: '3px',
                                      color: agentInfo.color,
                                    }}>
                                      {agentInfo.icon} {agentInfo.name}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                )}

                {disclaimer && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(245, 158, 11, 0.05)',
                      borderRadius: '12px',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}>
                      <span style={{ color: '#F59E0B' }}>⚠️</span>
                      <span style={{ 
                        color: '#F59E0B', 
                        fontSize: '14px',
                        fontWeight: 600,
                      }}>
                        {disclaimer.title}
                      </span>
                    </div>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '12px',
                      color: 'rgba(255, 255, 255, 0.6)',
                      lineHeight: 1.8,
                    }}>
                      {disclaimer.content}
                    </p>
                  </motion.div>
                )}

                {copyright && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.9 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}>
                      <span style={{ color: '#EC4899' }}>©️</span>
                      <span style={{ 
                        color: 'rgba(255, 255, 255, 0.7)', 
                        fontSize: '14px',
                        fontWeight: 500,
                      }}>
                        版权声明
                      </span>
                    </div>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                    }}>
                      <p style={{ 
                        margin: 0, 
                        fontSize: '13px',
                        color: 'rgba(255, 255, 255, 0.8)',
                      }}>
                        <strong>{copyright.holder}</strong> © {copyright.year}
                      </p>
                      <p style={{ 
                        margin: 0, 
                        fontSize: '12px',
                        color: 'rgba(255, 255, 255, 0.5)',
                      }}>
                        {copyright.rights}
                      </p>
                      {copyright.contact && (
                        <p style={{ 
                          margin: 0, 
                          fontSize: '11px',
                          color: 'rgba(255, 255, 255, 0.4)',
                        }}>
                          联系方式: {copyright.contact}
                        </p>
                      )}
                    </div>
                  </motion.div>
                )}

                {isComplete && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '12px',
                      padding: '20px',
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
                      borderRadius: '12px',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                    }}
                  >
                    <span style={{ fontSize: '24px' }}>✅</span>
                    <div>
                      <p style={{ 
                        margin: 0, 
                        color: '#10B981', 
                        fontSize: '16px',
                        fontWeight: 600,
                      }}>
                        报告生成完成
                      </p>
                      <p style={{ 
                        margin: '4px 0 0 0', 
                        color: 'rgba(255, 255, 255, 0.5)', 
                        fontSize: '12px',
                      }}>
                        共 {sections.length} 章节 · {totalParagraphs} 段落 · {insights.length} 洞察 · {chartsArray.length} 图表 · {references.length} 引用
                      </p>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div style={{
          width: compact ? '200px' : '240px',
          borderLeft: '1px solid rgba(255, 255, 255, 0.05)',
          overflow: 'auto',
          padding: '12px',
        }}>
          <PlaybackControls
            isPlaying={isPlaying}
            speed={speed}
            progress={progress}
            totalDuration={totalDuration}
            currentTime={currentTime}
            onPlayPause={handlePlayPause}
            onSpeedChange={handleSpeedChange}
            onProgressChange={handleProgressChange}
            onReplay={handleReplay}
            onComplete={isComplete}
          />
        </div>
      </div>
    </div>
  );
};

export default ReportGenerator;
