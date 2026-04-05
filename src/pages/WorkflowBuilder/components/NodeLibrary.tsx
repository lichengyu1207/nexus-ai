import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UserIcon,
  WrenchScrewdriverIcon,
  ArrowsRightLeftIcon,
  BoltIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import type { NodeType } from '../types';
import { AGENT_NODES, TOOL_NODES, CONTROL_NODES, TRIGGER_NODES } from '../types';

interface NodeLibraryProps {
  onDragStart: (type: NodeType, config?: Record<string, unknown>) => void;
  onNodeClick: (type: NodeType, config?: Record<string, unknown>) => void;
}

interface NodeCategoryProps {
  title: string;
  icon: React.ReactNode;
  nodes: { id?: string; type?: string; label: string; description: string }[];
  onDragStart: (type: NodeType, config?: Record<string, unknown>) => void;
  onNodeClick: (type: NodeType, config?: Record<string, unknown>) => void;
  defaultExpanded?: boolean;
  nodeType: NodeType;
}

function NodeCategory({
  title,
  icon,
  nodes,
  onDragStart,
  onNodeClick,
  defaultExpanded = true,
  nodeType,
}: NodeCategoryProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="mb-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span>{title}</span>
        </div>
        {isExpanded ? (
          <ChevronDownIcon className="w-4 h-4" />
        ) : (
          <ChevronRightIcon className="w-4 h-4" />
        )}
      </button>

      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="mt-1 space-y-1"
        >
          {nodes.map((node) => (
            <div
              key={node.id || node.type}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('nodeType', nodeType);
                e.dataTransfer.setData('nodeConfig', JSON.stringify({
                  agentId: node.id,
                  label: node.label,
                }));
                onDragStart(nodeType, { agentId: node.id, label: node.label });
              }}
              onClick={() => onNodeClick(nodeType, { agentId: node.id, label: node.label })}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-700/30 rounded-lg cursor-grab active:cursor-grabbing transition-colors"
            >
              <div className="w-6 h-6 rounded bg-slate-700/50 flex items-center justify-center">
                {icon}
              </div>
              <div>
                <p className="text-white">{node.label}</p>
                <p className="text-xs text-slate-500">{node.description}</p>
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

export function NodeLibrary({ onDragStart, onNodeClick }: NodeLibraryProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgentNodes = AGENT_NODES.filter(
    (node) =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      node.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredToolNodes = TOOL_NODES.filter(
    (node) =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      node.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredControlNodes = CONTROL_NODES.filter(
    (node) =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      node.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredTriggerNodes = TRIGGER_NODES.filter(
    (node) =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      node.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-64 bg-slate-800/50 backdrop-blur-sm border-r border-slate-700/50 flex flex-col">
      <div className="p-4 border-b border-slate-700/50">
        <h2 className="text-lg font-semibold text-white mb-3">节点库</h2>
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="搜索节点..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <NodeCategory
          title="智能体节点"
          icon={<UserIcon className="w-4 h-4 text-amber-400" />}
          nodes={filteredAgentNodes}
          nodeType="agent"
          onDragStart={onDragStart}
          onNodeClick={onNodeClick}
          defaultExpanded
        />

        <NodeCategory
          title="工具节点"
          icon={<WrenchScrewdriverIcon className="w-4 h-4 text-blue-400" />}
          nodes={filteredToolNodes}
          nodeType="tool"
          onDragStart={onDragStart}
          onNodeClick={onNodeClick}
          defaultExpanded
        />

        <NodeCategory
          title="控制节点"
          icon={<ArrowsRightLeftIcon className="w-4 h-4 text-orange-400" />}
          nodes={filteredControlNodes}
          nodeType="condition"
          onDragStart={onDragStart}
          onNodeClick={onNodeClick}
          defaultExpanded={false}
        />

        <NodeCategory
          title="触发器"
          icon={<BoltIcon className="w-4 h-4 text-green-400" />}
          nodes={filteredTriggerNodes}
          nodeType="trigger"
          onDragStart={onDragStart}
          onNodeClick={onNodeClick}
          defaultExpanded={false}
        />
      </div>

      <div className="p-3 border-t border-slate-700/50">
        <p className="text-xs text-slate-500 text-center">
          拖拽节点到画布或双击添加
        </p>
      </div>
    </div>
  );
}

export default NodeLibrary;
