export interface NodeData {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  position?: [number, number, number];
  color?: string;
  task?: string;
}

export interface EdgeData {
  source: string;
  target: string;
}

export interface TopologyData {
  nodes: NodeData[];
  edges: EdgeData[];
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  value: number;
  name?: string;
}

export interface HeatmapData {
  points: HeatmapPoint[];
}

export type VisualizationMode = 'topology' | 'heatmap';

export interface ThreeDVisualizationProps {
  mode: VisualizationMode;
  data?: TopologyData | HeatmapData;
  className?: string;
  onNodeClick?: (id: string) => void;
}
