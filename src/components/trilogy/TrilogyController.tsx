import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { SoundEffects } from './SoundEffects';
import { ParticleManager } from './ParticleManager';
import { MemoryTimeline } from './MemoryTimeline';
import { KnowledgeGraph } from './KnowledgeGraph';
import { PersonalityBubble } from './PersonalityBubble';
import { EvolutionProgress } from './EvolutionProgress';
import { EvolutionReward } from './EvolutionReward';
import { ReportTheater } from '../reportTheater';
import agentsData from '../../data/agentsData.json';
import scene2Script from '../../data/scene2Script.json';
import reportScript from '../../data/reportScript.json';

type DemoPhase = 'idle' | 'input' | 'agents' | 'memory' | 'personality' | 'evolution' | 'complete';

interface AgentStatus {
  status: 'idle' | 'working' | 'done';
  message: string;
  progress: number;
}

const PHASE_DURATIONS = {
  input: 20000,
  agents: 60000,
  memory: 40000,
  personality: 30000,
  evolution: 30000,
  complete: 10000,
};

const TrilogyController: React.FC = () => {
  const [phase, setPhase] = useState<DemoPhase>('idle');
  const [userInput, setUserInput] = useState('帮我分析深圳南山区学区房');
  const [agentsStatus, setAgentsStatus] = useState<Record<string, AgentStatus>>({});
  const [reportSections, setReportSections] = useState<Array<{ title: string; content: string }>>([]);
  const [selectedPersonality, setSelectedPersonality] = useState<'zhouyu' | 'luxun'>('zhouyu');
  const [evolutionProgress, setEvolutionProgress] = useState(0);
  const [showEvolutionReward, setShowEvolutionReward] = useState(false);
  const [memoryProgress, setMemoryProgress] = useState(0);
  const [inputProgress, setInputProgress] = useState(0);
  const [currentTypingText, setCurrentTypingText] = useState('');
  const [showLightBeams, setShowLightBeams] = useState(false);
  const [agentsComplete, setAgentsComplete] = useState(0);
  const [showReport, setShowReport] = useState(false);
  const [reportContent, setReportContent] = useState<{
    title: string;
    findings: string[];
    charts: { type: string; data: number[] }[];
  } | null>(null);
  const [showReportTheater, setShowReportTheater] = useState(false);
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const scriptIndexRef = useRef(0);

  const agents = agentsData.agents;

  useEffect(() => {
    SoundEffects.initialize().catch(console.warn);
  }, []);

  const clearAllTimers = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startDemo = useCallback(() => {
    clearAllTimers();
    setPhase('input');
    setInputProgress(0);
    setCurrentTypingText('');
    SoundEffects.playTone(440, 0.2, 'sine');
    
    runInputPhase();
  }, [clearAllTimers]);

  const runInputPhase = useCallback(() => {
    const fullText = userInput;
    let charIndex = 0;
    
    const typeInterval = setInterval(() => {
      if (charIndex < fullText.length) {
        setCurrentTypingText(fullText.substring(0, charIndex + 1));
        setInputProgress((charIndex + 1) / fullText.length * 100);
        charIndex++;
      } else {
        clearInterval(typeInterval);
        SoundEffects.playTone(523, 0.15, 'sine');
        
        setTimeout(() => {
          setShowLightBeams(true);
          SoundEffects.playTone(659, 0.3, 'sine');
          
          setTimeout(() => {
            setPhase('agents');
            runAgentsPhase();
          }, 2500);
        }, 500);
      }
    }, 80);
    
    intervalRef.current = typeInterval;
  }, [userInput]);

  const runAgentsPhase = useCallback(() => {
    const script = scene2Script as Array<{ time: number; agent: string; status: string; message: string }>;
    scriptIndexRef.current = 0;
    let completedCount = 0;
    
    const executeScript = () => {
      if (scriptIndexRef.current >= script.length) {
        setTimeout(() => {
          setPhase('memory');
          runMemoryPhase();
        }, 2000);
        return;
      }
      
      const item = script[scriptIndexRef.current];
      const newStatus = item.status as 'idle' | 'working' | 'done';
      
      setAgentsStatus(prev => ({
        ...prev,
        [item.agent]: {
          status: newStatus,
          message: item.message || '',
          progress: newStatus === 'done' ? 100 : newStatus === 'working' ? 50 : 0,
        },
      }));
      
      if (newStatus === 'working') {
        ParticleManager.createBurst('lightBeam', 100, 100, 3);
        SoundEffects.playTone(440 + Math.random() * 200, 0.1, 'sine');
      } else if (newStatus === 'done') {
        completedCount++;
        setAgentsComplete(completedCount);
        SoundEffects.playTone(880, 0.15, 'sine');
      }
      
      scriptIndexRef.current++;
      
      if (scriptIndexRef.current < script.length) {
        const nextDelay = Math.max(1000, (script[scriptIndexRef.current].time - item.time) * 500);
        timerRef.current = setTimeout(executeScript, nextDelay);
      } else {
        setTimeout(() => {
          setPhase('memory');
          runMemoryPhase();
        }, 2000);
      }
    };
    
    executeScript();
  }, []);

  const runMemoryPhase = useCallback(() => {
    SoundEffects.playTone(523, 0.3, 'sine');
    setMemoryProgress(0);
    
    const progressInterval = setInterval(() => {
      setMemoryProgress(prev => {
        const newValue = prev + 2.5;
        if (newValue >= 100) {
          clearInterval(progressInterval);
          SoundEffects.playTone(659, 0.2, 'sine');
          setTimeout(() => {
            setPhase('personality');
            runPersonalityPhase();
          }, 1000);
          return 100;
        }
        return newValue;
      });
    }, 400);
    
    intervalRef.current = progressInterval;
  }, []);

  const runPersonalityPhase = useCallback(() => {
    const personality: 'zhouyu' | 'luxun' = Math.random() > 0.5 ? 'zhouyu' : 'luxun';
    setSelectedPersonality(personality);
    
    if (personality === 'zhouyu') {
      SoundEffects.playZhouyuSpeak();
    } else {
      SoundEffects.playLuxunSpeak();
    }
    
    setTimeout(() => {
      setPhase('evolution');
      runEvolutionPhase();
    }, PHASE_DURATIONS.personality);
  }, []);

  const runEvolutionPhase = useCallback(() => {
    SoundEffects.playTone(659, 0.2, 'sine');
    setEvolutionProgress(0);
    
    const progressInterval = setInterval(() => {
      setEvolutionProgress(prev => {
        const newValue = prev + 3.3;
        if (newValue >= 100) {
          clearInterval(progressInterval);
          SoundEffects.playEvolutionComplete();
          setShowEvolutionReward(true);
          setTimeout(() => {
            setPhase('complete');
            runCompletePhase();
          }, 2000);
          return 100;
        }
        return newValue;
      });
    }, 300);
    
    intervalRef.current = progressInterval;
  }, []);

  const runCompletePhase = useCallback(() => {
    setShowReport(true);
    setReportContent({
      title: '深圳南山区学区房分析报告',
      findings: [
        '近三个月均价上涨5.2%',
        '学区房溢价率约15-20%',
        '地铁规划区域增值潜力大',
        '南山区教育资源优质集中',
      ],
      charts: [
        { type: 'price_trend', data: [12, 15, 18, 22, 25, 28, 32, 35, 38, 42, 45, 48] },
        { type: 'area_compare', data: [85, 72, 68, 55] },
      ],
    });
    
    setTimeout(() => {
      SoundEffects.playTone(880, 0.3, 'sine');
    }, 500);
  }, []);

  const resetDemo = useCallback(() => {
    clearAllTimers();
    setPhase('idle');
    setAgentsStatus({});
    setReportSections([]);
    setEvolutionProgress(0);
    setMemoryProgress(0);
    setInputProgress(0);
    setCurrentTypingText('');
    setShowLightBeams(false);
    setAgentsComplete(0);
    setShowReport(false);
    setShowEvolutionReward(false);
    setReportContent(null);
  }, [clearAllTimers]);

  useEffect(() => {
    return () => {
      clearAllTimers();
    };
  }, [clearAllTimers]);

  return (
    <div style={styles.container}>
      <canvas
        ref={(canvas) => {
          if (canvas && phase !== 'idle') {
            ParticleManager.initialize(canvas);
          }
        }}
        style={styles.particleCanvas}
      />
      
      <AnimatePresence mode="wait">
        {phase === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.idleContent}
          >
            <motion.div
              animate={{ 
                boxShadow: [
                  '0 0 20px rgba(212, 175, 55, 0.3)',
                  '0 0 40px rgba(212, 175, 55, 0.6)',
                  '0 0 20px rgba(212, 175, 55, 0.3)',
                ],
              }}
              transition={{ duration: 2, repeat: Infinity }}
              style={styles.logoContainer}
            >
              <span style={styles.logoIcon}>🏠</span>
            </motion.div>
            
            <motion.h1
              style={styles.title}
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            >
              房都督AI
            </motion.h1>
            
            <p style={styles.subtitle}>基于AI大模型集群的智能决策中枢</p>
            
            <motion.p
              style={styles.description}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              六部智能体协同 · 海马体记忆挖掘 · 自我进化系统
            </motion.p>
            
            <motion.button
              style={styles.startButton}
              onClick={startDemo}
              whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(212, 175, 55, 0.5)' }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
            >
              <span style={styles.buttonIcon}>▶</span>
              开始分析
            </motion.button>
            
            <motion.p
              style={styles.duration}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2 }}
            >
              演示时长约3分钟
            </motion.p>
          </motion.div>
        )}

        {phase === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={styles.inputContent}
          >
            <div style={styles.inputBox}>
              <div style={styles.terminalHeader}>
                <span style={styles.dot} />
                <span style={{ ...styles.dot, background: '#fbbf24' }} />
                <span style={{ ...styles.dot, background: '#22c55e' }} />
                <span style={styles.terminalTitle}>智能分析终端</span>
              </div>
              <div style={styles.inputContent_inner}>
                <span style={styles.prompt}>$ </span>
                <span style={styles.inputText}>{currentTypingText}</span>
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  style={styles.cursor}
                >
                  ▋
                </motion.span>
              </div>
              <div style={styles.progressBar}>
                <motion.div
                  style={styles.progressFill}
                  animate={{ width: `${inputProgress}%` }}
                />
              </div>
            </div>
            
            {showLightBeams && (
              <motion.div
                style={styles.lightBeams}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                {agents.slice(0, 6).map((agent, index) => (
                  <motion.div
                    key={agent.id}
                    style={{
                      ...styles.beamParticle,
                      backgroundColor: agent.color,
                      boxShadow: `0 0 30px ${agent.color}, 0 0 60px ${agent.color}`,
                    }}
                    initial={{ y: 0, x: 0, scale: 0, opacity: 0 }}
                    animate={{
                      y: [0, -50, 150, 250],
                      x: (index - 2.5) * 80,
                      scale: [0, 2, 1.5, 0],
                      opacity: [0, 1, 1, 0],
                    }}
                    transition={{ duration: 2, delay: index * 0.15, ease: 'easeOut' }}
                  />
                ))}
              </motion.div>
            )}
            
            <motion.div
              style={styles.inputStatus}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                style={styles.spinner}
              />
              <span>正在解析需求...</span>
            </motion.div>
          </motion.div>
        )}

        {phase === 'agents' && (
          <motion.div
            key="agents"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.agentsContent}
          >
            <div style={styles.agentsHeader}>
              <h3 style={styles.sectionTitle}>六部智能体协同分析</h3>
              <div style={styles.agentsProgress}>
                <span style={styles.progressText}>{agentsComplete}/6 完成</span>
                <div style={styles.miniProgressBar}>
                  <motion.div
                    style={styles.miniProgressFill}
                    animate={{ width: `${(agentsComplete / 6) * 100}%` }}
                  />
                </div>
              </div>
            </div>
            
            <div style={styles.agentsGrid}>
              {agents.map((agent, index) => {
                const status = agentsStatus[agent.id]?.status || 'idle';
                const message = agentsStatus[agent.id]?.message || '';
                
                return (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, scale: 0.8, y: 20 }}
                    animate={{ 
                      opacity: 1, 
                      scale: 1, 
                      y: 0,
                      borderColor: status === 'working' ? agent.color : 'rgba(255,255,255,0.1)',
                    }}
                    transition={{ delay: index * 0.1 }}
                    style={{
                      ...styles.agentCard,
                      background: status === 'done' 
                        ? `linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1))` 
                        : status === 'working'
                        ? `linear-gradient(135deg, ${agent.color}20, ${agent.color}10)`
                        : 'rgba(255, 255, 255, 0.03)',
                    }}
                  >
                    {status === 'working' && (
                      <motion.div
                        style={{ ...styles.scanLine, background: `linear-gradient(90deg, transparent, ${agent.color}60, transparent)` }}
                        animate={{ x: ['-100%', '100%'] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      />
                    )}
                    
                    <motion.div 
                      style={styles.agentIcon}
                      animate={status === 'working' ? { scale: [1, 1.1, 1] } : {}}
                      transition={{ duration: 0.5, repeat: status === 'working' ? Infinity : 0 }}
                    >
                      {agent.icon}
                    </motion.div>
                    
                    <div style={styles.agentName}>{agent.name}</div>
                    <div style={styles.agentRole}>{agent.role}</div>
                    
                    {message && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={styles.agentMessage}
                      >
                        {message}
                      </motion.div>
                    )}
                    
                    {status === 'done' && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        style={styles.checkMark}
                      >
                        ✓
                      </motion.div>
                    )}
                    
                    {status === 'working' && (
                      <motion.div
                        style={styles.workingIndicator}
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      />
                    )}
                  </motion.div>
                );
              })}
            </div>
            
            <div style={styles.statusIndicator}>
              <motion.div
                animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={styles.statusDot}
              />
              <span style={styles.statusText}>智能体协同分析中...</span>
            </div>
          </motion.div>
        )}

        {phase === 'memory' && (
          <motion.div
            key="memory"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.memoryContent}
          >
            <h3 style={styles.sectionTitle}>海马体记忆挖掘</h3>
            
            <div style={styles.memoryGrid}>
              <div style={styles.memoryLeft}>
                <MemoryTimeline isActive={true} />
              </div>
              <div style={styles.memoryRight}>
                <KnowledgeGraph width={320} height={280} isMining={true} />
                
                <div style={styles.memoryProgress}>
                  <div style={styles.progressLabel}>
                    <span>记忆挖掘进度</span>
                    <span style={styles.progressPercent}>{Math.round(memoryProgress)}%</span>
                  </div>
                  <div style={styles.progressBar}>
                    <motion.div
                      style={styles.progressFill}
                      animate={{ width: `${memoryProgress}%` }}
                    />
                  </div>
                  
                  <div style={styles.memoryStats}>
                    <div style={styles.memoryStat}>
                      <span style={styles.statValue}>12</span>
                      <span style={styles.statLabel}>关联记忆</span>
                    </div>
                    <div style={styles.memoryStat}>
                      <span style={styles.statValue}>8</span>
                      <span style={styles.statLabel}>新发现</span>
                    </div>
                    <div style={styles.memoryStat}>
                      <span style={styles.statValue}>3</span>
                      <span style={styles.statLabel}>深度洞察</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {phase === 'personality' && (
          <motion.div
            key="personality"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.personalityContent}
          >
            <h3 style={styles.sectionTitle}>
              {selectedPersonality === 'zhouyu' ? '周瑜都督' : '陆逊都督'}为您服务
            </h3>
            
            <div style={styles.personalityCard}>
              <motion.div
                style={{
                  ...styles.personalityAvatar,
                  background: selectedPersonality === 'zhouyu' 
                    ? 'linear-gradient(135deg, #D4AF37, #F59E0B)'
                    : 'linear-gradient(135deg, #3B82F6, #60A5FA)',
                }}
                animate={{ 
                  boxShadow: [
                    `0 0 20px ${selectedPersonality === 'zhouyu' ? 'rgba(212, 175, 55, 0.5)' : 'rgba(59, 130, 246, 0.5)'}`,
                    `0 0 40px ${selectedPersonality === 'zhouyu' ? 'rgba(212, 175, 55, 0.8)' : 'rgba(59, 130, 246, 0.8)'}`,
                    `0 0 20px ${selectedPersonality === 'zhouyu' ? 'rgba(212, 175, 55, 0.5)' : 'rgba(59, 130, 246, 0.5)'}`,
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {selectedPersonality === 'zhouyu' ? '瑜' : '逊'}
              </motion.div>
              
              <PersonalityBubble
                personality={selectedPersonality}
                scene="taskComplete"
                autoShow={true}
              />
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 }}
                style={styles.personalityDesc}
              >
                {selectedPersonality === 'zhouyu' 
                  ? '豪迈果敢，善于宏观把控，以战略眼光分析房产投资价值'
                  : '沉稳细致，精于数据验证，以严谨态度确保分析准确性'}
              </motion.div>
            </div>
          </motion.div>
        )}

        {phase === 'evolution' && (
          <motion.div
            key="evolution"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.evolutionContent}
          >
            <h3 style={styles.sectionTitle}>智能体进化</h3>
            
            <EvolutionProgress
              currentProgress={evolutionProgress}
              showDetails={true}
            />
            
            <div style={styles.evolutionAbilities}>
              {['多轮诱导检测', '情感识别', '风险预警'].map((ability, index) => (
                <motion.div
                  key={ability}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ 
                    opacity: evolutionProgress > (index + 1) * 30 ? 1 : 0.3,
                    scale: evolutionProgress > (index + 1) * 30 ? 1 : 0.8,
                  }}
                  transition={{ delay: index * 0.2 }}
                  style={styles.abilityCard}
                >
                  <span style={styles.abilityIcon}>⚡</span>
                  <span style={styles.abilityName}>{ability}</span>
                </motion.div>
              ))}
            </div>
            
            {showEvolutionReward && (
              <EvolutionReward autoShow={true} />
            )}
          </motion.div>
        )}

        {phase === 'complete' && (
          <motion.div
            key="complete"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            style={styles.completeContent}
          >
            <motion.div
              animate={{ 
                scale: [1, 1.2, 1],
                rotate: [0, 10, -10, 0],
              }}
              transition={{ duration: 0.5 }}
              style={styles.completeIcon}
            >
              🎉
            </motion.div>
            
            <h2 style={styles.completeTitle}>分析完成！</h2>
            
            <p style={styles.completeDesc}>
              六部智能体协同工作，已完成智能分析与进化升级
            </p>
            
            {showReport && reportContent && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={styles.reportPreview}
              >
                <h4 style={styles.reportTitle}>{reportContent.title}</h4>
                <ul style={styles.findingsList}>
                  {reportContent.findings.map((finding, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      style={styles.findingItem}
                    >
                      ✓ {finding}
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}
            
            <div style={styles.completeStats}>
              <div style={styles.statItem}>
                <span style={styles.statValue}>6</span>
                <span style={styles.statLabel}>智能体协作</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>12</span>
                <span style={styles.statLabel}>记忆关联</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>3</span>
                <span style={styles.statLabel}>新能力解锁</span>
              </div>
            </div>
            
            <div style={styles.completeButtons}>
              <motion.button
                style={styles.secondaryButton}
                onClick={resetDemo}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                再看一次
              </motion.button>
              <motion.button
                style={styles.theaterButton}
                onClick={() => setShowReportTheater(true)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                📊 观看报告生成
              </motion.button>
              <motion.button
                style={styles.primaryButton}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                查看完整报告 →
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <ReportTheater
        isOpen={showReportTheater}
        onClose={() => setShowReportTheater(false)}
        autoPlay={true}
      />
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    minHeight: '600px',
    background: `linear-gradient(180deg, ${theme.colors.primary.deepBlue}, ${theme.colors.primary.deepBlueDark})`,
    borderRadius: theme.borderRadius.xl,
    overflow: 'hidden',
    position: 'relative',
  },
  particleCanvas: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    opacity: 0.6,
  },
  idleContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '600px',
    textAlign: 'center',
    padding: '40px',
  },
  logoContainer: {
    width: '100px',
    height: '100px',
    borderRadius: '50%',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}20, ${theme.colors.primary.gold}10)`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '24px',
    border: `2px solid ${theme.colors.primary.gold}40`,
  },
  logoIcon: {
    fontSize: '48px',
  },
  title: {
    fontSize: '48px',
    color: theme.colors.primary.gold,
    fontFamily: theme.typography.fontFamily.display,
    margin: 0,
    marginBottom: '8px',
    textShadow: '0 0 30px rgba(212, 175, 55, 0.3)',
  },
  subtitle: {
    fontSize: '20px',
    color: theme.colors.primary.goldLight,
    margin: 0,
    marginBottom: '16px',
    opacity: 0.8,
  },
  description: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
    marginBottom: '32px',
  },
  startButton: {
    padding: '16px 48px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldDark})`,
    color: theme.colors.primary.deepBlue,
    fontSize: '18px',
    fontWeight: 'bold',
    border: 'none',
    borderRadius: theme.borderRadius.xl,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  buttonIcon: {
    fontSize: '14px',
  },
  duration: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.4)',
    marginTop: '16px',
  },
  inputContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '600px',
    padding: '40px',
    position: 'relative',
  },
  inputBox: {
    width: '100%',
    maxWidth: '650px',
    background: 'rgba(255, 255, 255, 0.08)',
    borderRadius: theme.borderRadius.xl,
    backdropFilter: 'blur(10px)',
    overflow: 'hidden',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  terminalHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(0, 0, 0, 0.2)',
  },
  dot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    background: '#ef4444',
  },
  terminalTitle: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '14px',
    marginLeft: '12px',
  },
  inputContent_inner: {
    padding: '24px',
    fontSize: '18px',
    color: '#fff',
    fontFamily: 'monospace',
    minHeight: '80px',
  },
  prompt: {
    color: theme.colors.primary.gold,
  },
  inputText: {
    color: '#fff',
  },
  cursor: {
    color: theme.colors.primary.gold,
    marginLeft: '2px',
  },
  progressBar: {
    height: '3px',
    background: 'rgba(255, 255, 255, 0.1)',
  },
  progressFill: {
    height: '100%',
    background: `linear-gradient(90deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldLight})`,
    borderRadius: theme.borderRadius.full,
  },
  lightBeams: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '100%',
    height: '400px',
    pointerEvents: 'none',
  },
  beamParticle: {
    position: 'absolute',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    left: '50%',
    top: '0',
    transform: 'translate(-50%, -50%)',
  },
  inputStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginTop: '32px',
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: '14px',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255, 255, 255, 0.2)',
    borderTopColor: theme.colors.primary.gold,
    borderRadius: '50%',
  },
  agentsContent: {
    padding: '40px',
  },
  agentsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    maxWidth: '900px',
    margin: '0 auto 24px',
  },
  sectionTitle: {
    color: theme.colors.primary.gold,
    fontSize: '24px',
    textAlign: 'center',
    marginBottom: '24px',
    fontFamily: theme.typography.fontFamily.display,
  },
  agentsProgress: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  progressText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '14px',
  },
  miniProgressBar: {
    width: '100px',
    height: '6px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: theme.borderRadius.full,
    overflow: 'hidden',
  },
  miniProgressFill: {
    height: '100%',
    background: theme.colors.primary.gold,
    borderRadius: theme.borderRadius.full,
  },
  agentsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    maxWidth: '900px',
    margin: '0 auto',
  },
  agentCard: {
    position: 'relative',
    padding: '24px 16px',
    borderRadius: theme.borderRadius.lg,
    border: '2px solid rgba(255, 255, 255, 0.1)',
    textAlign: 'center',
    overflow: 'hidden',
    transition: 'all 0.3s ease',
  },
  scanLine: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
  },
  agentIcon: {
    fontSize: '40px',
    marginBottom: '12px',
  },
  agentName: {
    color: '#fff',
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  agentRole: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '12px',
    marginBottom: '8px',
  },
  agentMessage: {
    color: theme.colors.primary.goldLight,
    fontSize: '12px',
    padding: '8px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.md,
    marginTop: '8px',
  },
  checkMark: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    width: '24px',
    height: '24px',
    background: '#22c55e',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: '14px',
  },
  workingIndicator: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    width: '20px',
    height: '20px',
    border: '2px solid rgba(255, 255, 255, 0.2)',
    borderTopColor: theme.colors.primary.gold,
    borderRadius: '50%',
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    marginTop: '32px',
  },
  statusDot: {
    width: '10px',
    height: '10px',
    background: '#22c55e',
    borderRadius: '50%',
  },
  statusText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '14px',
  },
  memoryContent: {
    padding: '40px',
  },
  memoryGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '32px',
    maxWidth: '1000px',
    margin: '0 auto',
  },
  memoryLeft: {},
  memoryRight: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  memoryProgress: {
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.lg,
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  progressLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '14px',
    marginBottom: '12px',
  },
  progressPercent: {
    color: theme.colors.primary.gold,
    fontWeight: 'bold',
  },
  memoryStats: {
    display: 'flex',
    justifyContent: 'space-around',
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
  },
  memoryStat: {
    textAlign: 'center',
  },
  statValue: {
    display: 'block',
    color: theme.colors.primary.gold,
    fontSize: '24px',
    fontWeight: 'bold',
  },
  statLabel: {
    display: 'block',
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '12px',
    marginTop: '4px',
  },
  personalityContent: {
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    minHeight: '500px',
    justifyContent: 'center',
  },
  personalityCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '24px',
    maxWidth: '500px',
  },
  personalityAvatar: {
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '56px',
    color: '#fff',
    fontFamily: theme.typography.fontFamily.display,
    border: '3px solid rgba(255, 255, 255, 0.2)',
  },
  personalityDesc: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '14px',
    textAlign: 'center',
    lineHeight: 1.6,
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.lg,
  },
  evolutionContent: {
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    minHeight: '500px',
    justifyContent: 'center',
  },
  evolutionAbilities: {
    display: 'flex',
    gap: '16px',
    marginTop: '32px',
    marginBottom: '24px',
  },
  abilityCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 20px',
    background: 'rgba(212, 175, 55, 0.1)',
    border: '1px solid rgba(212, 175, 55, 0.3)',
    borderRadius: theme.borderRadius.lg,
    color: theme.colors.primary.gold,
    fontSize: '14px',
  },
  abilityIcon: {
    fontSize: '16px',
  },
  abilityName: {
    fontWeight: 500,
  },
  completeContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '600px',
    textAlign: 'center',
    padding: '40px',
  },
  completeIcon: {
    fontSize: '80px',
    marginBottom: '24px',
  },
  completeTitle: {
    color: theme.colors.primary.gold,
    fontSize: '36px',
    margin: '0 0 16px 0',
    fontFamily: theme.typography.fontFamily.display,
  },
  completeDesc: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '16px',
    margin: '0 0 24px 0',
  },
  reportPreview: {
    width: '100%',
    maxWidth: '500px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.lg,
    border: '1px solid rgba(255, 255, 255, 0.1)',
    marginBottom: '24px',
    textAlign: 'left',
  },
  reportTitle: {
    color: theme.colors.primary.gold,
    fontSize: '16px',
    margin: '0 0 12px 0',
    paddingBottom: '12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  findingsList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  findingItem: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    padding: '8px 0',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  },
  completeStats: {
    display: 'flex',
    gap: '48px',
    marginBottom: '32px',
  },
  statItem: {
    textAlign: 'center',
  },
  completeButtons: {
    display: 'flex',
    gap: '16px',
  },
  secondaryButton: {
    padding: '14px 32px',
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#fff',
    fontSize: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: theme.borderRadius.lg,
    cursor: 'pointer',
  },
  theaterButton: {
    padding: '14px 32px',
    background: 'rgba(212, 175, 55, 0.2)',
    color: '#D4AF37',
    fontSize: '16px',
    border: '1px solid rgba(212, 175, 55, 0.4)',
    borderRadius: theme.borderRadius.lg,
    cursor: 'pointer',
  },
  primaryButton: {
    padding: '14px 32px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldDark})`,
    color: theme.colors.primary.deepBlue,
    fontSize: '16px',
    fontWeight: 'bold',
    border: 'none',
    borderRadius: theme.borderRadius.lg,
    cursor: 'pointer',
  },
};

export default TrilogyController;
