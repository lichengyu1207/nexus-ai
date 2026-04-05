import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment } from '@react-three/drei';
import { TopologyScene } from './TopologyScene';
import { HeatmapScene } from './HeatmapScene';
import { ThreeDVisualizationProps, TopologyData, HeatmapData } from './types';
import { DEFAULT_TOPOLOGY_DATA, DEFAULT_HEATMAP_DATA } from './utils';
import clsx from 'clsx';

const LoadingFallback: React.FC = () => (
  <div className="absolute inset-0 flex items-center justify-center bg-bg-secondary/50">
    <div className="flex flex-col items-center gap-2">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      <span className="text-text-secondary text-sm">加载3D场景...</span>
    </div>
  </div>
);

export const ThreeDVisualization: React.FC<ThreeDVisualizationProps> = ({
  mode,
  data,
  className,
  onNodeClick,
}) => {
  const topologyData = (mode === 'topology' ? (data as TopologyData) : null) || DEFAULT_TOPOLOGY_DATA;
  const heatmapData = (mode === 'heatmap' ? (data as HeatmapData) : null) || DEFAULT_HEATMAP_DATA;

  return (
    <div className={clsx('relative w-full h-full min-h-[400px] rounded-xl overflow-hidden', className)}>
      <Canvas
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
        dpr={[1, 2]}
      >
        <PerspectiveCamera makeDefault position={[5, 5, 5]} fov={50} />
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 7]} intensity={0.8} />
        <pointLight position={[2, 3, 4]} intensity={0.6} color="#FFD966" />
        <Suspense fallback={null}>
          {mode === 'topology' && (
            <TopologyScene data={topologyData} onNodeClick={onNodeClick} />
          )}
          {mode === 'heatmap' && <HeatmapScene data={heatmapData} />}
          <Environment preset="night" />
        </Suspense>
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          zoomSpeed={1}
          rotateSpeed={0.5}
          minDistance={2}
          maxDistance={15}
        />
      </Canvas>
      <Suspense fallback={<LoadingFallback />}>
        <div className="absolute bottom-2 right-2 text-xs text-text-secondary bg-bg-glass backdrop-blur-sm px-2 py-1 rounded">
          拖拽旋转 | 滚轮缩放
        </div>
      </Suspense>
    </div>
  );
};

export default ThreeDVisualization;
