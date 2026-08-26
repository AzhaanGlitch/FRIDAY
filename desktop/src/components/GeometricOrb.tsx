"use client";

import React, { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame, useThree, extend } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { Line2 } from "three-stdlib";
import { LineMaterial } from "three-stdlib";
import { LineGeometry } from "three-stdlib";

// Extend Three.js custom lines for R3F
extend({ Line2, LineMaterial, LineGeometry });

export type VoiceState = 'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated';

export type GeometricOrbConfig = {
  numLines?: number;
  radius?: number;
  speed?: number;
  lineWidth?: number;
  color?: string;
  background?: string;
  squiggleAmount?: number;
  squiggleFrequency?: number;
  squiggleSpeed?: number;
  pointsPerLine?: number;
  enableZoom?: boolean;
  enablePan?: boolean;
  minDistance?: number;
  maxDistance?: number;
};

const defaults: Required<GeometricOrbConfig> = {
  numLines: 24,
  radius: 1.6,
  speed: 15,
  lineWidth: 2.2,
  color: "#38bdf8",
  background: "transparent",
  squiggleAmount: 0.05,
  squiggleFrequency: 5,
  squiggleSpeed: 2.5,
  pointsPerLine: 96,
  enableZoom: false,
  enablePan: false,
  minDistance: 2,
  maxDistance: 20,
};

