"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export type VoiceState = 'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated';

export type GradientOrbConfig = {
  background?: string;
  hue?: number;
  rotationSpeed?: number;
  noiseScale?: number;
  innerRadius?: number;
};

const defaults: Required<GradientOrbConfig> = {
  background: "#07090e",
  hue: 0,
  rotationSpeed: 0.3,
  noiseScale: 0.65,
  innerRadius: 0.1,
};

const vertexShader = /* glsl */ `
  varying vec2 vUv;

  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;

  uniform float iTime;
  uniform vec3 iResolution;
  uniform float hue;
  uniform float rot;
  uniform float noiseScale;
  uniform float innerRadius;
  uniform float pulseSpeed;
  uniform float pulseAmp;
  uniform float voiceDistortion;

  // Dynamic state-based base palette colors
  uniform vec3 color0;
  uniform vec3 color1;
  uniform vec3 color2;
  uniform vec3 color3;

  varying vec2 vUv;

  // --- YIQ color space hue rotation ---

  vec3 rgb2yiq(vec3 c) {
    return vec3(
      dot(c, vec3(0.299, 0.587, 0.114)),
      dot(c, vec3(0.596, -0.274, -0.322)),
      dot(c, vec3(0.211, -0.523, 0.312))
    );
  }

  vec3 yiq2rgb(vec3 c) {
    return vec3(
      c.x + 0.956 * c.y + 0.621 * c.z,
      c.x - 0.272 * c.y - 0.647 * c.z,
      c.x - 1.106 * c.y + 1.703 * c.z
    );
  }

  vec3 adjustHue(vec3 color, float hueDeg) {
    float hueRad = radians(hueDeg);
    vec3 yiq = rgb2yiq(color);
    float cosA = cos(hueRad);
    float sinA = sin(hueRad);
    yiq.yz = vec2(yiq.y * cosA - yiq.z * sinA, yiq.y * sinA + yiq.z * cosA);
    return yiq2rgb(yiq);
  }

  // --- 3D simplex noise (hash-based) ---

  vec3 hash33(vec3 p3) {
    p3 = fract(p3 * vec3(0.1031, 0.11369, 0.13787));
    p3 += dot(p3, p3.yxz + 19.19);
    return -1.0 + 2.0 * fract(vec3(p3.x + p3.y, p3.x + p3.z, p3.y + p3.z) * p3.zyx);
  }

  float snoise3(vec3 p) {
    const float K1 = 0.333333333;
    const float K2 = 0.166666667;
    vec3 i = floor(p + (p.x + p.y + p.z) * K1);
    vec3 d0 = p - (i - (i.x + i.y + i.z) * K2);
    vec3 e = step(vec3(0.0), d0 - d0.yzx);
    vec3 i1 = e * (1.0 - e.zxy);
    vec3 i2 = 1.0 - e.zxy * (1.0 - e);
    vec3 d1 = d0 - (i1 - K2);
    vec3 d2 = d0 - (i2 - K1);
    vec3 d3 = d0 - 0.5;
    vec4 h = max(0.6 - vec4(dot(d0, d0), dot(d1, d1), dot(d2, d2), dot(d3, d3)), 0.0);
    vec4 n = h * h * h * h * vec4(
      dot(d0, hash33(i)),
      dot(d1, hash33(i + i1)),
      dot(d2, hash33(i + i2)),
      dot(d3, hash33(i + 1.0))
    );
    return dot(vec4(31.316), n);
  }

  // --- Orb rendering ---

  vec4 extractAlpha(vec3 colorIn) {
    float a = max(max(colorIn.r, colorIn.g), colorIn.b);
    return vec4(colorIn.rgb / (a + 1e-5), a);
  }

  float light1(float intensity, float attenuation, float dist) {
    return intensity / (1.0 + dist * attenuation);
  }

  float light2(float intensity, float attenuation, float dist) {
    return intensity / (1.0 + dist * dist * attenuation);
  }

  vec4 draw(vec2 uv) {
    vec3 c0 = adjustHue(color0, hue);
    vec3 c1 = adjustHue(color1, hue);
    vec3 c2 = adjustHue(color2, hue);
    vec3 c3 = adjustHue(color3, hue);

    float len = length(uv);
    float invLen = len > 0.0 ? 1.0 / len : 0.0;

    // Synchronized Speech undulation & breathing pulse
    float speechWave = sin(iTime * 14.0) * cos(iTime * 8.0) * voiceDistortion;
    float pulse = (sin(iTime * pulseSpeed) * pulseAmp) + speechWave;

    float n0 = snoise3(vec3(uv * (noiseScale + voiceDistortion * 0.4), iTime * (0.5 + voiceDistortion * 1.5))) * 0.5 + 0.5;

    float r0 = mix(mix(innerRadius + pulse, 1.0, 0.4), mix(innerRadius + pulse, 1.0, 0.6), n0);

    float d0 = distance(uv, (r0 * invLen) * uv);
    float v0 = light1(1.0 + voiceDistortion * 0.8, 10.0, d0);
    v0 *= smoothstep(r0 * 1.05, r0, len);
    float cl = cos(atan(uv.y, uv.x) + iTime * (2.0 + voiceDistortion * 3.0)) * 0.5 + 0.5;

    float a = iTime * -1.0;
    vec2 pos = vec2(cos(a), sin(a)) * r0;
    float d = distance(uv, pos);
    float v1 = light2(1.5 + voiceDistortion * 1.2, 5.0, d);
    v1 *= light1(1.0, 50.0, d0);

    float v2 = smoothstep(1.0, mix(innerRadius, 1.0, n0 * 0.5), len);
    float v3 = smoothstep(innerRadius, mix(innerRadius, 1.0, 0.5), len);

    vec3 col = mix(c1, c2, cl);
    col = mix(col, c0, n0);
    col = mix(c3, col, v0);
    col = (col + v1) * v2 * v3;
    col = clamp(col, 0.0, 1.0);

    return extractAlpha(col);
  }

  void main() {
    vec2 center = iResolution.xy * 0.5;
    float size = min(iResolution.x, iResolution.y);
    vec2 uv = (vUv * iResolution.xy - center) / size * 2.0;

    float s = sin(rot);
    float c = cos(rot);
    uv = vec2(c * uv.x - s * uv.y, s * uv.x + c * uv.y);

    vec4 col = draw(uv);
    gl_FragColor = vec4(col.rgb * col.a, col.a);
  }
`;

