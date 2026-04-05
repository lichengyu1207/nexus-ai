import { useState, useCallback, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import type { WorkflowExecution, NodeExecution, NodeStatus } from '../types';

interface ExecutionState {
  executionId: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed';
  nodeStatuses: Record<string, NodeStatus>;
  logs: ExecutionLog[];
  inputs: unknown;
  outputs: unknown;
}

interface ExecutionLog {
  timestamp: string;
  nodeId?: string;
  message: string;
  type: 'info' | 'error' | 'warning' | 'success';
}

async function startTestExecution(workflowId: string, inputs: unknown): Promise<{ executionId: string }> {
  const response = await fetch(`/api/workflows/${workflowId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputs }),
  });
  if (!response.ok) throw new Error('Failed to start test execution');
  return response.json();
}

async function fetchExecution(executionId: string): Promise<WorkflowExecution> {
  const response = await fetch(`/api/workflows/executions/${executionId}`);
  if (!response.ok) throw new Error('Failed to fetch execution');
  return response.json();
}

export function useWorkflowExecution(workflowId?: string) {
  const [state, setState] = useState<ExecutionState>({
    executionId: null,
    status: 'idle',
    nodeStatuses: {},
    logs: [],
    inputs: null,
    outputs: null,
  });

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const updateFromExecution = useCallback((execution: WorkflowExecution) => {
    const nodeStatuses: Record<string, NodeStatus> = {};
    const newLogs: ExecutionLog[] = [];

    execution.nodeExecutions.forEach((nodeExec: NodeExecution) => {
      nodeStatuses[nodeExec.nodeId] = nodeExec.status;

      if (nodeExec.status === 'running') {
        newLogs.push({
          timestamp: nodeExec.startedAt,
          nodeId: nodeExec.nodeId,
          message: `节点 ${nodeExec.nodeId} 开始执行`,
          type: 'info',
        });
      } else if (nodeExec.status === 'completed') {
        newLogs.push({
          timestamp: nodeExec.endedAt || nodeExec.startedAt,
          nodeId: nodeExec.nodeId,
          message: `节点 ${nodeExec.nodeId} 执行完成`,
          type: 'success',
        });
      } else if (nodeExec.status === 'failed') {
        newLogs.push({
          timestamp: nodeExec.endedAt || nodeExec.startedAt,
          nodeId: nodeExec.nodeId,
          message: `节点 ${nodeExec.nodeId} 执行失败: ${nodeExec.error}`,
          type: 'error',
        });
      }
    });

    setState((prev) => ({
      ...prev,
      status: execution.status === 'running' ? 'running' : execution.status,
      nodeStatuses,
      outputs: execution.outputs,
      logs: [...prev.logs, ...newLogs],
    }));
  }, []);

  const startPolling = useCallback((executionId: string) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        const execution = await fetchExecution(executionId);
        updateFromExecution(execution);

        if (execution.status === 'completed' || execution.status === 'failed') {
          stopPolling();
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 1000);
  }, [updateFromExecution, stopPolling]);

  const startMutation = useMutation({
    mutationFn: (inputs: unknown) =>
      workflowId ? startTestExecution(workflowId, inputs) : Promise.reject(new Error('No workflow ID')),
    onSuccess: (data) => {
      setState((prev) => ({
        ...prev,
        executionId: data.executionId,
        status: 'running',
        logs: [
          ...prev.logs,
          { timestamp: new Date().toISOString(), message: '开始执行工作流', type: 'info' },
        ],
      }));
      startPolling(data.executionId);
    },
    onError: (error) => {
      setState((prev) => ({
        ...prev,
        status: 'failed',
        logs: [
          ...prev.logs,
          { timestamp: new Date().toISOString(), message: `启动失败: ${error}`, type: 'error' },
        ],
      }));
    },
  });

  const startExecution = useCallback((inputs: unknown) => {
    setState((prev) => ({
      ...prev,
      status: 'running',
      logs: [],
      inputs,
      outputs: null,
      nodeStatuses: {},
    }));
    startMutation.mutate(inputs);
  }, [startMutation]);

  const stopExecution = useCallback(() => {
    stopPolling();
    setState((prev) => ({
      ...prev,
      status: 'idle',
      logs: [
        ...prev.logs,
        { timestamp: new Date().toISOString(), message: '执行已停止', type: 'warning' },
      ],
    }));
  }, [stopPolling]);

  const resetExecution = useCallback(() => {
    stopPolling();
    setState({
      executionId: null,
      status: 'idle',
      nodeStatuses: {},
      logs: [],
      inputs: null,
      outputs: null,
    });
  }, [stopPolling]);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    executionId: state.executionId,
    status: state.status,
    nodeStatuses: state.nodeStatuses,
    logs: state.logs,
    inputs: state.inputs,
    outputs: state.outputs,

    startExecution,
    stopExecution,
    resetExecution,

    isStarting: startMutation.isPending,
    startError: startMutation.error,
  };
}

export default useWorkflowExecution;
