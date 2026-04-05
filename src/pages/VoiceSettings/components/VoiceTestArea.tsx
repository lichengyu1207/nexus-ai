import { useState } from 'react';
import { motion } from 'framer-motion';
import { SpeakerWaveIcon, PlayIcon, StopIcon } from '@heroicons/react/24/outline';
import type { VoiceSettings, SpeechOptions } from '../types';
import { RATE_OPTIONS } from '../types';

interface VoiceTestAreaProps {
  settings: VoiceSettings;
  onSpeak: (text: string, options?: SpeechOptions) => Promise<void>;
  onStop: () => void;
  voices: SpeechSynthesisVoice[];
}

export function VoiceTestArea({ settings, onSpeak, onStop, voices }: VoiceTestAreaProps) {
  const [testText, setTestText] = useState('您好，这是语音测试。欢迎使用房都督平台。');
  const [selectedVoice, setSelectedVoice] = useState<string>(settings.voiceURI);
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlay = async () => {
    if (isPlaying) {
      onStop();
      setIsPlaying(false);
      return;
    }

    setIsPlaying(true);
    try {
      await onSpeak(testText, { voiceURI: selectedVoice || undefined });
    } finally {
      setIsPlaying(false);
    }
  };

  const chineseVoices = voices.filter(
    (v) => v.lang.includes('zh') || v.lang.includes('CN')
  );

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
      <div className="flex items-center gap-2 mb-4">
        <SpeakerWaveIcon className="w-5 h-5 text-amber-400" />
        <h3 className="text-lg font-semibold text-white">语音测试</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-2">测试文本</label>
          <textarea
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            rows={3}
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 resize-none"
            placeholder="输入要测试的文本..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">选择音色</label>
            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-amber-500/50"
            >
              <option value="">默认音色</option>
              {chineseVoices.map((voice) => (
                <option key={voice.voiceURI} value={voice.voiceURI}>
                  {voice.name} ({voice.lang})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">语速</label>
            <select
              value={settings.rate}
              disabled
              className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-xl text-slate-400 cursor-not-allowed"
            >
              {RATE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handlePlay}
          disabled={!testText.trim()}
          className={`
            w-full py-3 rounded-xl font-medium flex items-center justify-center gap-2
            transition-colors
            ${isPlaying
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'bg-amber-500 text-slate-900 hover:bg-amber-400'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {isPlaying ? (
            <>
              <StopIcon className="w-5 h-5" />
              停止播放
            </>
          ) : (
            <>
              <PlayIcon className="w-5 h-5" />
              播放测试
            </>
          )}
        </motion.button>

        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>音量: {Math.round(settings.volume * 100)}%</span>
          <span>语速: {settings.rate}x</span>
          <span>音调: {settings.pitch}</span>
        </div>
      </div>
    </div>
  );
}
