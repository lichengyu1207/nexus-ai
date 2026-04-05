import React, { useEffect, useCallback, useRef, useState, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { useDemoStore } from '@/stores/demoStore';
import DynamicInput from './DynamicInput';
import AgentIconsGrid from './AgentIconsGrid';
import DataFlowCanvas from './DataFlowCanvas';
import MemoryParticles from './MemoryParticles';
import LiveReportPreview from './LiveReportPreview';
import scene2Script from '@/data/scene2Script.json';
import reportScript from '@/data/reportScript.json';
import { SoundEffects } from '@/components/trilogy/SoundEffects';

const TrilogyController = lazy(() => import('@/components/trilogy/TrilogyController'));

const DemoShowcase: React.FC = () => {
  const { 
    currentScene, 
    isPlaying, 
    startDemo, 
    resetDemo, 
    setScene, 
    setAgentStatus, 
    addReportSection 
  } = useDemoStore();
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const sceneTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  
  const { ref, inView } = useInView({
    threshold: 0.3,
    triggerOnce: false,
  });

  useEffect(() => {
    if (inView && !isInitialized) {
      setIsInitialized(true);
      SoundEffects.initialize().catch(console.warn);
    }
  }, [inView, isInitialized]);

  const runScene2Script = useCallback(() => {
    let scriptIndex = 0;
    const script = scene2Script as Array<{ time: number; agent: string; status: string; message: string }>;
    
    const executeScript = () => {
      if (scriptIndex >= script.length) {
        setTimeout(() => setScene('scene3'), 1000);
        return;
      }
      
      const item = script[scriptIndex];
      setAgentStatus(item.agent, item.status as 'idle' | 'working' | 'done', item.message);
      scriptIndex++;
      
      if (scriptIndex < script.length) {
        const nextDelay = (script[scriptIndex].time - item.time) * 1000;
        timerRef.current = setTimeout(executeScript, nextDelay);
      } else {
        setTimeout(() => setScene('scene3'), 1000);
      }
    };
    
    executeScript();
  }, [setAgentStatus, setScene]);

  const runReportScript = useCallback(() => {
    let sectionIndex = 0;
    const script = reportScript as Array<{ time: number; section: string; title: string; content: string }>;
    
    const executeScript = () => {
      if (sectionIndex >= script.length) {
        return;
      }
      
      const item = script[sectionIndex];
      addReportSection({
        type: item.section,
        title: item.title,
        content: item.content,
        visible: true,
      });
      sectionIndex++;
      
      if (sectionIndex < script.length) {
        const nextDelay = (script[sectionIndex].time - item.time) * 1000;
        sceneTimerRef.current = setTimeout(executeScript, nextDelay);
      }
    };
    
    executeScript();
  }, [addReportSection]);

  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (sceneTimerRef.current) clearTimeout(sceneTimerRef.current);
      return;
    }

    if (currentScene === 'scene1') {
      const timer = setTimeout(() => {
        setScene('scene2');
        runScene2Script();
      }, 3000);
      return () => clearTimeout(timer);
    }

    if (currentScene === 'scene3') {
      runReportScript();
    }
  }, [isPlaying, currentScene, setScene, runScene2Script, runReportScript]);

  const handleStart = useCallback((input?: string) => {
    startDemo(input);
    SoundEffects.playTone(440, 0.15, 'sine');
  }, [startDemo]);

  const handleReset = useCallback(() => {
    resetDemo();
    if (timerRef.current) clearTimeout(timerRef.current);
    if (sceneTimerRef.current) clearTimeout(sceneTimerRef.current);
  }, [resetDemo]);

  return (
    <section className="py-8" ref={ref}>
      <div className="max-w-6xl mx-auto px-4">
        <Suspense fallback={
          <div className="min-h-[600px] flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 rounded-2xl">
            <div className="text-white text-center">
              <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p>加载智能演示...</p>
            </div>
          </div>
        }>
          <TrilogyController />
        </Suspense>
      </div>
    </section>
  );
};

export default DemoShowcase;
