import { theme } from './theme';

export type ParticleType = 'lightBeam' | 'probe' | 'memory' | 'evolution';

export interface Particle {
  id: string;
  type: ParticleType;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  opacity: number;
  lifetime: number;
  age: number;
  targetX?: number;
  targetY?: number;
}

export interface ParticleConfig {
  color: string;
  size: { min: number; max: number };
  speed: { min: number; max: number };
  opacity: { min: number; max: number };
  lifetime: { min: number; max: number };
}

class ParticleManagerClass {
  private particles: Map<string, Particle> = new Map();
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private animationId: number | null = null;
  private lastTime: number = 0;
  private performanceMode: 'high' | 'medium' | 'low' = 'high';
  private maxParticles: number = theme.particles.maxCount;
  private onPerformanceWarning?: (message: string) => void;

  initialize(canvas: HTMLCanvasElement): void {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.startAnimation();
  }

  setPerformanceMode(mode: 'high' | 'medium' | 'low'): void {
    this.performanceMode = mode;
    switch (mode) {
      case 'high':
        this.maxParticles = theme.particles.maxCount;
        break;
      case 'medium':
        this.maxParticles = Math.floor(theme.particles.maxCount * 0.6);
        break;
      case 'low':
        this.maxParticles = Math.floor(theme.particles.maxCount * 0.3);
        break;
    }
    while (this.particles.size > this.maxParticles) {
      const firstKey = this.particles.keys().next().value;
      if (firstKey) this.particles.delete(firstKey);
    }
  }

  setPerformanceWarningCallback(callback: (message: string) => void): void {
    this.onPerformanceWarning = callback;
  }

  private getConfig(type: ParticleType): ParticleConfig {
    return theme.particles.types[type];
  }

  private randomInRange(min: number, max: number): number {
    return Math.random() * (max - min) + min;
  }

  createParticle(
    type: ParticleType,
    x: number,
    y: number,
    options?: {
      targetX?: number;
      targetY?: number;
      color?: string;
      size?: number;
    }
  ): string | null {
    if (this.particles.size >= this.maxParticles) {
      return null;
    }

    const config = this.getConfig(type);
    const id = `particle_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const speed = this.randomInRange(config.speed.min, config.speed.max);
    const angle = Math.random() * Math.PI * 2;
    
    const particle: Particle = {
      id,
      type,
      x,
      y,
      vx: options?.targetX !== undefined 
        ? (options.targetX - x) / 100 
        : Math.cos(angle) * speed,
      vy: options?.targetY !== undefined 
        ? (options.targetY - y) / 100 
        : Math.sin(angle) * speed,
      size: options?.size ?? this.randomInRange(config.size.min, config.size.max),
      color: options?.color ?? config.color,
      opacity: this.randomInRange(config.opacity.min, config.opacity.max),
      lifetime: this.randomInRange(config.lifetime.min, config.lifetime.max),
      age: 0,
      targetX: options?.targetX,
      targetY: options?.targetY,
    };

    this.particles.set(id, particle);
    return id;
  }

  createBurst(
    type: ParticleType,
    x: number,
    y: number,
    count: number,
    options?: {
      spread?: number;
      targetX?: number;
      targetY?: number;
    }
  ): string[] {
    const ids: string[] = [];
    const spread = options?.spread ?? Math.PI * 2;
    const startAngle = Math.random() * Math.PI * 2;

    for (let i = 0; i < count; i++) {
      if (this.particles.size >= this.maxParticles) break;
      
      const angle = startAngle + (spread * i) / count;
      const config = this.getConfig(type);
      const speed = this.randomInRange(config.speed.min, config.speed.max);
      
      const id = this.createParticle(type, x, y, {
        targetX: options?.targetX ?? x + Math.cos(angle) * speed * 2,
        targetY: options?.targetY ?? y + Math.sin(angle) * speed * 2,
      });
      
      if (id) {
        const particle = this.particles.get(id);
        if (particle) {
          particle.vx = Math.cos(angle) * speed * 0.1;
          particle.vy = Math.sin(angle) * speed * 0.1;
        }
        ids.push(id);
      }
    }
    
    return ids;
  }

  createBeam(
    type: ParticleType,
    startX: number,
    startY: number,
    endX: number,
    endY: number,
    count: number
  ): string[] {
    const ids: string[] = [];
    
    for (let i = 0; i < count; i++) {
      const progress = i / count;
      const x = startX + (endX - startX) * progress;
      const y = startY + (endY - startY) * progress;
      
      const id = this.createParticle(type, x, y, {
        targetX: endX,
        targetY: endY,
      });
      
      if (id) ids.push(id);
    }
    
    return ids;
  }

  removeParticle(id: string): void {
    this.particles.delete(id);
  }

  clearParticles(): void {
    this.particles.clear();
  }

  private update(deltaTime: number): void {
    const toRemove: string[] = [];
    
    this.particles.forEach((particle, id) => {
      particle.age += deltaTime;
      
      if (particle.age >= particle.lifetime) {
        toRemove.push(id);
        return;
      }
      
      if (particle.targetX !== undefined && particle.targetY !== undefined) {
        const dx = particle.targetX - particle.x;
        const dy = particle.targetY - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 5) {
          const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
          particle.vx = (dx / distance) * speed;
          particle.vy = (dy / distance) * speed;
        }
      }
      
      particle.x += particle.vx * deltaTime * 0.1;
      particle.y += particle.vy * deltaTime * 0.1;
      
      const lifeRatio = 1 - particle.age / particle.lifetime;
      particle.opacity = lifeRatio * 0.8;
    });
    
    toRemove.forEach(id => this.particles.delete(id));
  }

  private render(): void {
    if (!this.ctx || !this.canvas) return;
    
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    this.particles.forEach(particle => {
      if (!this.ctx) return;
      
      this.ctx.beginPath();
      this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      this.ctx.fillStyle = particle.color;
      this.ctx.globalAlpha = particle.opacity;
      this.ctx.fill();
      
      this.ctx.shadowColor = particle.color;
      this.ctx.shadowBlur = particle.size * 2;
    });
    
    this.ctx.globalAlpha = 1;
    this.ctx.shadowBlur = 0;
  }

  private animate = (currentTime: number): void => {
    const deltaTime = currentTime - this.lastTime;
    this.lastTime = currentTime;
    
    if (deltaTime > theme.particles.performanceThreshold) {
      if (this.performanceMode === 'high') {
        this.setPerformanceMode('medium');
        this.onPerformanceWarning?.(
          `检测到帧时间过长(${deltaTime.toFixed(1)}ms)，已降低粒子数量`
        );
      }
    }
    
    this.update(deltaTime);
    this.render();
    
    this.animationId = requestAnimationFrame(this.animate);
  };

  private startAnimation(): void {
    if (this.animationId) return;
    this.lastTime = performance.now();
    this.animationId = requestAnimationFrame(this.animate);
  }

  stopAnimation(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  getParticleCount(): number {
    return this.particles.size;
  }

  getParticlesByType(type: ParticleType): Particle[] {
    return Array.from(this.particles.values()).filter(p => p.type === type);
  }
}

export const ParticleManager = new ParticleManagerClass();
export default ParticleManager;
