type ParticleType = 'data' | 'pheromone' | 'liveness' | 'consensus' | 'memory' | 'evolution';

interface ParticleConfig {
  color: string;
  speed: number;
  lifetime: number;
  size: number;
  glow: boolean;
}

interface Particle {
  id: string;
  type: ParticleType;
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  color: string;
  glow: boolean;
  trail: { x: number; y: number }[];
}

const PARTICLE_CONFIGS: Record<ParticleType, ParticleConfig> = {
  data: { color: '#3B82F6', speed: 3, lifetime: 100, size: 4, glow: true },
  pheromone: { color: '#60A5FA', speed: 1.5, lifetime: 150, size: 3, glow: false },
  liveness: { color: '#10B981', speed: 2, lifetime: 80, size: 5, glow: true },
  consensus: { color: '#F59E0B', speed: 4, lifetime: 60, size: 6, glow: true },
  memory: { color: '#8B5CF6', speed: 2.5, lifetime: 120, size: 4, glow: true },
  evolution: { color: '#D4AF37', speed: 3, lifetime: 100, size: 5, glow: true },
};

const MAX_PARTICLES = 100;
const TRAIL_LENGTH = 8;

class UnifiedParticleManager {
  private particles: Map<string, Particle> = new Map();
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private animationId: number = 0;
  private isRunning: boolean = false;
  private lowPerformanceMode: boolean = false;
  private particleIdCounter: number = 0;

  initialize(canvas: HTMLCanvasElement): void {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    if (!this.ctx) {
      console.warn('Failed to get canvas context');
    }
  }

  setLowPerformanceMode(enabled: boolean): void {
    this.lowPerformanceMode = enabled;
    if (enabled && this.particles.size > 30) {
      const keys = Array.from(this.particles.keys()).slice(30);
      keys.forEach(key => this.particles.delete(key));
    }
  }

  createParticle(
    type: ParticleType,
    x: number,
    y: number,
    targetX?: number,
    targetY?: number
  ): string | null {
    if (this.lowPerformanceMode && this.particles.size >= 30) {
      return null;
    }
    if (!this.lowPerformanceMode && this.particles.size >= MAX_PARTICLES) {
      return null;
    }

    const config = PARTICLE_CONFIGS[type];
    const id = `particle_${++this.particleIdCounter}`;

    let vx = (Math.random() - 0.5) * config.speed * 2;
    let vy = (Math.random() - 0.5) * config.speed * 2;

    if (targetX !== undefined && targetY !== undefined) {
      const dx = targetX - x;
      const dy = targetY - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > 0) {
        vx = (dx / dist) * config.speed;
        vy = (dy / dist) * config.speed;
      }
    }

    const particle: Particle = {
      id,
      type,
      x,
      y,
      vx,
      vy,
      life: config.lifetime,
      maxLife: config.lifetime,
      size: config.size,
      color: config.color,
      glow: config.glow,
      trail: [],
    };

    this.particles.set(id, particle);
    return id;
  }

  createBurst(
    type: ParticleType,
    x: number,
    y: number,
    count: number
  ): string[] {
    const ids: string[] = [];
    for (let i = 0; i < count; i++) {
      const id = this.createParticle(type, x, y);
      if (id) ids.push(id);
    }
    return ids;
  }

  createFlow(
    type: ParticleType,
    startX: number,
    startY: number,
    endX: number,
    endY: number,
    count: number,
    interval: number = 100
  ): void {
    let created = 0;
    const createNext = () => {
      if (created >= count) return;
      this.createParticle(type, startX, startY, endX, endY);
      created++;
      setTimeout(createNext, interval);
    };
    createNext();
  }

  removeParticle(id: string): void {
    this.particles.delete(id);
  }

  clearAll(): void {
    this.particles.clear();
  }

  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.animate();
  }

  stop(): void {
    this.isRunning = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }

  private animate = (): void => {
    if (!this.isRunning || !this.canvas || !this.ctx) return;

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    const toRemove: string[] = [];

    this.particles.forEach((particle) => {
      particle.trail.push({ x: particle.x, y: particle.y });
      if (particle.trail.length > TRAIL_LENGTH) {
        particle.trail.shift();
      }

      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.life--;

      if (particle.life <= 0) {
        toRemove.push(particle.id);
        return;
      }

      const alpha = particle.life / particle.maxLife;

      if (particle.trail.length > 1) {
        this.ctx.beginPath();
        this.ctx.moveTo(particle.trail[0].x, particle.trail[0].y);
        particle.trail.forEach((point, index) => {
          this.ctx.lineTo(point.x, point.y);
        });
        this.ctx.strokeStyle = `${particle.color}${Math.floor(alpha * 0.3 * 255).toString(16).padStart(2, '0')}`;
        this.ctx.lineWidth = particle.size * 0.5;
        this.ctx.stroke();
      }

      this.ctx.beginPath();
      this.ctx.arc(particle.x, particle.y, particle.size * alpha, 0, Math.PI * 2);

      if (particle.glow) {
        const gradient = this.ctx.createRadialGradient(
          particle.x, particle.y, 0,
          particle.x, particle.y, particle.size * 2
        );
        gradient.addColorStop(0, particle.color);
        gradient.addColorStop(0.5, `${particle.color}80`);
        gradient.addColorStop(1, `${particle.color}00`);
        this.ctx.fillStyle = gradient;
      } else {
        this.ctx.fillStyle = `${particle.color}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`;
      }

      this.ctx.fill();
    });

    toRemove.forEach(id => this.particles.delete(id));

    this.animationId = requestAnimationFrame(this.animate);
  };

  getParticleCount(): number {
    return this.particles.size;
  }

  getParticlesByType(type: ParticleType): Particle[] {
    return Array.from(this.particles.values()).filter(p => p.type === type);
  }
}

export const particleManager = new UnifiedParticleManager();
export type { ParticleType, Particle, ParticleConfig };
