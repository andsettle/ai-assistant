import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { motion } from 'framer-motion';
import * as THREE from 'three';
import type { OrbActivity } from '../types';

interface RobotProps {
  activity: OrbActivity;
  variant: "full" | "mini";
  onPointerDown: (e: React.PointerEvent) => void;
  onPointerMove: (e: React.PointerEvent) => void;
  onPointerUp: (e: React.PointerEvent) => void;
}

function RobotModel({ activity }: { activity: OrbActivity }) {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Group>(null);
  const antennaRef = useRef<THREE.Mesh>(null);
  
  // Basic colors based on activity
  const colors: Record<OrbActivity, string> = {
    idle: '#6dd3ff',
    thinking: '#9b8cff',
    tool: '#26d07c',
    streaming: '#6dd3ff',
    error: '#ef4444',
    disconnected: '#666666'
  };

  const eyeColor = colors[activity];

  useFrame((state, delta) => {
    if (!groupRef.current || !headRef.current || !antennaRef.current) return;
    const t = state.clock.getElapsedTime();

    // Floating animation
    groupRef.current.position.y = Math.sin(t * 2) * 0.1;

    // Looking around animation
    if (activity === 'idle') {
      headRef.current.rotation.y = Math.sin(t * 1.5) * 0.2;
      headRef.current.rotation.x = Math.sin(t * 1) * 0.1;
    } else if (activity === 'thinking') {
      headRef.current.rotation.y = Math.sin(t * 4) * 0.3;
      headRef.current.rotation.x = Math.sin(t * 6) * 0.2;
    } else if (activity === 'streaming') {
      headRef.current.rotation.y = Math.sin(t * 5) * 0.1;
      headRef.current.rotation.x = Math.sin(t * 8) * 0.05;
    } else {
      headRef.current.rotation.y = Math.sin(t * 0.5) * 0.05;
      headRef.current.rotation.x = 0;
    }

    // Antenna spin
    if (activity === 'thinking' || activity === 'tool' || activity === 'streaming') {
      antennaRef.current.rotation.y += delta * (activity === 'thinking' ? 10 : 2);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Body */}
      <mesh position={[0, -0.6, 0]}>
        <boxGeometry args={[1.2, 0.8, 0.8]} />
        <meshStandardMaterial color="#8e92a0" roughness={0.4} metalness={0.4} />
      </mesh>

      {/* Head Group */}
      <group ref={headRef} position={[0, 0.2, 0]}>
        {/* Head Base */}
        <mesh>
          <boxGeometry args={[1, 0.8, 1]} />
          <meshStandardMaterial color="#b2b5c2" roughness={0.5} metalness={0.3} />
        </mesh>
        
        {/* Face Screen */}
        <mesh position={[0, 0, 0.51]}>
          <planeGeometry args={[0.8, 0.5]} />
          <meshBasicMaterial color="#0a0f1d" />
        </mesh>

        {/* Eyes */}
        <mesh position={[-0.2, 0, 0.52]}>
          <circleGeometry args={[0.08, 16]} />
          <meshBasicMaterial color={eyeColor} />
        </mesh>
        <mesh position={[0.2, 0, 0.52]}>
          <circleGeometry args={[0.08, 16]} />
          <meshBasicMaterial color={eyeColor} />
        </mesh>

        {/* Antenna Stem */}
        <mesh position={[0, 0.5, 0]}>
          <cylinderGeometry args={[0.03, 0.03, 0.3]} />
          <meshStandardMaterial color="#7a7e95" />
        </mesh>

        {/* Antenna Ball */}
        <mesh ref={antennaRef} position={[0, 0.7, 0]}>
          <sphereGeometry args={[0.1, 16, 16]} />
          <meshBasicMaterial color={eyeColor} />
        </mesh>
      </group>
    </group>
  );
}

export function Robot({ activity, variant, onPointerDown, onPointerMove, onPointerUp }: RobotProps) {
  return (
    <motion.div
      className={`robot-wrapper ${variant}`}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      whileHover={{ scale: variant === "full" ? 1.1 : 1.05 }}
    >
      <Canvas camera={{ position: [0, 0, 3.5], fov: 45 }}>
        <ambientLight intensity={1.5} />
        <directionalLight position={[10, 10, 5]} intensity={2} />
        <RobotModel activity={activity} />
      </Canvas>
    </motion.div>
  );
}
