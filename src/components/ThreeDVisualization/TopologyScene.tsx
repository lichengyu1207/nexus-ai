import React, { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { TopologyData, NodeData } from './types';
import { getNodeColor, generateTopologyPositions } from './utils';

interface NodeProps {
  node: NodeData;
  position: THREE.Vector3;
  onClick?: (id: string) => void;
}

const Node: React.FC<NodeProps> = ({ node, position, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const baseColor = node.color || getNodeColor(node.status);

  useFrame(({ clock }) => {
    if (meshRef.current && node.status === 'active') {
      const scale = 1 + Math.sin(clock.getElapsedTime() * 3) * 0.05;
      meshRef.current.scale.set(scale, scale, scale);
    }
  });

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={() => onClick?.(node.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshStandardMaterial
          color={baseColor}
          emissive={node.status === 'active' ? '#FFD966' : '#000000'}
          emissiveIntensity={node.status === 'active' ? 0.3 : 0}
          metalness={0.3}
          roughness={0.4}
        />
      </mesh>
      {node.status === 'active' && (
        <pointLight position={[0, 0, 0]} intensity={0.3} color="#FFD966" distance={1.5} />
      )}
      {hovered && (
        <Html distanceFactor={10} center position={[0, 0.6, 0]}>
          <div className="bg-bg-glass backdrop-blur-md text-text-primary text-xs rounded-lg px-3 py-2 whitespace-nowrap border border-border-light shadow-lg">
            <div className="font-bold text-primary">{node.name}</div>
            <div className="text-text-secondary">
              状态: {node.status === 'active' ? '活跃' : node.status === 'idle' ? '空闲' : '故障'}
            </div>
            {node.task && <div className="text-text-secondary">任务: {node.task}</div>}
          </div>
        </Html>
      )}
    </group>
  );
};

interface TopologySceneProps {
  data: TopologyData;
  onNodeClick?: (id: string) => void;
}

export const TopologyScene: React.FC<TopologySceneProps> = ({ data, onNodeClick }) => {
  const positions = useMemo(() => generateTopologyPositions(data.nodes), [data.nodes]);

  const nodePosMap = useMemo(() => {
    const map = new Map<string, THREE.Vector3>();
    data.nodes.forEach((node, idx) => {
      map.set(node.id, positions[idx]);
    });
    return map;
  }, [data.nodes, positions]);

  const lineGeometry = useMemo(() => {
    const points: THREE.Vector3[] = [];
    data.edges.forEach((edge) => {
      const p1 = nodePosMap.get(edge.source);
      const p2 = nodePosMap.get(edge.target);
      if (p1 && p2) {
        points.push(p1.clone(), p2.clone());
      }
    });
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    return geometry;
  }, [data.edges, nodePosMap]);

  return (
    <>
      {data.nodes.map((node, idx) => (
        <Node key={node.id} node={node} position={positions[idx]} onClick={onNodeClick} />
      ))}
      <lineSegments geometry={lineGeometry}>
        <lineBasicMaterial color="#FFD966" transparent opacity={0.5} />
      </lineSegments>
    </>
  );
};

export default TopologyScene;