function LatitudeLines({
  config,
  voiceState,
}: {
  config: Required<GeometricOrbConfig>;
  voiceState: VoiceState;
}) {
  const groupRefs = useRef<(THREE.Group | null)[]>([]);
  const camDirRef = useRef(new THREE.Vector3());
  const { size } = useThree();

  // Dynamic state colors
  const activeColorStr = useMemo(() => {
    switch (voiceState) {
      case 'listening':
        return '#00f2ff'; // Cyan
      case 'speaking':
        return '#c084fc'; // Purple / Violet
      case 'terminated':
        return '#ef4444'; // Red
      default:
        return '#38bdf8'; // Blue Standby
    }
  }, [voiceState]);

  const baseColor = useMemo(() => new THREE.Color(activeColorStr), [activeColorStr]);
  const colorInt = useMemo(() => baseColor.getHex(), [baseColor]);

  const lineConstants = useMemo(
    () =>
      Array.from({ length: config.numLines }, (_, i) => ({
        longitudeRotation: (i / config.numLines) * Math.PI,
        timeOffset: (i / config.numLines) * config.speed,
        cosR: Math.cos((i / config.numLines) * Math.PI),
        sinR: Math.sin((i / config.numLines) * Math.PI),
      })),
    [config.numLines, config.speed],
  );

  const materials = useMemo(
    () =>
      Array.from(
        { length: config.numLines },
        () =>
          new LineMaterial({
            color: colorInt,
            linewidth: config.lineWidth,
            transparent: true,
            opacity: 0.9,
            vertexColors: true,
          }),
      ),
    [colorInt, config.numLines, config.lineWidth],
  );

  const geometries = useMemo(
    () => Array.from({ length: config.numLines }, () => new LineGeometry()),
    [config.numLines],
  );

  useEffect(() => {
    return () => {
      for (const mat of materials) mat.dispose();
      for (const geo of geometries) geo.dispose();
    };
  }, [materials, geometries]);

  useEffect(() => {
    for (const mat of materials) {
      mat.resolution.set(size.width, size.height);
      mat.color.set(baseColor);
    }
  }, [materials, size.width, size.height, baseColor]);

  const vertexCount = config.pointsPerLine + 1;
  const positionBuffer = useMemo(() => new Float32Array(vertexCount * 3), [vertexCount]);
  const colorBuffer = useMemo(() => new Float32Array(vertexCount * 3), [vertexCount]);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const camDir = camDirRef.current.copy(state.camera.position).normalize();
    const r = baseColor.r;
    const g = baseColor.g;
    const b = baseColor.b;

    // Reactively change squiggle amplitude & speed based on VoiceState
    let liveSquiggle = config.squiggleAmount;
    let liveSpeed = config.squiggleSpeed;
    let liveRadius = config.radius;

    if (voiceState === 'listening') {
      // Dynamic pulsing expansion while listening to microphone
      liveSquiggle = 0.09 + Math.sin(time * 6) * 0.03;
      liveSpeed = 4.5;
      liveRadius = config.radius * (1 + Math.sin(time * 4) * 0.04);
    } else if (voiceState === 'speaking') {
      // High-energy rapid undulating sound waves while speaking
      liveSquiggle = 0.14 + Math.sin(time * 12) * 0.05;
      liveSpeed = 7.0;
      liveRadius = config.radius * (1 + Math.sin(time * 8) * 0.08);
    } else if (voiceState === 'terminated') {
      liveSquiggle = 0.01;
      liveSpeed = 0.5;
    }

    for (let lineIdx = 0; lineIdx < config.numLines; lineIdx++) {
      const group = groupRefs.current[lineIdx];
      if (!group) continue;

      const constants = lineConstants[lineIdx];
      const geometry = geometries[lineIdx];
      if (!constants || !geometry) continue;

      const { timeOffset, longitudeRotation, cosR, sinR } = constants;
      const progress = ((time + timeOffset) % config.speed) / config.speed;
      const latitude = progress * Math.PI;
      const circleRadius = Math.sin(latitude) * liveRadius;
      const yPosition = Math.cos(latitude) * liveRadius;

      for (let i = 0; i < config.pointsPerLine; i++) {
        const angle = (i / config.pointsPerLine) * Math.PI * 2;
        const squiggle =
          Math.sin(angle * config.squiggleFrequency + time * liveSpeed + lineIdx * 0.5) *
          liveSquiggle;
        const radiusSquiggle =
          Math.cos(angle * config.squiggleFrequency * 1.3 + time * liveSpeed * 0.8) *
          liveSquiggle *
          0.5;
        const displacedRadius = circleRadius + (squiggle + radiusSquiggle) * circleRadius;
        const ySquiggle =
          Math.sin(angle * config.squiggleFrequency * 0.7 + time * liveSpeed * 1.2) *
          liveSquiggle *
          0.4;

        const x = Math.cos(angle) * displacedRadius;
        const y = yPosition + ySquiggle * circleRadius;
        const z = Math.sin(angle) * displacedRadius;

        const offset = i * 3;
        positionBuffer[offset] = x;
        positionBuffer[offset + 1] = y;
        positionBuffer[offset + 2] = z;

        // Smooth volumetric depth fade
        const worldX = x * cosR + z * sinR;
        const worldZ = -x * sinR + z * cosR;
        const dot = worldX * camDir.x + y * camDir.y + worldZ * camDir.z;
        const depthFactor = (dot / liveRadius + 1) / 2;
        const opacity = Math.max(0.1, depthFactor * 0.85 + 0.15);

        colorBuffer[offset] = r * opacity;
        colorBuffer[offset + 1] = g * opacity;
        colorBuffer[offset + 2] = b * opacity;
      }

      // Close loop
      const last = config.pointsPerLine * 3;
      positionBuffer[last] = positionBuffer[0]!;
      positionBuffer[last + 1] = positionBuffer[1]!;
      positionBuffer[last + 2] = positionBuffer[2]!;
      colorBuffer[last] = colorBuffer[0]!;
      colorBuffer[last + 1] = colorBuffer[1]!;
      colorBuffer[last + 2] = colorBuffer[2]!;

      geometry.setPositions(positionBuffer);
      geometry.setColors(colorBuffer);
      group.rotation.y = longitudeRotation + time * 0.05;
    }
  });

  return (
    <>
      {Array.from({ length: config.numLines }, (_, lineIdx) => {
        const geometry = geometries[lineIdx];
        const material = materials[lineIdx];
        if (!geometry || !material) return null;
        return (
          <group
            key={lineIdx}
            ref={(el) => {
              groupRefs.current[lineIdx] = el;
            }}
          >
            {/* @ts-expect-error custom extended line2 component */}
            <line2>
              <primitive object={geometry} attach="geometry" />
              <primitive object={material} attach="material" />
              {/* @ts-expect-error custom extended line2 component */}
            </line2>
          </group>
        );
      })}
    </>
  );
}

export function GeometricOrb({
  voiceState = 'idle',
  config: configOverrides,
  className = "",
}: {
  voiceState?: VoiceState;
  config?: GeometricOrbConfig;
  className?: string;
}) {
  const config = useMemo(() => ({ ...defaults, ...configOverrides }), [configOverrides]);

  return (
    <div className={`w-full h-full ${className}`} style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Canvas camera={{ position: [0, 0, 7.5], fov: 45 }} gl={{ antialias: true, alpha: true }}>
        <LatitudeLines config={config} voiceState={voiceState} />
        <OrbitControls
          enablePan={config.enablePan}
          enableZoom={config.enableZoom}
          minDistance={config.minDistance}
          maxDistance={config.maxDistance}
          autoRotate
          autoRotateSpeed={voiceState === 'speaking' ? 2.5 : voiceState === 'listening' ? 1.5 : 0.6}
        />
      </Canvas>
    </div>
  );
}

export default GeometricOrb;
