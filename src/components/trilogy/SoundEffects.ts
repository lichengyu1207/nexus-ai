type SoundType = 
  | 'memoryRecall'
  | 'miningSuccess'
  | 'evolutionComplete'
  | 'zhouyuSpeak'
  | 'luxunSpeak'
  | 'taskComplete'
  | 'dataFlow'
  | 'alert';

interface SoundConfig {
  src: string;
  volume: number;
  preload?: boolean;
}

const soundConfigs: Record<SoundType, SoundConfig> = {
  memoryRecall: { src: '/sounds/memory-recall.mp3', volume: 0.3, preload: true },
  miningSuccess: { src: '/sounds/mining-success.mp3', volume: 0.5, preload: true },
  evolutionComplete: { src: '/sounds/evolution-complete.mp3', volume: 0.7, preload: true },
  zhouyuSpeak: { src: '/sounds/zhouyu-speak.mp3', volume: 0.4, preload: true },
  luxunSpeak: { src: '/sounds/luxun-speak.mp3', volume: 0.4, preload: true },
  taskComplete: { src: '/sounds/task-complete.mp3', volume: 0.5, preload: true },
  dataFlow: { src: '/sounds/data-flow.mp3', volume: 0.2, preload: false },
  alert: { src: '/sounds/alert.mp3', volume: 0.6, preload: true },
};

class SoundEffectsClass {
  private audioContext: AudioContext | null = null;
  private sounds: Map<SoundType, AudioBuffer> = new Map();
  private enabled: boolean = true;
  private masterVolume: number = 1.0;

  async initialize(): Promise<void> {
    try {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      
      const preloadPromises = Object.entries(soundConfigs)
        .filter(([, config]) => config.preload)
        .map(([type, config]) => this.loadSound(type as SoundType, config.src));
      
      await Promise.all(preloadPromises);
    } catch (error) {
      console.warn('音频系统初始化失败:', error);
    }
  }

  private async loadSound(type: SoundType, src: string): Promise<void> {
    if (!this.audioContext) return;
    
    try {
      const response = await fetch(src);
      if (!response.ok) {
        return;
      }
      const arrayBuffer = await response.arrayBuffer();
      if (arrayBuffer.byteLength === 0) {
        return;
      }
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      this.sounds.set(type, audioBuffer);
    } catch {
    }
  }

  play(type: SoundType, options?: { volume?: number; rate?: number }): void {
    if (!this.enabled || !this.audioContext) return;
    
    const buffer = this.sounds.get(type);
    if (!buffer) {
      this.loadSound(type, soundConfigs[type].src).then(() => {
        this.play(type, options);
      });
      return;
    }
    
    try {
      const source = this.audioContext.createBufferSource();
      source.buffer = buffer;
      
      const gainNode = this.audioContext.createGain();
      const volume = (options?.volume ?? soundConfigs[type].volume) * this.masterVolume;
      gainNode.gain.value = volume;
      
      if (options?.rate) {
        source.playbackRate.value = options.rate;
      }
      
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      source.start(0);
    } catch (error) {
      console.warn(`播放音效失败: ${type}`, error);
    }
  }

  playTone(frequency: number, duration: number = 0.1, type: OscillatorType = 'sine'): void {
    if (!this.enabled || !this.audioContext) return;
    
    try {
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();
      
      oscillator.type = type;
      oscillator.frequency.value = frequency;
      
      gainNode.gain.setValueAtTime(0.3 * this.masterVolume, this.audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      oscillator.start();
      oscillator.stop(this.audioContext.currentTime + duration);
    } catch (error) {
      console.warn('播放音调失败:', error);
    }
  }

  playMemoryRecall(): void {
    this.playTone(523.25, 0.3, 'sine');
    setTimeout(() => this.playTone(659.25, 0.2, 'sine'), 100);
  }

  playMiningSuccess(): void {
    this.playTone(880, 0.1, 'triangle');
    setTimeout(() => this.playTone(1108.73, 0.15, 'triangle'), 50);
    setTimeout(() => this.playTone(1318.51, 0.2, 'triangle'), 100);
  }

  playEvolutionComplete(): void {
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 0.4, 'sine'), i * 150);
    });
  }

  playZhouyuSpeak(): void {
    this.playTone(392, 0.15, 'sine');
    setTimeout(() => this.playTone(440, 0.1, 'sine'), 100);
  }

  playLuxunSpeak(): void {
    this.playTone(349.23, 0.15, 'sine');
    setTimeout(() => this.playTone(392, 0.1, 'sine'), 100);
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  setMasterVolume(volume: number): void {
    this.masterVolume = Math.max(0, Math.min(1, volume));
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  resume(): void {
    if (this.audioContext?.state === 'suspended') {
      this.audioContext.resume();
    }
  }
}

export const SoundEffects = new SoundEffectsClass();
export default SoundEffects;
