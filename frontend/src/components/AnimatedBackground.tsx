/**
 * AnimatedBackground — 动态WebGL着色器背景组件
 * 
 * 来源: MiniMax shader-dev (GLSL着色器36技术吸收)
 * 适用: AI数字名片首页/登录页/展示页
 * 
 * 5种预设效果:
 * - aurora: 极光渐变 (默认)
 * - particles: 粒子星云
 * - waves: 波浪流动
 * - gradient: 动态渐变
 * - matrix: 数字雨 (赛博风格)
 * 
 * 性能: 低 ~ 中 (GPU加速, 移动端自动降级)
 */

import React, { useRef, useEffect, useState } from 'react';

type EffectType = 'aurora' | 'particles' | 'waves' | 'gradient' | 'matrix';

interface AnimatedBackgroundProps {
  effect?: EffectType;
  color1?: string;
  color2?: string;
  speed?: number;
  className?: string;
  children?: React.ReactNode;
}

// ── GLSL Shaders ───────────────────────────────────────────

const VERTEX_SHADER = `
  attribute vec2 position;
  void main() {
    gl_Position = vec4(position, 0.0, 1.0);
  }
`;

const AURORA_FRAGMENT = `
  precision highp float;
  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec3 uColor1;
  uniform vec3 uColor2;

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float t = uTime * 0.15;
    
    // Aurora layers
    float wave1 = sin(uv.x * 4.0 + t) * cos(uv.y * 3.0 - t * 0.7) * 0.5 + 0.5;
    float wave2 = sin(uv.x * 7.0 - t * 1.2) * cos(uv.y * 5.0 + t * 0.5) * 0.5 + 0.5;
    float wave3 = sin((uv.x + uv.y) * 6.0 + t * 0.9) * 0.5 + 0.5;
    
    float blend = wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2;
    vec3 color = mix(uColor1, uColor2, blend);
    
    // Vignette
    float vignette = 1.0 - length(uv - 0.5) * 0.6;
    color *= vignette;
    
    gl_FragColor = vec4(color, 1.0);
  }
`;

const PARTICLE_FRAGMENT = `
  precision highp float;
  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec3 uColor1;
  uniform vec3 uColor2;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float t = uTime * 0.08;
    
    vec3 color = vec3(0.0);
    for (int i = 0; i < 3; i++) {
      vec2 pos = vec2(
        hash(vec2(float(i) * 13.0, 0.0)) + sin(t + float(i) * 2.1) * 0.3,
        hash(vec2(float(i) * 7.0, 1.0)) + cos(t * 0.7 + float(i) * 3.7) * 0.3
      );
      float d = length(uv - pos);
      float glow = 0.003 / (d * d + 0.003);
      color += mix(uColor1, uColor2, float(i) * 0.5) * glow;
    }
    
    color = clamp(color, 0.0, 1.0);
    gl_FragColor = vec4(color, 0.8);
  }
`;

const WAVE_FRAGMENT = `
  precision highp float;
  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec3 uColor1;
  uniform vec3 uColor2;

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float t = uTime * 0.2;
    
    float wave = 0.0;
    for (int i = 0; i < 5; i++) {
      float fi = float(i);
      wave += sin(uv.x * (3.0 + fi) + t * (1.0 + fi * 0.3) + fi * 1.5) * 0.15;
    }
    
    float intensity = wave * (1.0 - uv.y) * 1.5;
    vec3 color = mix(uColor1, uColor2, intensity);
    color += wave * uColor1 * 0.1;
    
    gl_FragColor = vec4(color, 0.7);
  }
`;

const GRADIENT_FRAGMENT = `
  precision highp float;
  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec3 uColor1;
  uniform vec3 uColor2;

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float t = uTime * 0.1;
    
    float angle = sin(t) * 0.5 + 0.5;
    float blend = uv.x * angle + uv.y * (1.0 - angle) + sin(t + uv.x * 2.0) * 0.1;
    blend = clamp(blend, 0.0, 1.0);
    
    vec3 color = mix(uColor1, uColor2, blend);
    gl_FragColor = vec4(color, 1.0);
  }
`;

