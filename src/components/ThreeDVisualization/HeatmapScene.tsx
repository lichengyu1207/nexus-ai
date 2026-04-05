import React, { useMemo, useState } from 'react';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { HeatmapData } from './types';
import { calculateHeatmapItems } from './utils';

interface HeatmapBarProps {
  position: THREE.Vector3;
  height: number;
  color: THREE.Color;
  name?: string;
  value: number;
}

const HeatmapBar: React.FC<HeatmapBarProps> = ({ position, height, color, name, value }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <group position={position}>
      <mesh
        position={[0, height / 2, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <cylinderGeometry args={[0.15, 0.25, height, 8]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? 0.5 : 0.2}
          metalness={0.3}
          roughness={0.4}
        />
      </mesh>
      <pointLight position={[0, height + 0.1, 0]} intensity={0.4} color={color} distance={1} />
      {hovered && (
        <Html distanceFactor={10} center position={[0, height + 0.5, 0]}>
          <div className="bg-bg-glass backdrop-blur-md text-text-primary text-xs rounded-lg px-3 py-2 whitespace-nowrap border border-border-light shadow-lg">
            {name && <div className="font-bold text-primary">{name}</div>}
            <div className="text-text-secondary">数值: {(value * 100).toFixed(1)}%</div>
          </div>
        </Html>
      )}
    </group>
  );
};

interface HeatmapSceneProps {
  data: HeatmapData;
}

export const HeatmapScene: React.FC<HeatmapSceneProps> = ({ data }) => {
  const items = useMemo(() => calculateHeatmapItems(data.points), [data.points]);

  return (
    <>
      <gridHelper args={[10, 20, '#444', '#333']} position={[0, -0.1, 0]} />
      {items.map((item, idx) => (
        <HeatmapBar
          key={idx}
          position={item.pos}
          height={item.height}
          color={item.color}
          name={item.point.name}
          value={item.point.value}
        />
      ))}
    </>
  );
};

export default HeatmapScene;
