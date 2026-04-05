import { useCallback, useEffect, useRef, useState } from 'react';

interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionWrapperOptions {
  onResult?: (result: SpeechRecognitionResult) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  continuous?: boolean;
  interimResults?: boolean;
  lang?: string;
}

interface SpeechRecognitionWrapperReturn {
  isListening: boolean;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  transcript: string;
  interimTranscript: string;
  error: string | null;
}

type SpeechRecognitionEvent = {
  resultIndex: number;
  results: SpeechRecognitionResultList;
};

type SpeechRecognitionErrorEvent = {
  error: string;
  message: string;
};

type SpeechRecognitionResultList = {
  length: number;
  [index: number]: {
    isFinal: boolean;
    [itemIndex: number]: {
      transcript: string;
      confidence: number;
    };
  };
};

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onstart: (() => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor;
    webkitSpeechRecognition: SpeechRecognitionConstructor;
  }
}

export function useSpeechRecognition(
  options: SpeechRecognitionWrapperOptions = {}
): SpeechRecognitionWrapperReturn {
  const {
    onResult,
    onError,
    onStart,
    onEnd,
    continuous = false,
    interimResults = true,
    lang = 'zh-CN',
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  const isSupported = typeof window !== 'undefined' && 
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognitionAPI();

    const recognition = recognitionRef.current;
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = lang;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
          if (onResult) {
            onResult({
              transcript: result[0].transcript,
              confidence: result[0].confidence,
            });
          }
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalTranscript) {
        setTranscript((prev) => prev + finalTranscript);
      }
      setInterimTranscript(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessage = getErrorMessage(event.error);
      setError(errorMessage);
      setIsListening(false);
      if (onError) {
        onError(errorMessage);
      }
    };

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      if (onStart) {
        onStart();
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
      if (onEnd) {
        onEnd();
      }
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [isSupported, continuous, interimResults, lang, onResult, onError, onStart, onEnd]);

  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current) {
      setError('当前浏览器不支持语音识别');
      return;
    }

    if (isListening) {
      return;
    }

    setError(null);
    setTranscript('');
    setInterimTranscript('');

    try {
      recognitionRef.current.start();
    } catch (err) {
      setError('启动语音识别失败');
    }
  }, [isSupported, isListening]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) {
      return;
    }

    try {
      recognitionRef.current.stop();
    } catch (err) {
      setError('停止语音识别失败');
    }
  }, [isListening]);

  return {
    isListening,
    isSupported,
    startListening,
    stopListening,
    transcript,
    interimTranscript,
    error,
  };
}

function getErrorMessage(error: string): string {
  const errorMessages: Record<string, string> = {
    'no-speech': '未检测到语音输入',
    'audio-capture': '未找到麦克风设备',
    'not-allowed': '麦克风权限被拒绝',
    'network': '网络连接错误',
    'aborted': '语音识别被中止',
    'service-not-allowed': '语音识别服务不可用',
    'language-not-supported': '不支持的语言',
    'bad-grammar': '语法错误',
  };

  return errorMessages[error] || `语音识别错误: ${error}`;
}

export class SpeechRecognitionWrapper {
  private recognition: SpeechRecognitionInstance | null = null;
  private isSupported: boolean;

  constructor() {
    this.isSupported = typeof window !== 'undefined' && 
      ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

    if (this.isSupported) {
      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognitionAPI();
    }
  }

  checkSupport(): boolean {
    return this.isSupported;
  }

  configure(options: {
    continuous?: boolean;
    interimResults?: boolean;
    lang?: string;
  }): void {
    if (!this.recognition) return;

    if (options.continuous !== undefined) {
      this.recognition.continuous = options.continuous;
    }
    if (options.interimResults !== undefined) {
      this.recognition.interimResults = options.interimResults;
    }
    if (options.lang !== undefined) {
      this.recognition.lang = options.lang;
    }
  }

  start(
    onResult: (transcript: string, confidence: number) => void,
    onError?: (error: string) => void,
    onStart?: () => void,
    onEnd?: () => void
  ): void {
    if (!this.recognition) {
      onError?.('当前浏览器不支持语音识别');
      return;
    }

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          onResult(result[0].transcript, result[0].confidence);
        }
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      onError?.(getErrorMessage(event.error));
    };

    this.recognition.onstart = () => {
      onStart?.();
    };

    this.recognition.onend = () => {
      onEnd?.();
    };

    try {
      this.recognition.start();
    } catch (err) {
      onError?.('启动语音识别失败');
    }
  }

  stop(): void {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.error('停止语音识别失败:', err);
      }
    }
  }

  abort(): void {
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (err) {
        console.error('中止语音识别失败:', err);
      }
    }
  }
}

export default SpeechRecognitionWrapper;
