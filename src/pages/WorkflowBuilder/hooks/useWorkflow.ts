import { useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import type {
  Workflow,
  WorkflowNode,
  WorkflowEdge,
  Trigger,
  NodeType,
  WorkflowVersion,
} from '../types';

interface WorkflowState {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  triggers: Trigger[];
  selectedNodeId: string | null;
  viewport: { x: number; y: number; zoom: number };
  hasUnsavedChanges: boolean;
  setNodes: (nodes: WorkflowNode[]) => void;
  setEdges: (edges: WorkflowEdge[]) => void;
  setTriggers: (triggers: Trigger[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;
  addNode: (node: WorkflowNode) => void;
  updateNode: (id: string, data: Partial<WorkflowNode['data']>) => void;
  deleteNode: (id: string) => void;
  addEdge: (edge: WorkflowEdge) => void;
  deleteEdge: (id: string) => void;
  markSaved: () => void;
  reset: (workflow: Workflow) => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  triggers: [],
  selectedNodeId: null,
  viewport: { x: 0, y: 0, zoom: 1 },
  hasUnsavedChanges: false,

  setNodes: (nodes) => set({ nodes, hasUnsavedChanges: true }),
  setEdges: (edges) => set({ edges, hasUnsavedChanges: true }),
  setTriggers: (triggers) => set({ triggers, hasUnsavedChanges: true }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  setViewport: (viewport) => set({ viewport }),

  addNode: (node) => set({ nodes: [...get().nodes, node], hasUnsavedChanges: true }),
  updateNode: (id, data) => set({
    nodes: get().nodes.map((n) =>
      n.id === id ? { ...n, data: { ...n.data, ...data } } : n
    ),
    hasUnsavedChanges: true,
  }),
  deleteNode: (id) => set({
    nodes: get().nodes.filter((n) => n.id !== id),
    edges: get().edges.filter((e) => e.source !== id && e.target !== id),
    hasUnsavedChanges: true,
  }),

  addEdge: (edge) => set({ edges: [...get().edges, edge], hasUnsavedChanges: true }),
  deleteEdge: (id) => set({
    edges: get().edges.filter((e) => e.id !== id),
    hasUnsavedChanges: true,
  }),

  markSaved: () => set({ hasUnsavedChanges: false }),
  reset: (workflow) => set({
    nodes: workflow.nodes,
    edges: workflow.edges,
    triggers: workflow.triggers,
    hasUnsavedChanges: false,
  }),
}));

async function fetchWorkflow(id: string): Promise<Workflow> {
  const response = await fetch(`/api/workflows/${id}`);
  if (!response.ok) throw new Error('Failed to fetch workflow');
  return response.json();
}

async function saveWorkflow(id: string, data: Partial<Workflow>): Promise<Workflow> {
  const response = await fetch(`/api/workflows/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to save workflow');
  return response.json();
}

async function createWorkflow(data: Partial<Workflow>): Promise<Workflow> {
  const response = await fetch('/api/workflows', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create workflow');
  return response.json();
}

async function publishWorkflow(id: string): Promise<WorkflowVersion> {
  const response = await fetch(`/api/workflows/${id}/publish`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to publish workflow');
  return response.json();
}

async function fetchVersions(workflowId: string): Promise<WorkflowVersion[]> {
  const response = await fetch(`/api/workflows/${workflowId}/versions`);
  if (!response.ok) throw new Error('Failed to fetch versions');
  return response.json();
}

export function useWorkflow(workflowId?: string) {
  const queryClient = useQueryClient();
  const store = useWorkflowStore();

  const { data: workflow, isLoading, error } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => workflowId ? fetchWorkflow(workflowId) : null,
    enabled: !!workflowId,
  });

  const { data: versions } = useQuery({
    queryKey: ['workflow-versions', workflowId],
    queryFn: () => workflowId ? fetchVersions(workflowId) : [],
    enabled: !!workflowId,
  });

  const saveMutation = useMutation({
    mutationFn: (data: Partial<Workflow>) =>
      workflowId ? saveWorkflow(workflowId, data) : createWorkflow(data),
    onSuccess: (savedWorkflow) => {
      store.markSaved();
      queryClient.setQueryData(['workflow', workflowId], savedWorkflow);
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => workflowId ? publishWorkflow(workflowId) : Promise.reject(new Error('No workflow ID')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-versions', workflowId] });
    },
  });

  const generateNodeId = useCallback((type: NodeType): string => {
    return `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const createNode = useCallback((
    type: NodeType,
    position: { x: number; y: number },
    label?: string
  ): WorkflowNode => {
    const id = generateNodeId(type);
    return {
      id,
      type,
      position,
      data: {
        label: label || type,
        config: {},
        inputs: {},
        outputs: {},
        errorHandling: 'fail',
      },
    };
  }, [generateNodeId]);

  const createEdge = useCallback((
    source: string,
    target: string,
    sourceHandle?: string,
    targetHandle?: string
  ): WorkflowEdge => {
    return {
      id: `edge_${source}_${target}`,
      source,
      target,
      sourceHandle,
      targetHandle,
    };
  }, []);

  const selectedNode = useMemo(() =>
    store.nodes.find((n) => n.id === store.selectedNodeId) || null,
    [store.nodes, store.selectedNodeId]
  );

  const handleSave = useCallback(() => {
    saveMutation.mutate({
      nodes: store.nodes,
      edges: store.edges,
      triggers: store.triggers,
    });
  }, [saveMutation, store.nodes, store.edges, store.triggers]);

  const handlePublish = useCallback(() => {
    publishMutation.mutate();
  }, [publishMutation]);

  return {
    workflow,
    versions,
    isLoading,
    error,

    nodes: store.nodes,
    edges: store.edges,
    triggers: store.triggers,
    selectedNodeId: store.selectedNodeId,
    selectedNode,
    viewport: store.viewport,
    hasUnsavedChanges: store.hasUnsavedChanges,

    setNodes: store.setNodes,
    setEdges: store.setEdges,
    setTriggers: store.setTriggers,
    setSelectedNodeId: store.setSelectedNodeId,
    setViewport: store.setViewport,
    addNode: store.addNode,
    updateNode: store.updateNode,
    deleteNode: store.deleteNode,
    addEdge: store.addEdge,
    deleteEdge: store.deleteEdge,

    createNode,
    createEdge,
    generateNodeId,

    save: handleSave,
    publish: handlePublish,
    isSaving: saveMutation.isPending,
    isPublishing: publishMutation.isPending,
    saveError: saveMutation.error,
  };
}

export default useWorkflow;
