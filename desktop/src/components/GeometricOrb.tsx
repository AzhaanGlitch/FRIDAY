"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { Line2 } from "three-stdlib";
import { LineMaterial } from "three-stdlib";
import { LineGeometry } from "three-stdlib";

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
  numLines: 22,
  radius: 1.6,
  speed: 15,
  lineWidth: 2.2,
  color: "#38bdf8",
  background: "#07090e",
  squiggleAmount: 0.05,
  squiggleFrequency: 5,
  squiggleSpeed: 2.5,
  pointsPerLine: 96,
  enableZoom: false,
  enablePan: false,
  minDistance: 2,
  maxDistance: 20,
};

export const GeometricOrb: React.FC<{
  voiceState?: VoiceState;
  config?: GeometricOrbConfig;
  className?: string;
}> = ({ voiceState = 'idle', config: configOverrides, className = "" }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const voiceStateRef = useRef<VoiceState>(voiceState);
  voiceStateRef.current = voiceState;

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const config = { ...defaults, ...configOverrides };

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x07090e);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 7.5);

    // WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Orbit Lines Setup
    const baseColor = new THREE.Color(0x38bdf8);
    const lineConstants = Array.from({ length: config.numLines }, (_, i) => ({
      longitudeRotation: (i / config.numLines) * Math.PI,
      timeOffset: (i / config.numLines) * config.speed,
      cosR: Math.cos((i / config.numLines) * Math.PI),
      sinR: Math.sin((i / config.numLines) * Math.PI),
    }));

    const materials: LineMaterial[] = [];
    const geometries: LineGeometry[] = [];
    const lineGroups: THREE.Group[] = [];

    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    for (let i = 0; i < config.numLines; i++) {
      const mat = new LineMaterial({
        color: 0xffffff,
        linewidth: config.lineWidth,
        transparent: true,
        opacity: 0.9,
        vertexColors: true,
      });
      mat.resolution.set(width, height);
      materials.push(mat);

      const geo = new LineGeometry();
      geometries.push(geo);

      const group = new THREE.Group();
      const line2 = new Line2(geo, mat);
      group.add(line2);
      rootGroup.add(group);
      lineGroups.push(group);
    }

    const vertexCount = config.pointsPerLine + 1;
    const positionBuffer = new Float32Array(vertexCount * 3);
    const colorBuffer = new Float32Array(vertexCount * 3);

    const clock = new THREE.Clock();
    let reqId = 0;
    const camDir = new THREE.Vector3();

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      materials.forEach(m => m.resolution.set(w, h));
    };
    window.addEventListener('resize', handleResize);

    // Render Animation Loop
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();
      const state = voiceStateRef.current;

      // Color mapping:
      // Standby / Default: Radiant Gold (#ffd700)
      // Woken up / Listening: Dark Ember Orange (#ff5500)
      // Responding / Speaking: Intense Glowing Crimson-Orange (#ff3300)
      // Terminated: Dim Red (#ef4444)
      let targetHex = 0xffd700; // Default Gold
      if (state === 'listening') targetHex = 0xff5500; // Dark Vibrant Orange
      else if (state === 'speaking') targetHex = 0xff7700; // Bright Glowing Orange
      else if (state === 'terminated') targetHex = 0xef4444; // Red
      else targetHex = 0xffd700; // Idle/Wakeword Standby Gold

      baseColor.lerp(new THREE.Color(targetHex), 0.08);
      const r = baseColor.r;

      const g = baseColor.g;
      const b = baseColor.b;

      // Audio/Voice Reactivity
      let liveSquiggle = config.squiggleAmount;
      let liveSpeed = config.squiggleSpeed;
      let liveRadius = config.radius;

      if (state === 'listening') {
        liveSquiggle = 0.09 + Math.sin(time * 6) * 0.03;
        liveSpeed = 4.5;
        liveRadius = config.radius * (1 + Math.sin(time * 4) * 0.04);
      } else if (state === 'speaking') {
        liveSquiggle = 0.14 + Math.sin(time * 12) * 0.05;
        liveSpeed = 7.0;
        liveRadius = config.radius * (1 + Math.sin(time * 8) * 0.08);
      } else if (state === 'terminated') {
        liveSquiggle = 0.01;
        liveSpeed = 0.5;
      }

      camDir.copy(camera.position).normalize();

      for (let lineIdx = 0; lineIdx < config.numLines; lineIdx++) {
        const group = lineGroups[lineIdx];
        const constants = lineConstants[lineIdx];
        const geometry = geometries[lineIdx];
        if (!group || !constants || !geometry) continue;

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

          // Volumetric depth-fade
          const worldX = x * cosR + z * sinR;
          const worldZ = -x * sinR + z * cosR;
          const dot = worldX * camDir.x + y * camDir.y + worldZ * camDir.z;
          const depthFactor = (dot / liveRadius + 1) / 2;
          const opacity = Math.max(0.08, depthFactor * 0.85 + 0.15);

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
        group.rotation.y = longitudeRotation;
      }

      rootGroup.rotation.y += state === 'speaking' ? 0.015 : state === 'listening' ? 0.008 : 0.003;
      rootGroup.rotation.x = Math.sin(time * 0.5) * 0.1;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      materials.forEach(m => m.dispose());
      geometries.forEach(g => g.dispose());
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [configOverrides]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        width: '100vw',
        height: '100vh',
        position: 'absolute',
        top: 0,
        left: 0,
        overflow: 'hidden',
        background: '#07090e',
      }}
    />
  );
};

export default GeometricOrb;
