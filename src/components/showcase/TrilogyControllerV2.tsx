import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDemoStore } from '../../stores/demoStore';
import TaskInput from './TaskInput';
import AgentCluster from './AgentCluster';
import LiveReportPreview from './LiveReportPreview';
import MemoryTimeline from './MemoryTimeline';
import MemoryGraphVisualization from './MemoryGraphVisualization';
import PersonalitySelector from './PersonalitySelector';
import EvolutionProgressPanel from './EvolutionProgressPanel';
import taskApi, { Task } from '../../api/task';

type SceneType = 'idle' | 'scene1' | 'scene2' | 'scene3' | 'complete';

interface TrilogyControllerV2Props {
  autoPlay?: boolean;
  height?: number | string;
  onComplete?: () => void;
}

const TrilogyControllerV2: React.FC<TrilogyControllerV2Props> = ({
  autoPlay = false,
  height = 600,
  onComplete,
}) => {
  const {
    currentScene,
    userInput,
    agentsStatus,
    reportData,
    isPlaying,
    lightBeams,
    dataFlows,
    setScene,
    setAgentStatus,
    addReportSection,
    addLightBeam,
    addDataFlow,
    resetDemo,
    startDemo,
  } = useDemoStore();

  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<any>(null);
  const [evolutionProgress, setEvolutionProgress] = useState(0);
  const [experience, setExperience] = useState(0);
  const [level, setLevel] = useState(1);
  const [userInteracted, setUserInteracted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动播放逻辑：页面加载时自动开始演示
  useEffect(() => {
    if (autoPlay && !userInteracted && currentScene === 'idle') {
      const timer = setTimeout(() => {
        startDemo();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [autoPlay, userInteracted, currentScene, startDemo]);

  // 用户交互检测：点击时停止自动播放
  const handleUserInteraction = useCallback(() => {
    setUserInteracted(true);
  }, []);

  const handleTaskCreated = useCallback((task: Task) => {
    setUserInteracted(true);
    setCurrentTask(task);
    setScene('scene1');
  }, [setScene]);

  const handleScene1Complete = useCallback(() => {
    setTimeout(() => {
      setScene('scene2');
    }, 1000);
  }, [setScene]);

  const handleScene2Complete = useCallback(() => {
    setTimeout(() => {
      setScene('scene3');
    }, 500);
  }, [setScene]);

  const handleScene3Complete = useCallback(() => {
    setEvolutionProgress(100);
    setTimeout(() => {
      setScene('complete');
      onComplete?.();
    }, 2000);
  }, [setScene, onComplete]);

  const handleMemorySelect = useCallback((memory: any) => {
    setSelectedMemory(memory);
  }, []);

  const handleMemoryReplay = useCallback((memory: any) => {
    setExperience((prev) => prev + 50);
    setEvolutionProgress((prev) => Math.min(100, prev + 10));
  }, []);

  const handlePersonalitySelect = useCallback(() => {
    setExperience((prev) => prev + 100);
    setEvolutionProgress((prev) => Math.min(100, prev + 20));
  }, []);

  const handleEvolution = useCallback(() => {
    setLevel((prev) => prev + 1);
    setExperience(0);
    setEvolutionProgress(0);
  }, []);

  const handleReplay = useCallback(() => {
    resetDemo();
    setCurrentTask(null);
    setSelectedMemory(null);
    setEvolutionProgress(0);
    setExperience(0);
    setLevel(1);
  }, [resetDemo]);

  const sceneLabels = {
    idle: '开始',
    scene1: '需求分析',
    scene2: '记忆挖掘',
    scene3: '人格进化',
    complete: '完成',
  };

  return (
    <div
      ref={containerRef}
      style={{
        height,
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.98))',
        borderRadius: '20px',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(0, 0, 0, 0.3)',
        position: 'relative',
        zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <motion.div
            animate={{ rotate: isPlaying ? 360 : 0 }}
            transition={{ duration: 2, repeat: isPlaying ? Infinity : 0, ease: 'linear' }}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '18px',
            }}
          >
            🏠
          </motion.div>
          <div>
            <h2 style={{
              color: '#D4AF37',
              fontSize: '18px',
              fontWeight: 700,
              margin: 0,
            }}>
              房都督AI · 智能决策中枢
            </h2>
            <p style={{
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '12px',
              margin: '4px 0 0 0',
            }}>
              三部曲动态演示
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {(['idle', 'scene1', 'scene2', 'scene3'] as SceneType[]).map((scene, index) => (
            <div
              key={scene}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <div
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: currentScene === scene
                    ? 'linear-gradient(135deg, #D4AF37, #F59E0B)'
                    : currentScene === 'complete'
                    ? '#10B981'
                    : 'rgba(255, 255, 255, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  color: currentScene === scene || currentScene === 'complete' ? '#0f172a' : 'rgba(255, 255, 255, 0.5)',
                  fontWeight: 600,
                }}
              >
                {index + 1}
              </div>
              <span style={{
                color: currentScene === scene ? '#D4AF37' : 'rgba(255, 255, 255, 0.5)',
                fontSize: '12px',
              }}>
                {sceneLabels[scene]}
              </span>
              {index < 3 && (
                <div style={{
                  width: '20px',
                  height: '2px',
                  background: 'rgba(255, 255, 255, 0.2)',
                  marginLeft: '4px',
                }} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '20px',
      }}>
        <AnimatePresence mode="wait">
          {currentScene === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
              }}
            >
              <motion.div
                animate={{
                  boxShadow: [
                    '0 0 30px rgba(212, 175, 55, 0.3)',
                    '0 0 60px rgba(212, 175, 55, 0.6)',
                    '0 0 30px rgba(212, 175, 55, 0.3)',
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.1))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '24px',
                  border: '2px solid rgba(212, 175, 55, 0.4)',
                }}
              >
                <span style={{ fontSize: '40px' }}>🏠</span>
              </motion.div>

              <h1 style={{
                color: '#D4AF37',
                fontSize: '32px',
                fontWeight: 700,
                margin: '0 0 8px 0',
                textShadow: '0 0 30px rgba(212, 175, 55, 0.3)',
              }}>
                房都督AI
              </h1>

              <p style={{
                color: 'rgba(255, 255, 255, 0.6)',
                fontSize: '16px',
                margin: '0 0 32px 0',
              }}>
                六部智能体协同 · 海马体记忆挖掘 · 自我进化系统
              </p>

              <TaskInput
                onTaskCreated={handleTaskCreated}
                popularTasks={[
                  { title: '深圳南山区学区房分析', description: '热门' },
                  { title: '北京朝阳区写字楼评估', description: '热门' },
                  { title: '上海浦东别墅市场趋势', description: '热门' },
                ]}
                autoFocus={autoPlay}
              />
            </motion.div>
          )}

          {currentScene === 'scene1' && currentTask && (
            <motion.div
              key="scene1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
                height: '100%',
              }}
            >
              <AgentCluster
                taskId={currentTask.id}
                onComplete={handleScene1Complete}
              />

              <LiveReportPreview
                taskId={currentTask.id}
                onComplete={handleScene1Complete}
                compact
              />
            </motion.div>
          )}

          {currentScene === 'scene2' && (
            <motion.div
              key="scene2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '20px',
                height: '100%',
              }}
            >
              <MemoryTimeline
                taskId={currentTask?.id}
                onMemorySelect={handleMemorySelect}
                onMemoryReplay={handleMemoryReplay}
                isActive
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <MemoryGraphVisualization
                  taskId={currentTask?.id}
                  onNodeSelect={handleMemorySelect}
                  isActive
                  compact
                  height={250}
                />

                <EvolutionProgressPanel
                  currentProgress={evolutionProgress}
                  experience={experience}
                  level={level}
                  isActive
                  onEvolution={handleEvolution}
                  compact
                />
              </div>
            </motion.div>
          )}

          {currentScene === 'scene3' && (
            <motion.div
              key="scene3"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                gap: '24px',
              }}
            >
              <PersonalitySelector
                onSelect={handlePersonalitySelect}
                compact
              />

              <EvolutionProgressPanel
                currentProgress={evolutionProgress}
                experience={experience}
                level={level}
                isActive
                onEvolution={handleScene3Complete}
              />
            </motion.div>
          )}

          {currentScene === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
              }}
            >
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  rotate: [0, 10, -10, 0],
                }}
                transition={{ duration: 0.5 }}
                style={{ fontSize: '64px', marginBottom: '24px' }}
              >
                🎉
              </motion.div>

              <h2 style={{
                color: '#D4AF37',
                fontSize: '28px',
                fontWeight: 700,
                margin: '0 0 12px 0',
              }}>
                演示完成！
              </h2>

              <p style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '16px',
                margin: '0 0 24px 0',
                maxWidth: '400px',
              }}>
                您已体验了房都督AI的核心能力：智能体协同、记忆挖掘、自我进化
              </p>

              <div style={{
                display: 'flex',
                gap: '16px',
                marginBottom: '24px',
              }}>
                <div style={{
                  textAlign: 'center',
                  padding: '16px 24px',
                  background: 'rgba(212, 175, 55, 0.1)',
                  borderRadius: '12px',
                }}>
                  <span style={{
                    display: 'block',
                    color: '#D4AF37',
                    fontSize: '24px',
                    fontWeight: 700,
                  }}>
                    6
                  </span>
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                  }}>
                    智能体协作
                  </span>
                </div>
                <div style={{
                  textAlign: 'center',
                  padding: '16px 24px',
                  background: 'rgba(139, 92, 246, 0.1)',
                  borderRadius: '12px',
                }}>
                  <span style={{
                    display: 'block',
                    color: '#8B5CF6',
                    fontSize: '24px',
                    fontWeight: 700,
                  }}>
                    {level}
                  </span>
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                  }}>
                    进化等级
                  </span>
                </div>
                <div style={{
                  textAlign: 'center',
                  padding: '16px 24px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  borderRadius: '12px',
                }}>
                  <span style={{
                    display: 'block',
                    color: '#10B981',
                    fontSize: '24px',
                    fontWeight: 700,
                  }}>
                    3
                  </span>
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '12px',
                  }}>
                    新能力解锁
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <motion.button
                  onClick={handleReplay}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '12px 24px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                >
                  再看一次
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '12px 24px',
                    background: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#0f172a',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  开始使用 →
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default TrilogyControllerV2;
