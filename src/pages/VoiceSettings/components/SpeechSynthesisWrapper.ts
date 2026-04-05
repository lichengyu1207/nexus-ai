import { useRef, useCallback, useEffect } from 'react';
import type { SpeechQueueItem, SpeechOptions, VoiceSettings } from '../types';

class SpeechSynthesisManager {
  private static instance: SpeechSynthesisManager;
  private queue: SpeechQueueItem[] = [];
  private isSpeaking = false;
  private currentUtterance: SpeechSynthesisUtterance | null = null;

  static getInstance(): SpeechSynthesisManager {
    if (!SpeechSynthesisManager.instance) {
      SpeechSynthesisManager.instance = new SpeechSynthesisManager();
    }
    return SpeechSynthesisManager.instance;
  }

  speak(text: string, options?: SpeechOptions): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('浏览器不支持语音合成'));
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      
      if (options?.voiceURI) {
        const voices = window.speechSynthesis.getVoices();
        const voice = voices.find((v) => v.voiceURI === options.voiceURI);
        if (voice) utterance.voice = voice;
      }

      utterance.rate = options?.rate ?? 1.0;
      utterance.pitch = options?.pitch ?? 1.0;
      utterance.volume = options?.volume ?? 1.0;
      utterance.lang = 'zh-CN';

      utterance.onend = () => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        this.processQueue();
        resolve();
      };

      utterance.onerror = (event) => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        this.processQueue();
        reject(new Error(event.error));
      };

      const item: SpeechQueueItem = {
        text,
        options,
        id: `${Date.now()}-${Math.random()}`,
      };

      this.queue.push(item);
      this.processQueue();
    });
  }

  private processQueue() {
    if (this.isSpeaking || this.queue.length === 0) return;

    const item = this.queue.shift();
    if (!item) return;

    this.isSpeaking = true;
    const utterance = new SpeechSynthesisUtterance(item.text);

    if (item.options?.voiceURI) {
      const voices = window.speechSynthesis.getVoices();
      const voice = voices.find((v) => v.voiceURI === item.options?.voiceURI);
      if (voice) utterance.voice = voice;
    }

    utterance.rate = item.options?.rate ?? 1.0;
    utterance.pitch = item.options?.pitch ?? 1.0;
    utterance.volume = item.options?.volume ?? 1.0;
    utterance.lang = 'zh-CN';

    utterance.onend = () => {
      this.isSpeaking = false;
      this.currentUtterance = null;
      this.processQueue();
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      this.currentUtterance = null;
      this.processQueue();
    };

    this.currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }

  stop() {
    window.speechSynthesis.cancel();
    this.queue = [];
    this.isSpeaking = false;
    this.currentUtterance = null;
  }

  pause() {
    window.speechSynthesis.pause();
  }

  resume() {
    window.speechSynthesis.resume();
  }

  getIsSpeaking() {
    return this.isSpeaking;
  }

  getVoices(): SpeechSynthesisVoice[] {
    return window.speechSynthesis?.getVoices() ?? [];
  }
}

export const speechSynthesisManager = SpeechSynthesisManager.getInstance();

export function useSpeechSynthesis(settings: VoiceSettings) {
  const managerRef = useRef(speechSynthesisManager);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = managerRef.current.getVoices();
      setVoices(availableVoices);
    };

    loadVoices();
    
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const speak = useCallback((text: string, options?: SpeechOptions) => {
    if (!settings.enabled) return Promise.resolve();
    
    return managerRef.current.speak(text, {
      volume: settings.volume,
      rate: settings.rate,
      pitch: settings.pitch,
      voiceURI: options?.voiceURI ?? settings.voiceURI,
      ...options,
    });
  }, [settings]);

  const stop = useCallback(() => {
    managerRef.current.stop();
  }, []);

  const pause = useCallback(() => {
    managerRef.current.pause();
  }, []);

  const resume = useCallback(() => {
    managerRef.current.resume();
  }, []);

  const getChineseVoices = useCallback(() => {
    return voices.filter((v) => v.lang.includes('zh') || v.lang.includes('CN'));
  }, [voices]);

  return {
    speak,
    stop,
    pause,
    resume,
    voices,
    chineseVoices: getChineseVoices(),
    isSupported: 'speechSynthesis' in window,
  };
}

import { useState } from 'react';
