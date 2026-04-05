import { useQuery } from '@tanstack/react-query';
import type { LineageData, LineageNode, LineageEdge } from '../types';

const API_BASE = '/api/assets';

async function fetchLineage(id: string, depth: number = 2): Promise<LineageData> {
  const response = await fetch(`${API_BASE}/${id}/lineage?depth=${depth}`);
  if (!response.ok) {
    throw new Error('Failed to fetch lineage data');
  }
  return response.json();
}

export interface UseLineageOptions {
  assetId: string | null;
  depth?: number;
  enabled?: boolean;
}

export function useLineage(options: UseLineageOptions) {
  const { assetId, depth = 2, enabled = true } = options;

  const query = useQuery({
    queryKey: ['lineage', assetId, depth],
    queryFn: () => fetchLineage(assetId!, depth),
    enabled: !!assetId && enabled,
    staleTime: 10 * 60 * 1000,
  });

  const findNode = (nodeId: string): LineageNode | undefined => {
    return query.data?.nodes.find((n) => n.id === nodeId);
  };

  const findEdges = (nodeId: string): { incoming: LineageEdge[]; outgoing: LineageEdge[] } => {
    const incoming: LineageEdge[] = [];
    const outgoing: LineageEdge[] = [];

    query.data?.edges.forEach((edge) => {
      if (edge.target === nodeId) incoming.push(edge);
      if (edge.source === nodeId) outgoing.push(edge);
    });

    return { incoming, outgoing };
  };

  const getUpstreamNodes = (nodeId: string): LineageNode[] => {
    const { incoming } = findEdges(nodeId);
    return incoming
      .map((edge) => findNode(edge.source))
      .filter((n): n is LineageNode => n !== undefined);
  };

  const getDownstreamNodes = (nodeId: string): LineageNode[] => {
    const { outgoing } = findEdges(nodeId);
    return outgoing
      .map((edge) => findNode(edge.target))
      .filter((n): n is LineageNode => n !== undefined);
  };

  return {
    nodes: query.data?.nodes ?? [],
    edges: query.data?.edges ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    findNode,
    findEdges,
    getUpstreamNodes,
    getDownstreamNodes,
  };
}
