import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { motion, AnimatePresence } from 'framer-motion';

export type VoiceState = 'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated';

interface HolographicReactorProps {
  voiceState: VoiceState;
  audioFrequency?: number;
}

export const HolographicReactor: React.FC<HolographicReactorProps> = ({ voiceState, audioFrequency = 0 }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const particlesRef = useRef<THREE.Points | null>(null);
  const ringsRef = useRef<THREE.Group | null>(null);
  const coreRef = useRef<THREE.Mesh | null>(null);
  const reqIdRef = useRef<number>(0);

  // 1. Initialize 3D Three.js Holographic Arc Reactor
  useEffect(() => {
    if (!mountRef.current) return;

    const width = 380;
    const height = 380;

    // Scene & Camera
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 8.5;

    // WebGL Renderer with Alpha Transparent Background
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Ring Group
    const ringsGroup = new THREE.Group();
    ringsRef.current = ringsGroup;
    scene.add(ringsGroup);

    // Create 3 Nested Arc Rings
    const ringConfigs = [
      { radius: 2.2, tube: 0.015, color: 0x00f2ff, speedX: 0.008, speedY: 0.012 },
      { radius: 1.7, tube: 0.018, color: 0x3b82f6, speedX: -0.012, speedY: 0.009 },
      { radius: 1.2, tube: 0.022, color: 0xa855f7, speedX: 0.015, speedY: -0.014 }
    ];

    ringConfigs.forEach((cfg) => {
      const geom = new THREE.TorusGeometry(cfg.radius, cfg.tube, 16, 100);
      const mat = new THREE.MeshBasicMaterial({
        color: cfg.color,
        wireframe: false,
        transparent: true,
        opacity: 0.85
      });
      const ringMesh = new THREE.Mesh(geom, mat);
      ringsGroup.add(ringMesh);
    });

    // Core Glowing Nucleus Sphere
    const coreGeom = new THREE.IcosahedronGeometry(0.65, 3);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x00f2ff,
      wireframe: true,
      transparent: true,
      opacity: 0.9
    });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    coreRef.current = coreMesh;
    scene.add(coreMesh);

    // 3D Orbiting Hologram Particle Cloud (250 particles)
    const particleCount = 260;
    const particleGeom = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      const radius = 2.4 + Math.random() * 0.9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      posArray[i] = radius * Math.sin(phi) * Math.cos(theta);
      posArray[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      posArray[i + 2] = radius * Math.cos(phi);
    }

    particleGeom.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.045,
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(particleGeom, particleMat);
    particlesRef.current = particles;
    scene.add(particles);

    // Render Animation Loop
    let angle = 0;
    const animate = () => {
      reqIdRef.current = requestAnimationFrame(animate);
      angle += 0.01;

      // Rotate Rings with 3D Gimbal Motion
      if (ringsGroup) {
        ringsGroup.children.forEach((ring, idx) => {
          const cfg = ringConfigs[idx];
          ring.rotation.x += cfg.speedX;
          ring.rotation.y += cfg.speedY;
          ring.rotation.z += 0.005;
        });
      }

      // Pulse and Rotate Core
      if (coreMesh) {
        coreMesh.rotation.y -= 0.015;
        coreMesh.rotation.x += 0.01;
      }

      // Rotate Outer Particle Cloud
      if (particles) {
        particles.rotation.y += 0.003;
        particles.rotation.x -= 0.002;
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(reqIdRef.current);
      renderer.dispose();
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  // 2. React to voiceState Color & Speed changes dynamically
  useEffect(() => {
    if (!ringsRef.current || !coreRef.current || !particlesRef.current) return;

    let primaryColor = 0x3b82f6; // Standby Blue
    let coreColor = 0x00f2ff;

    if (voiceState === 'listening') {
      primaryColor = 0x00f2ff; // Cyan Pulse
      coreColor = 0x38bdf8;
    } else if (voiceState === 'speaking') {
      primaryColor = 0xa855f7; // Purple / High Energy
      coreColor = 0xc084fc;
    } else if (voiceState === 'terminated') {
      primaryColor = 0xef4444; // Red
      coreColor = 0xf87171;
    }

    // Update Core Material
    (coreRef.current.material as THREE.MeshBasicMaterial).color.setHex(coreColor);
    (particlesRef.current.material as THREE.PointsMaterial).color.setHex(primaryColor);

    ringsRef.current.children.forEach((child) => {
      ((child as THREE.Mesh).material as THREE.MeshBasicMaterial).color.setHex(primaryColor);
    });
  }, [voiceState]);

  // Dynamic Framer Motion glow configurations
  const glowColors: Record<VoiceState, string> = {
    idle: 'rgba(59, 130, 246, 0.4)',
    wakeword: 'rgba(59, 130, 246, 0.5)',
    listening: 'rgba(0, 242, 255, 0.85)',
    speaking: 'rgba(168, 85, 247, 0.9)',
    terminated: 'rgba(239, 68, 68, 0.8)'
  };

  return (
    <div style={{ position: 'relative', width: '380px', height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {/* Framer Motion Reactive Atmospheric Pulse Waves */}
      <AnimatePresence>
        {voiceState === 'listening' && (
          <motion.div
            initial={{ scale: 0.85, opacity: 0.8 }}
            animate={{ scale: [0.85, 1.45, 1.8], opacity: [0.7, 0.35, 0] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              width: '240px',
              height: '240px',
              borderRadius: '50%',
              border: '2px solid #00f2ff',
              boxShadow: '0 0 25px #00f2ff, inset 0 0 20px #00f2ff',
              pointerEvents: 'none',
              zIndex: 1
            }}
          />
        )}

        {voiceState === 'speaking' && (
          <motion.div
            initial={{ scale: 0.9, opacity: 0.9 }}
            animate={{ scale: [0.9, 1.35, 1.6], opacity: [0.8, 0.4, 0] }}
            transition={{ repeat: Infinity, duration: 1.2, ease: 'easeInOut' }}
            style={{
              position: 'absolute',
              width: '240px',
              height: '240px',
              borderRadius: '50%',
              border: '2px solid #a855f7',
              boxShadow: '0 0 35px #a855f7, inset 0 0 25px #a855f7',
              pointerEvents: 'none',
              zIndex: 1
            }}
          />
        )}
      </AnimatePresence>

      {/* Dynamic Background Core Glow */}
      <motion.div
        animate={{
          scale: voiceState === 'speaking' ? [1, 1.15, 1] : voiceState === 'listening' ? [1, 1.08, 1] : [1, 1.03, 1],
          boxShadow: `0 0 60px ${glowColors[voiceState]}, inset 0 0 40px ${glowColors[voiceState]}`
        }}
        transition={{ repeat: Infinity, duration: voiceState === 'speaking' ? 0.9 : 2.0, ease: 'easeInOut' }}
        style={{
          position: 'absolute',
          width: '180px',
          height: '180px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.8) 100%)',
          pointerEvents: 'none',
          zIndex: 2
        }}
      />

      {/* Three.js 3D Canvas Mount Point */}
      <div ref={mountRef} style={{ position: 'absolute', top: 0, left: 0, width: '380px', height: '380px', zIndex: 3, pointerEvents: 'none' }} />
    </div>
  );
};
