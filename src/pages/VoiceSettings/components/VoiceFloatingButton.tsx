import { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MicrophoneIcon, SpeakerWaveIcon, XMarkIcon } from '@heroicons/react/24/outline';
import type { VoiceRecognitionResult, VoiceSettings } from '../types';
import { useVoiceCommands } from '../hooks/useVoiceCommands';

interface VoiceFloatingButtonProps {
  settings: VoiceSettings;
  onSpeak: (text: string) => void;
  onSettingsClick?: () => void;
}

export function VoiceFloatingButton({ settings, onSpeak, onSettingsClick }: VoiceFloatingButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [lastResult, setLastResult] = useState<VoiceRecognitionResult | null>(null);
  const [showCaption, setShowCaption] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleResult = useCallback((result: VoiceRecognitionResult) => {
    setLastResult(result);
    setShowCaption(true);
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      setShowCaption(false);
    }, 3000);
  }, []);

  const handleCommand = useCallback(() => {
    onSpeak('好的，正在为您执行');
  }, [onSpeak]);

  const handleError = useCallback((error: string) => {
    setLastResult({
      transcript: `错误: ${error}`,
      confidence: 0,
      isFinal: true,
    });
    setShowCaption(true);
    setIsListening(false);
  }, []);

  const { toggleListening } = useVoiceCommands({
    onResult: handleResult,
    onCommand: handleCommand,
    onError: handleError,
  });

  const handleToggle = useCallback(() => {
    if (!settings.enabled) return;
    
    setIsListening((prev) => {
      const newValue = !prev;
      toggleListening();
      
      if (newValue) {
        onSpeak('请说出您的指令');
      }
      
      return newValue;
    });
  }, [settings.enabled, toggleListening, onSpeak]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      <AnimatePresence>
        {showCaption && lastResult && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="bg-slate-800/90 backdrop-blur-sm rounded-xl border border-slate-700/50 px-4 py-3 max-w-xs"
          >
            <div className="flex items-start gap-3">
              <SpeakerWaveIcon className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-white">{lastResult.transcript}</p>
                {!lastResult.isFinal && (
                  <p className="text-xs text-slate-400 mt-1">正在识别...</p>
                )}
              </div>
              <button
                onClick={() => setShowCaption(false)}
                className="text-slate-400 hover:text-white"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative">
        <AnimatePresence>
          {isListening && (
            <>
              {[...Array(3)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ scale: 1, opacity: 0.5 }}
                  animate={{ scale: 2, opacity: 0 }}
                  exit={{ scale: 1, opacity: 0 }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.3,
                  }}
                  className="absolute inset-0 rounded-full bg-amber-500/30"
                />
              ))}
            </>
          )}
        </AnimatePresence>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleToggle}
          disabled={!settings.enabled}
          className={`
            relative w-14 h-14 rounded-full flex items-center justify-center
            backdrop-blur-sm border transition-all duration-200
            ${isListening 
              ? 'bg-amber-500 border-amber-400 text-slate-900' 
              : settings.enabled
              ? 'bg-slate-800/80 border-slate-700/50 text-white hover:border-amber-500/50'
              : 'bg-slate-800/50 border-slate-700/30 text-slate-500 cursor-not-allowed'
            }
          `}
        >
          <MicrophoneIcon className={`w-6 h-6 ${isListening ? 'animate-pulse' : ''}`} />
        </motion.button>

        <AnimatePresence>
          {isListening && (
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-slate-900"
            />
          )}
        </AnimatePresence>
      </div>

      {settings.enabled && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          whileHover={{ scale: 1.02 }}
          onClick={onSettingsClick}
          className="text-xs text-slate-400 hover:text-amber-400 transition-colors"
        >
          语音设置
        </motion.button>
      )}
    </div>
  );
}
