/**
 * 智能体点击交互组件
 * Agent Clickable Interaction Component
 * 
 * 处理智能体点击、长按、拖拽等交互
 */

import React, { useState, useRef, useCallback, useEffect, memo } from 'react';
import { motion, AnimatePresence, useDragControls } from 'framer-motion';
import AgentAnimation, { AgentStatus, AgentDepartment } from './AgentAnimation';

export interface AgentTask {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
}

export interface AgentInfo {
  id: string;
  name: string;
  department: AgentDepartment;
  status: AgentStatus;
  level: number;
  energy: number;
  maxEnergy: number;
  tasks: AgentTask[];
  description: string;
  lastActive: Date;
}

export interface AgentClickableProps {
  agent: AgentInfo;
  onAssignTask?: (agentId: string) => void;
  onViewLogs?: (agentId: string) => void;
  onStartChat?: (agentId: string) => void;
  onDragToTask?: (agentId: string, taskId: string) => void;
  className?: string;
}

interface DetailCardProps {
  agent: AgentInfo;
  position: { x: number; y: number };
  onClose: () => void;
  onAssignTask: () => void;
  onViewLogs: () => void;
  onStartChat: () => void;
}

const DetailCard: React.FC<DetailCardProps> = memo(({
  agent,
  position,
  onClose,
  onAssignTask,
  onViewLogs,
  onStartChat,
}) => {
  const energyPercentage = (agent.energy / agent.maxEnergy) * 100;
  
  return (
    <motion.div
      className="fixed z-50 bg-white rounded-xl shadow-2xl overflow-hidden"
      style={{
        left: Math.min(position.x, window.innerWidth - 320),
        top: Math.min(position.y, window.innerHeight - 400),
      }}
      initial={{ opacity: 0, scale: 0.9, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <div 
        className="h-2"
        style={{ 
          background: `linear-gradient(90deg, 
            ${energyPercentage > 50 ? '#22C55E' : energyPercentage > 20 ? '#EAB308' : '#EF4444'} 
            ${energyPercentage}%, 
            #E5E7EB ${energyPercentage}%)` 
        }}
      />
      
      <div className="p-4 w-72">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <AgentAnimation
              agentId={agent.id}
              department={agent.department}
              status={agent.status}
              size="small"
              showLabel={false}
            />
            <div>
              <h3 className="font-bold text-gray-800">{agent.name}</h3>
              <span className="text-xs text-gray-500">Lv.{agent.level}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500"
          >
            ✕
          </button>
        </div>
        
        <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
        
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>能量值</span>
            <span>{agent.energy}/{agent.maxEnergy}</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ 
                backgroundColor: energyPercentage > 50 ? '#22C55E' : energyPercentage > 20 ? '#EAB308' : '#EF4444'
              }}
              initial={{ width: 0 }}
              animate={{ width: `${energyPercentage}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
        
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-500 mb-2">最近任务</h4>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {agent.tasks.slice(0, 3).map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-2 text-xs p-1.5 bg-gray-50 rounded"
              >
                <span className={`w-2 h-2 rounded-full ${
                  task.status === 'completed' ? 'bg-green-500' :
                  task.status === 'running' ? 'bg-blue-500' :
                  task.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                }`} />
                <span className="flex-1 truncate">{task.name}</span>
              </div>
            ))}
            {agent.tasks.length === 0 && (
              <span className="text-xs text-gray-400">暂无任务</span>
            )}
          </div>
        </div>
        
        <div className="flex gap-2">
          <motion.button
            className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onAssignTask}
          >
            分配任务
          </motion.button>
          <motion.button
            className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onViewLogs}
          >
            查看日志
          </motion.button>
        </div>
        
        <motion.button
          className="w-full mt-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm rounded-lg"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStartChat}
        >
          💬 与智能体对话
        </motion.button>
      </div>
    </motion.div>
  );
});

DetailCard.displayName = 'DetailCard';

const AgentClickable: React.FC<AgentClickableProps> = memo(({
  agent,
  onAssignTask,
  onViewLogs,
  onStartChat,
  onDragToTask,
  className = '',
}) => {
  const [showDetail, setShowDetail] = useState(false);
  const [detailPosition, setDetailPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isLongPress, setIsLongPress] = useState(false);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const dragControls = useDragControls();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (isDragging || isLongPress) return;
    
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setDetailPosition({
      x: rect.right + 10,
      y: rect.top,
    });
    setShowDetail(true);
  }, [isDragging, isLongPress]);

  const handleClose = useCallback(() => {
    setShowDetail(false);
  }, []);

  const handleMouseDown = useCallback(() => {
    longPressTimerRef.current = setTimeout(() => {
      setIsLongPress(true);
    }, 500);
  }, []);

  const handleMouseUp = useCallback(() => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
    }
    setTimeout(() => setIsLongPress(false), 100);
  }, []);

  const handleDragStart = useCallback(() => {
    setIsDragging(true);
    setShowDetail(false);
  }, []);

  const handleDragEnd = useCallback((event: MouseEvent | TouchEvent | PointerEvent, info: { point: { x: number; y: number } }) => {
    setIsDragging(false);
    
    const dropZone = document.elementFromPoint(info.point.x, info.point.y);
    if (dropZone?.hasAttribute('data-task-zone')) {
      const taskId = dropZone.getAttribute('data-task-id');
      if (taskId) {
        onDragToTask?.(agent.id, taskId);
      }
    }
  }, [agent.id, onDragToTask]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDetail(false);
      }
    };

    if (showDetail) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, [showDetail]);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <motion.div
        drag
        dragControls={dragControls}
        dragElastic={0.1}
        dragMomentum={false}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd as any}
        whileDrag={{ scale: 1.1, zIndex: 100 }}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <AgentAnimation
          agentId={agent.id}
          department={agent.department}
          status={agent.status}
          onClick={handleClick}
        />
      </motion.div>
      
      {isLongPress && (
        <motion.div
          className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          拖拽到任务区域
        </motion.div>
      )}
      
      <AnimatePresence>
        {showDetail && (
          <DetailCard
            agent={agent}
            position={detailPosition}
            onClose={handleClose}
            onAssignTask={() => {
              onAssignTask?.(agent.id);
              handleClose();
            }}
            onViewLogs={() => {
              onViewLogs?.(agent.id);
              handleClose();
            }}
            onStartChat={() => {
              onStartChat?.(agent.id);
              handleClose();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
});

AgentClickable.displayName = 'AgentClickable';

export default AgentClickable;
