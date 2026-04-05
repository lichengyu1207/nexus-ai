/**
 * 智能体工作流动画组件
 * Agent Workflow Animation Component
 * 
 * 展示智能体执行任务的动态过程
 */

import React, { useState, useEffect, useMemo, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentAnimation, { AgentDepartment, AgentStatus } from './AgentAnimation';

export interface WorkflowStep {
  id: string;
  name: string;
  agentId: string;
  agentDepartment: AgentDepartment;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  details?: string;
}

export interface WorkflowData {
  id: string;
  name: string;
  steps: WorkflowStep[];
  currentStepIndex: number;
  startTime: Date;
  estimatedEndTime?: Date;
}

export interface AgentWorkflowAnimationProps {
  workflow: WorkflowData;
  onStepClick?: (step: WorkflowStep) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

const FlowingDots: React.FC<{ isFlowing: boolean; color: string }> = memo(({ isFlowing, color }) => (
  <div className="flex-1 h-1 relative overflow-hidden">
    <div className="absolute inset-0 bg-gray-200" />
    {isFlowing && (
      <>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute top-1/2 transform -translate-y-1/2 w-2 h-2 rounded-full"
            style={{ backgroundColor: color }}
            initial={{ left: '0%' }}
            animate={{ left: '100%' }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.5,
              ease: 'linear',
            }}
          />
        ))}
      </>
    )}
  </div>
));

FlowingDots.displayName = 'FlowingDots';

const WorkflowStepNode: React.FC<{
  step: WorkflowStep;
  isActive: boolean;
  isCompleted: boolean;
  onClick?: () => void;
}> = memo(({ step, isActive, isCompleted, onClick }) => {
  const status: AgentStatus = isActive ? 'busy' : isCompleted ? 'success' : 'idle';
  
  return (
    <motion.div
      className={`
        relative flex flex-col items-center cursor-pointer
        ${isActive ? 'z-10' : ''}
      `}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
    >
      <motion.div
        className={`relative ${isActive ? 'scale-110' : ''}`}
        animate={isActive ? {
          boxShadow: [
            '0 0 0 0 rgba(59, 130, 246, 0.4)',
            '0 0 0 15px rgba(59, 130, 246, 0)',
          ],
        } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <AgentAnimation
          agentId={step.agentId}
          department={step.agentDepartment}
          status={status}
          size="small"
          showLabel={false}
        />
        
        {isCompleted && (
          <motion.div
            className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            <span className="text-white text-xs">✓</span>
          </motion.div>
        )}
        
        {step.status === 'failed' && (
          <motion.div
            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            <span className="text-white text-xs">✕</span>
          </motion.div>
        )}
      </motion.div>
      
      <span className={`
        text-xs mt-1 text-center max-w-16 truncate
        ${isActive ? 'font-bold text-blue-600' : 'text-gray-500'}
      `}>
        {step.name}
      </span>
    </motion.div>
  );
});

WorkflowStepNode.displayName = 'WorkflowStepNode';

const StepDetailModal: React.FC<{
  step: WorkflowStep;
  onClose: () => void;
}> = memo(({ step, onClose }) => (
  <motion.div
    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    onClick={onClose}
  >
    <motion.div
      className="bg-white rounded-xl p-6 w-96 shadow-2xl"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">{step.name}</h3>
        <span className={`
          px-2 py-1 rounded-full text-xs
          ${step.status === 'completed' ? 'bg-green-100 text-green-700' :
            step.status === 'running' ? 'bg-blue-100 text-blue-700' :
            step.status === 'failed' ? 'bg-red-100 text-red-700' : 
            'bg-gray-100 text-gray-700'}
        `}>
          {step.status === 'completed' ? '已完成' :
           step.status === 'running' ? '进行中' :
           step.status === 'failed' ? '失败' : '待执行'}
        </span>
      </div>
      
      <div className="space-y-3 text-sm">
        <div>
          <span className="text-gray-500">智能体：</span>
          <span className="ml-2">{step.agentId}</span>
        </div>
        
        {step.startTime && (
          <div>
            <span className="text-gray-500">开始时间：</span>
            <span className="ml-2">{step.startTime.toLocaleString()}</span>
          </div>
        )}
        
        {step.endTime && (
          <div>
            <span className="text-gray-500">结束时间：</span>
            <span className="ml-2">{step.endTime.toLocaleString()}</span>
          </div>
        )}
        
        {step.details && (
          <div>
            <span className="text-gray-500">详情：</span>
            <p className="mt-1 p-2 bg-gray-50 rounded text-gray-700">{step.details}</p>
          </div>
        )}
      </div>
      
      <button
        className="mt-4 w-full py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700"
        onClick={onClose}
      >
        关闭
      </button>
    </motion.div>
  </motion.div>
));

StepDetailModal.displayName = 'StepDetailModal';

const AgentWorkflowAnimation: React.FC<AgentWorkflowAnimationProps> = memo(({
  workflow,
  onStepClick,
  collapsed = false,
  onToggleCollapse,
  className = '',
}) => {
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const [progress, setProgress] = useState(0);

  const completedSteps = useMemo(() => 
    workflow.steps.filter(s => s.status === 'completed').length,
    [workflow.steps]
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => (prev + 1) % 100);
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const progressPercentage = (completedSteps / workflow.steps.length) * 100;

  if (collapsed) {
    return (
      <motion.div
        className={`bg-white rounded-lg shadow-md p-3 cursor-pointer ${className}`}
        onClick={onToggleCollapse}
        whileHover={{ scale: 1.02 }}
      >
        <div className="flex items-center gap-3">
          <div className="flex -space-x-2">
            {workflow.steps.slice(0, 3).map((step, i) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <AgentAnimation
                  agentId={step.agentId}
                  department={step.agentDepartment}
                  status={step.status === 'running' ? 'busy' : step.status === 'completed' ? 'success' : 'idle'}
                  size="small"
                  showLabel={false}
                />
              </motion.div>
            ))}
            {workflow.steps.length > 3 && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-600">
                +{workflow.steps.length - 3}
              </div>
            )}
          </div>
          
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">{workflow.name}</span>
              <span className="text-gray-500">{completedSteps}/{workflow.steps.length}</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-blue-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className={`bg-white rounded-xl shadow-lg p-4 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-gray-800">{workflow.name}</h3>
          <span className="text-xs text-gray-500">
            开始于 {workflow.startTime.toLocaleTimeString()}
          </span>
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <span className="text-gray-400">▼</span>
        </button>
      </div>
      
      <div className="flex items-center gap-2 mb-4">
        {workflow.steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <WorkflowStepNode
              step={step}
              isActive={index === workflow.currentStepIndex}
              isCompleted={index < workflow.currentStepIndex || step.status === 'completed'}
              onClick={() => setSelectedStep(step)}
            />
            {index < workflow.steps.length - 1 && (
              <FlowingDots
                isFlowing={index < workflow.currentStepIndex}
                color="#3B82F6"
              />
            )}
          </React.Fragment>
        ))}
      </div>
      
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <span className="text-sm font-medium text-gray-600">
          {Math.round(progressPercentage)}%
        </span>
      </div>
      
      <AnimatePresence>
        {selectedStep && (
          <StepDetailModal
            step={selectedStep}
            onClose={() => setSelectedStep(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
});

AgentWorkflowAnimation.displayName = 'AgentWorkflowAnimation';

export default AgentWorkflowAnimation;
