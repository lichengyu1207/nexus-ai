import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRightIcon, ChevronDownIcon, ClockIcon } from '@heroicons/react/24/outline';
import type { StackFrame } from '../types';

interface CallStackViewProps {
  stack: StackFrame[];
  onFrameClick?: (frame: StackFrame) => void;
  selectedFrameId?: string;
}

const StackFrameItem = ({ 
  frame, 
  depth = 0, 
  onFrameClick, 
  selectedFrameId 
}: { 
  frame: StackFrame; 
  depth?: number;
  onFrameClick?: (frame: StackFrame) => void;
  selectedFrameId?: string;
}) => {
  const [isExpanded, setIsExpanded] = useState(depth < 1);
  const hasChildren = frame.children && frame.children.length > 0;
  const isSelected = selectedFrameId === frame.id;

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusColor = (status: StackFrame['status']) => {
    switch (status) {
      case 'running': return 'text-amber-400';
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="select-none">
      <div
        onClick={() => onFrameClick?.(frame)}
        className={`
          flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors
          ${isSelected ? 'bg-amber-500/20 border-l-2 border-amber-500' : 'hover:bg-slate-800/50'}
        `}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="p-0.5 rounded hover:bg-slate-700/50"
          >
            {isExpanded ? (
              <ChevronDownIcon className="w-3.5 h-3.5 text-slate-400" />
            ) : (
              <ChevronRightIcon className="w-3.5 h-3.5 text-slate-400" />
            )}
          </button>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${getStatusColor(frame.status)}`}>
              {frame.name}
            </span>
            <span className="text-xs text-slate-500 px-1.5 py-0.5 bg-slate-800/50 rounded">
              {frame.type}
            </span>
          </div>
          {frame.input && (
            <p className="text-xs text-slate-400 truncate mt-0.5">
              {JSON.stringify(frame.input).slice(0, 50)}...
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-3 text-xs text-slate-500">
          {frame.duration && (
            <span className="flex items-center gap-1">
              <ClockIcon className="w-3 h-3" />
              {formatDuration(frame.duration)}
            </span>
          )}
          <span className={getStatusColor(frame.status)}>
            {frame.status}
          </span>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {frame.children!.map((child) => (
              <StackFrameItem
                key={child.id}
                frame={child}
                depth={depth + 1}
                onFrameClick={onFrameClick}
                selectedFrameId={selectedFrameId}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export function CallStackView({ stack, onFrameClick, selectedFrameId }: CallStackViewProps) {
  if (stack.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        暂无调用栈数据
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="py-2">
        {stack.map((frame) => (
          <StackFrameItem
            key={frame.id}
            frame={frame}
            onFrameClick={onFrameClick}
            selectedFrameId={selectedFrameId}
          />
        ))}
      </div>
    </div>
  );
}
