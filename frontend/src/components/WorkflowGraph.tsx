import React, { useState, useEffect } from 'react';
import ReactFlow, { MiniMap, Controls, Background, useNodesState, useEdgesState, addEdge } from 'react-flow-renderer';
import 'react-flow-renderer/dist/style.css';
import axios from 'axios';

interface WorkflowGraphProps {
  taskId: string;
}

const WorkflowGraph: React.FC<WorkflowGraphProps> = ({ taskId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        // 构建节点
        const newNodes = task.subtasks.map((subtask: any, index: number) => {
          let color = '#e0e0e0'; // 灰色 - pending
          if (subtask.status === 'running') {
            color = '#ffd700'; // 金色 - running
          } else if (subtask.status === 'completed') {
            color = '#4caf50'; // 绿色 - completed
          } else if (subtask.status === 'failed') {
            color = '#f44336'; // 红色 - failed
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
              error: subtask.error
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
              justifyContent: 'center'
            }
          };
        });

        // 构建边
        const newEdges = [];
        task.subtasks.forEach((subtask: any) => {
          subtask.dependencies.forEach((depId: string) => {
            newEdges.push({
              id: `${depId}-${subtask.id}`,
              source: depId,
              target: subtask.id,
              style: {
                stroke: '#ccc',
                strokeDasharray: '5,5'
              },
              arrowHeadType: 'arrow'
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

  if (loading) {
    return <div className="text-center p-lg">加载中...</div>;
  }

  if (error) {
    return <div className="text-center p-lg text-error">{error}</div>;
  }

  if (!taskId) {
    return <div className="text-center p-lg">请输入任务ID</div>;
  }

  return (
    <div style={{ height: 600, width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

export default WorkflowGraph;