export const GradientOrb: React.FC<{
  voiceState?: VoiceState;
  config?: GradientOrbConfig;
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

    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    // Fullscreen single-triangle geometry
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3),
    );
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));

    // Preset Palettes:
    // 1. Idle/Standby: Pure Glowing White/Silver Ice
    const whitePalette = {
      c0: new THREE.Vector3(0.95, 0.98, 1.0),
      c1: new THREE.Vector3(0.80, 0.85, 0.95),
      c2: new THREE.Vector3(0.65, 0.75, 0.90),
      c3: new THREE.Vector3(0.0, 0.0, 0.0)
    };

    // 2. Active / Woken Up: Original Vibrant Blue + Purple + Orange Gradient
    const activeGradientPalette = {
      c0: new THREE.Vector3(0.239, 0.353, 1.0),   // Electric Blue
      c1: new THREE.Vector3(0.616, 0.0, 1.0),     // Vivid Purple / Violet
      c2: new THREE.Vector3(1.0, 0.373, 0.122),   // Fiery Orange
      c3: new THREE.Vector3(0.0, 0.0, 0.0)
    };

    // 3. Terminated: Pure Warning Red
    const terminatedPalette = {
      c0: new THREE.Vector3(1.0, 0.1, 0.1),
      c1: new THREE.Vector3(0.8, 0.0, 0.05),
      c2: new THREE.Vector3(0.5, 0.0, 0.0),
      c3: new THREE.Vector3(0.0, 0.0, 0.0)
    };

    // Current lerping color uniforms
    const curC0 = new THREE.Vector3().copy(whitePalette.c0);
    const curC1 = new THREE.Vector3().copy(whitePalette.c1);
    const curC2 = new THREE.Vector3().copy(whitePalette.c2);
    const curC3 = new THREE.Vector3().copy(whitePalette.c3);

    const uniforms = {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3(width, height, 1) },
      hue: { value: 0 },
      rot: { value: 0 },
      noiseScale: { value: config.noiseScale },
      innerRadius: { value: config.innerRadius },
      pulseSpeed: { value: 1.5 },
      pulseAmp: { value: 0.02 },
      voiceDistortion: { value: 0.0 },
      color0: { value: curC0 },
      color1: { value: curC1 },
      color2: { value: curC2 },
      color3: { value: curC3 },
    };

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms,
      transparent: true,
      depthWrite: false,
      depthTest: false,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.frustumCulled = false;
    scene.add(mesh);

    // WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const clock = new THREE.Clock();
    let reqId = 0;
    let currentRot = 0;
    let currentVoiceDistortion = 0;

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      renderer.setSize(w, h);
      uniforms.iResolution.value.set(w * renderer.getPixelRatio(), h * renderer.getPixelRatio(), 1);
    };
    window.addEventListener("resize", handleResize);

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const state = voiceStateRef.current;

      let targetPalette = whitePalette;
      let rotSpeed = config.rotationSpeed;
      let targetPulseSpeed = 1.5;
      let targetPulseAmp = 0.02;
      let targetVoiceDistortion = 0.0;

      if (state === 'idle' || state === 'wakeword') {
        // White on Idle / Standby
        targetPalette = whitePalette;
        rotSpeed = 0.25;
        targetPulseSpeed = 1.2;
        targetPulseAmp = 0.015;
        targetVoiceDistortion = 0.0;
      } else if (state === 'listening') {
        // Subtle ripple while listening to user
        targetPalette = activeGradientPalette;
        rotSpeed = 0.55;
        targetPulseSpeed = 3.0;
        targetPulseAmp = 0.04;
        targetVoiceDistortion = 0.03;
      } else if (state === 'speaking') {
        // Active Voice Speech Synchronized Fluid Wave Animation
        targetPalette = activeGradientPalette;
        rotSpeed = 1.2;
        targetPulseSpeed = 7.0;
        targetPulseAmp = 0.09;
        targetVoiceDistortion = 0.12; // High expressive audio-wave rippling
      } else if (state === 'terminated') {
        // Red on Termination
        targetPalette = terminatedPalette;
        rotSpeed = 0.1;
        targetPulseSpeed = 0.8;
        targetPulseAmp = 0.01;
        targetVoiceDistortion = 0.0;
      }

      // Smooth color transitions between palettes
      curC0.lerp(targetPalette.c0, 0.08);
      curC1.lerp(targetPalette.c1, 0.08);
      curC2.lerp(targetPalette.c2, 0.08);
      curC3.lerp(targetPalette.c3, 0.08);

      currentVoiceDistortion += (targetVoiceDistortion - currentVoiceDistortion) * 0.1;
      currentRot += 0.01 * rotSpeed;

      uniforms.iTime.value = t;
      uniforms.rot.value = currentRot;
      uniforms.pulseSpeed.value = targetPulseSpeed;
      uniforms.pulseAmp.value = targetPulseAmp;
      uniforms.voiceDistortion.value = currentVoiceDistortion;
      uniforms.iResolution.value.set(
        container.clientWidth * renderer.getPixelRatio(),
        container.clientHeight * renderer.getPixelRatio(),
        1
      );

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
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
        width: "100vw",
        height: "100vh",
        position: "absolute",
        top: 0,
        left: 0,
        overflow: "hidden",
        background: "#07090e",
      }}
    />
  );
};

export default GradientOrb;
