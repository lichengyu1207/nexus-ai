import { useCallback, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { VoiceCommand, VoiceRecognitionResult } from '../types';

interface UseVoiceCommandsOptions {
  onResult?: (result: VoiceRecognitionResult) => void;
  onError?: (error: string) => void;
  onCommand?: (command: VoiceCommand) => void;
}

export function useVoiceCommands(options: UseVoiceCommandsOptions = {}) {
  const { onResult, onError, onCommand } = options;
  const navigate = useNavigate();
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);

  const commands: VoiceCommand[] = useMemo(() => [
    {
      phrase: '新建任务',
      action: () => navigate('/tasks/new'),
      description: '创建新任务',
    },
    {
      phrase: '任务列表',
      action: () => navigate('/tasks'),
      description: '查看任务列表',
    },
    {
      phrase: '智能体状态',
      action: () => navigate('/agents'),
      description: '查看智能体状态',
    },
    {
      phrase: '打开设置',
      action: () => navigate('/settings'),
      description: '打开设置页面',
    },
    {
      phrase: '语音设置',
      action: () => navigate('/voice-settings'),
      description: '打开语音设置',
    },
    {
      phrase: '仪表盘',
      action: () => navigate('/'),
      description: '返回首页',
    },
  ], [navigate]);

  const matchCommand = useCallback((transcript: string): VoiceCommand | null => {
    const normalized = transcript.toLowerCase().trim();
    for (const cmd of commands) {
      const phrase = typeof cmd.phrase === 'string' 
        ? cmd.phrase.toLowerCase() 
        : cmd.phrase.source.toLowerCase();
      if (normalized.includes(phrase)) {
        return cmd;
      }
    }
    return null;
  }, [commands]);

  const startListening = useCallback(() => {
    if (isListeningRef.current) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError?.('您的浏览器不支持语音识别');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      const confidence = result[0].confidence;
      const isFinal = result.isFinal;

      onResult?.({ transcript, confidence, isFinal });

      if (isFinal) {
        const matchedCommand = matchCommand(transcript);
        if (matchedCommand) {
          matchedCommand.action();
          onCommand?.(matchedCommand);
        }
      }
    };

    recognition.onerror = (event) => {
      isListeningRef.current = false;
      onError?.(event.error);
    };

    recognition.onend = () => {
      isListeningRef.current = false;
    };

    recognitionRef.current = recognition;
    isListeningRef.current = true;

    try {
      recognition.start();
    } catch (e) {
      isListeningRef.current = false;
      onError?.('启动语音识别失败');
    }
  }, [matchCommand, onCommand, onError, onResult]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListeningRef.current) {
      recognitionRef.current.stop();
      isListeningRef.current = false;
    }
  }, []);

  const toggleListening = useCallback(() => {
    if (isListeningRef.current) {
      stopListening();
    } else {
      startListening();
    }
  }, [startListening, stopListening]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  return {
    commands,
    startListening,
    stopListening,
    toggleListening,
    isListening: isListeningRef.current,
  };
}
