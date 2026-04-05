import * as THREE from 'three';
import { NodeData, HeatmapPoint } from './types';

export const getNodeColor = (status: string): string => {
  switch (status) {
    case 'active':
      return '#FFD966';
    case 'idle':
      return '#6B7280';
    case 'error':
      return '#EF4444';
    default:
      return '#FFD966';
  }
};

export const latLngToPosition = (
  lat: number,
  lng: number,
  scale: number = 0.05
): THREE.Vector3 => {
  const x = lng * scale;
  const z = lat * scale;
  return new THREE.Vector3(x, 0, z);
};

export const getColorByValue = (value: number): THREE.Color => {
  const t = Math.min(1, Math.max(0, value));
  const r = Math.round(255 * t + 0 * (1 - t));
  const g = Math.round(217 * t + 100 * (1 - t));
  const b = Math.round(102 * t + 255 * (1 - t));
  return new THREE.Color(`rgb(${r}, ${g}, ${b})`);
};

export const generateTopologyPositions = (
  nodes: NodeData[],
  radius: number = 2.5
): THREE.Vector3[] => {
  const count = nodes.length;
  const angleStep = (Math.PI * 2) / count;
  return nodes.map((node, i) => {
    if (node.position) {
      return new THREE.Vector3(...node.position);
    }
    const angle = i * angleStep;
    return new THREE.Vector3(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius * 0.5,
      Math.sin(angle) * radius
    );
  });
};

export const calculateHeatmapItems = (
  points: HeatmapPoint[],
  maxHeight: number = 1.5,
  scale: number = 0.05
): Array<{
  point: HeatmapPoint;
  pos: THREE.Vector3;
  height: number;
  color: THREE.Color;
}> => {
  const values = points.map((p) => p.value);
  const maxVal = Math.max(...values, 0.01);

  return points.map((point) => {
    const pos = latLngToPosition(point.lat, point.lng, scale);
    const height = (point.value / maxVal) * maxHeight;
    const color = getColorByValue(point.value / maxVal);
    return { point, pos, height, color };
  });
};

export const DEFAULT_TOPOLOGY_DATA = {
  nodes: [
    { id: 'bing', name: '兵部', status: 'active' as const, task: '数据分析' },
    { id: 'hu', name: '户部', status: 'active' as const, task: '资源调度' },
    { id: 'li', name: '礼部', status: 'idle' as const, task: '待命' },
    { id: 'xing', name: '刑部', status: 'error' as const, task: '异常处理' },
    { id: 'li2', name: '吏部', status: 'active' as const, task: '任务分配' },
    { id: 'gong', name: '工部', status: 'idle' as const, task: '待命' },
  ],
  edges: [
    { source: 'bing', target: 'hu' },
    { source: 'hu', target: 'li' },
    { source: 'li', target: 'xing' },
    { source: 'xing', target: 'bing' },
    { source: 'li2', target: 'gong' },
    { source: 'gong', target: 'bing' },
  ],
};

export const DEFAULT_HEATMAP_DATA = {
  points: [
    { lat: 31.23, lng: 121.47, value: 0.9, name: '上海' },
    { lat: 39.9, lng: 116.4, value: 0.8, name: '北京' },
    { lat: 23.13, lng: 113.26, value: 0.6, name: '广州' },
    { lat: 22.54, lng: 114.06, value: 0.7, name: '深圳' },
    { lat: 30.67, lng: 104.06, value: 0.4, name: '成都' },
    { lat: 29.56, lng: 106.55, value: 0.5, name: '重庆' },
    { lat: 34.26, lng: 108.95, value: 0.45, name: '西安' },
    { lat: 30.27, lng: 120.15, value: 0.55, name: '杭州' },
  ],
};