const MATRIX_FRAGMENT = `
  precision highp float;
  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec3 uColor1;
  uniform vec3 uColor2;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float t = uTime * 0.5;
    
    vec2 pos = uv * vec2(40.0, 60.0);
    vec2 cell = floor(pos);
    vec2 sub = fract(pos);
    
    float seed = hash(cell);
    float fall = fract(t + seed * 10.0);
    float trail = smoothstep(0.0, 0.3, fall) * (1.0 - smoothstep(0.6, 1.0, fall));
    
    float glyph = sub.y > 0.8 ? 0.0 : trail;
    float intensity = glyph * (1.0 - uv.y * 0.5);
    
    vec3 color = mix(uColor1, uColor2, seed) * intensity;
    float fade = 1.0 - uv.y * 0.7;
    gl_FragColor = vec4(color * fade, 0.6);
  }
`;

const FRAGMENT_SHADERS: Record<EffectType, string> = {
  aurora: AURORA_FRAGMENT,
  particles: PARTICLE_FRAGMENT,
  waves: WAVE_FRAGMENT,
  gradient: GRADIENT_FRAGMENT,
  matrix: MATRIX_FRAGMENT,
};

function hexToRgb(hex: string): [number, number, number] {
  const c = hex.replace('#', '');
  return [
    parseInt(c.substring(0, 2), 16) / 255,
    parseInt(c.substring(2, 4), 16) / 255,
    parseInt(c.substring(4, 6), 16) / 255,
  ];
}

const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({
  effect = 'aurora',
  color1 = '#1B2A38',
  color2 = '#3B6D8A',
  speed = 1.0,
  className = '',
  children,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [glReady, setGlReady] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl', { alpha: true });
    if (!gl) {
      console.warn('[AnimatedBackground] WebGL not supported, falling back to CSS');
      setGlReady(false);
      return;
    }
    setGlReady(true);

    // Compile shaders
    const vs = gl.createShader(gl.VERTEX_SHADER)!;
    gl.shaderSource(vs, VERTEX_SHADER);
    gl.compileShader(vs);

    const fs = gl.createShader(gl.FRAGMENT_SHADER)!;
    gl.shaderSource(fs, FRAGMENT_SHADERS[effect]);
    gl.compileShader(fs);

    const program = gl.createProgram()!;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    gl.useProgram(program);

    // Full-screen quad
    const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    // Uniforms
    const uTime = gl.getUniformLocation(program, 'uTime');
    const uResolution = gl.getUniformLocation(program, 'uResolution');
    const uColor1 = gl.getUniformLocation(program, 'uColor1');
    const uColor2 = gl.getUniformLocation(program, 'uColor2');

    const rgb1 = hexToRgb(color1);
    const rgb2 = hexToRgb(color2);

    // Resize handler
    const resize = () => {
      canvas.width = canvas.clientWidth * window.devicePixelRatio;
      canvas.height = canvas.clientHeight * window.devicePixelRatio;
      gl.viewport(0, 0, canvas.width, canvas.height);
    };
    resize();
    window.addEventListener('resize', resize);

    // Animation loop
    let startTime = performance.now();
    let animId: number;

    const render = () => {
      const elapsed = (performance.now() - startTime) / 1000 * speed;
      gl.uniform1f(uTime, elapsed);
      gl.uniform2f(uResolution, canvas.width, canvas.height);
      gl.uniform3f(uColor1, rgb1[0], rgb1[1], rgb1[2]);
      gl.uniform3f(uColor2, rgb2[0], rgb2[1], rgb2[2]);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animId = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      gl.deleteProgram(program);
    };
  }, [effect, color1, color2, speed]);

  return (
    <div className={`relative overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ opacity: glReady ? 1 : 0.5 }}
      />
      {!glReady && (
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${color1}, ${color2})`,
            opacity: 0.8,
          }}
        />
      )}
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default AnimatedBackground;
