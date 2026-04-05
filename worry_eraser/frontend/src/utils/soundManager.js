class SoundManager {
    constructor() {
        this.audioContext = null;
        this.sounds = new Map();
        this.enabled = true;
        this.initAudioContext();
    }
    initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        catch (error) {
            console.warn('Web Audio API not supported');
        }
    }
    async loadSound(name, url) {
        if (!this.audioContext)
            return;
        try {
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            this.sounds.set(name, audioBuffer);
        }
        catch (error) {
            console.error(`Failed to load sound: ${name}`, error);
        }
    }
    play(name, volume = 0.5) {
        if (!this.audioContext || !this.enabled)
            return;
        const audioBuffer = this.sounds.get(name);
        if (!audioBuffer) {
            console.warn(`Sound not found: ${name}`);
            return;
        }
        try {
            const source = this.audioContext.createBufferSource();
            const gainNode = this.audioContext.createGain();
            source.buffer = audioBuffer;
            gainNode.gain.value = volume;
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            source.start(0);
        }
        catch (error) {
            console.error(`Failed to play sound: ${name}`, error);
        }
    }
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
    isEnabled() {
        return this.enabled;
    }
    resume() {
        if (this.audioContext?.state === 'suspended') {
            this.audioContext.resume();
        }
    }
}
export const soundManager = new SoundManager();
export const SOUNDS = {
    SEND: 'send',
    RECEIVE: 'receive',
    MEMORY: 'memory',
    REPORT: 'report',
    CLICK: 'click',
    SUCCESS: 'success',
};
