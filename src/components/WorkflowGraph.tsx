import React, { useState, useEffect } from 'react';
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  Node,
  Edge
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

interface WorkflowGraphProps {
  taskId: string;
}

interface SubTask {
  id: string;
  type: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration: number | null;
  error: string | null;
  dependencies: string[];
  parameters: Record<string, any>;
}

const WorkflowGraph: React.FC<WorkflowGraphProps> = ({ taskId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    if (taskId) {
      loadWorkflowData();
    }
  }, [taskId]);

  const loadWorkflowData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/tasks/${taskId}`);
      const task = response.data;
      
      if (task.subtasks) {
        const newNodes: Node[] = task.subtasks.map((subtask: SubTask, index: number) => {
          let color = '#e0e0e0';
          if (subtask.status === 'running') {
            color = '#ffd700';
          } else if (subtask.status === 'completed') {
            color = '#4caf50';
          } else if (subtask.status === 'failed') {
            color = '#f44336';
          }

          return {
            id: subtask.id,
            type: 'default',
            data: {
              label: subtask.type,
              status: subtask.status,
              start_time: subtask.start_time,
              end_time: subtask.end_time,
              duration: subtask.duration,
              error: subtask.error,
              parameters: subtask.parameters
            },
            position: {
              x: 100 + (index % 3) * 200,
              y: 100 + Math.floor(index / 3) * 150
            },
            style: {
              backgroundColor: color,
              borderRadius: '50%',
              width: 60,
              height: 60,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '12px',
              fontWeight: 'bold'
            }
          };
        });

        const newEdges: Edge[] = [];
        task.subtasks.forEach((subtask: SubTask) => {
          subtask.dependencies.forEach((depId: string) => {
            newEdges.push({
              id: `${depId}-${subtask.id}`,
              source: depId,
              target: subtask.id,
              style: {
                stroke: '#ccc',
                strokeWidth: 2
              },
              type: 'arrow'
            });
          });
        });

        setNodes(newNodes);
        setEdges(newEdges);
      }
    } catch (err) {
      setError('加载工作流数据失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const onConnect = (params: any) => setEdges((eds) => addEdge(params, eds));

  const onNodeClick = (event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center text-red-500">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!taskId) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center text-gray-500">
          <p>请输入任务ID</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-96 w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="absolute right-0 top-0 h-full w-80 bg-white shadow-lg p-4 overflow-y-auto"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">子任务详情</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">类型</label>
                <p className="text-sm">{selectedNode.data.label}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">状态</label>
                <p className={`text-sm font-medium ${
                  selectedNode.data.status === 'completed' ? 'text-green-600' :
                  selectedNode.data.status === 'running' ? 'text-yellow-600' :
                  selectedNode.data.status === 'failed' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {selectedNode.data.status}
                </p>
              </div>
              
              {selectedNode.data.start_time && (
                <div>
                  <label className="text-sm font-medium text-gray-500">开始时间</label>
                  <p className="text-sm">{new Date(selectedNode.data.start_time).toLocaleString()}</p>
                </div>
              )}
              
              {selectedNode.data.end_time && (
                <div>
                  <label className="text-sm font-medium text-gray-500">结束时间</label>
                  <p className="text-sm">{new Date(selectedNode.data.end_time).toLocaleString()}</p>
                </div>
              )}
              
              {selectedNode.data.duration && (
                <div>
                  <label className="text-sm font-medium text-gray-500">耗时</label>
                  <p className="text-sm">{selectedNode.data.duration}秒</p>
                </div>
              )}
              
              {selectedNode.data.error && (
                <div>
                  <label className="text-sm font-medium text-gray-500">错误信息</label>
                  <p className="text-sm text-red-600">{selectedNode.data.error}</p>
                </div>
              )}
              
              {selectedNode.data.parameters && Object.keys(selectedNode.data.parameters).length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500">参数</label>
                  <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                    {JSON.stringify(selectedNode.data.parameters, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default WorkflowGraph;
