import { useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  SpeakerWaveIcon,
  CogIcon,
  BellIcon,
} from '@heroicons/react/24/outline';
import { useVoiceSettings } from './hooks/useVoiceSettings';
import { useSpeechSynthesis } from './components/SpeechSynthesisWrapper';
import { VoiceTestArea } from './components/VoiceTestArea';
import { CustomVoiceUpload } from './components/CustomVoiceUpload';
import { EVENT_LABELS, RATE_OPTIONS, type VoiceEventType } from './types';

export default function VoiceSettingsPage() {
  const {
    settings,
    updateSettings,
    updateEvent,
    setCustomSound,
    isSaving,
  } = useVoiceSettings();

  const { speak, stop, voices, chineseVoices, isSupported } = useSpeechSynthesis(settings);

  const handleSpeak = useCallback((text: string) => {
    return speak(text);
  }, [speak]);

  const handleUpload = async (type: VoiceEventType, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    try {
      const response = await fetch('/api/user/voice-sounds', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();
      setCustomSound(type, data.url);
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  };

  const handleDelete = (type: VoiceEventType) => {
    setCustomSound(type, undefined);
  };

  if (!isSupported) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <SpeakerWaveIcon className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h1 className="text-xl font-semibold text-white mb-2">浏览器不支持</h1>
          <p className="text-slate-400">
            您的浏览器不支持语音合成功能，请使用现代浏览器（Chrome、Edge、Safari）
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <SpeakerWaveIcon className="w-8 h-8 text-amber-400" />
            <h1 className="text-2xl font-bold text-white">语音交互设置</h1>
          </div>
          <p className="text-slate-400">
            配置语音播报、语音指令和自定义配音
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <CogIcon className="w-5 h-5 text-amber-400" />
              <h3 className="text-lg font-semibold text-white">基础设置</h3>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">启用语音</p>
                  <p className="text-sm text-slate-400">开启后平台将播报重要事件</p>
                </div>
                <button
                  onClick={() => updateSettings({ enabled: !settings.enabled })}
                  className={`
                    relative w-12 h-6 rounded-full transition-colors
                    ${settings.enabled ? 'bg-amber-500' : 'bg-slate-700'}
                  `}
                >
                  <motion.div
                    animate={{ x: settings.enabled ? 24 : 0 }}
                    className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow"
                  />
                </button>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-white font-medium">音量</p>
                  <span className="text-sm text-slate-400">{Math.round(settings.volume * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.volume}
                  onChange={(e) => updateSettings({ volume: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
              </div>

              <div>
                <p className="text-white font-medium mb-2">语速</p>
                <div className="grid grid-cols-4 gap-2">
                  {RATE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => updateSettings({ rate: opt.value })}
                      className={`
                        py-2 rounded-lg text-sm transition-colors
                        ${settings.rate === opt.value
                          ? 'bg-amber-500 text-slate-900 font-medium'
                          : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
                        }
                      `}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-white font-medium mb-2">默认音色</p>
                <select
                  value={settings.voiceURI}
                  onChange={(e) => updateSettings({ voiceURI: e.target.value })}
                  className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-amber-500/50"
                >
                  <option value="">系统默认</option>
                  {chineseVoices.map((voice) => (
                    <option key={voice.voiceURI} value={voice.voiceURI}>
                      {voice.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <BellIcon className="w-5 h-5 text-amber-400" />
              <h3 className="text-lg font-semibold text-white">播报事件</h3>
            </div>

            <div className="space-y-3">
              {(Object.keys(EVENT_LABELS) as VoiceEventType[]).map((event) => (
                <label
                  key={event}
                  className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg cursor-pointer hover:bg-slate-900/70 transition-colors"
                >
                  <span className="text-white">{EVENT_LABELS[event]}</span>
                  <input
                    type="checkbox"
                    checked={settings.events[event]}
                    onChange={(e) => updateEvent(event, e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 text-amber-500 focus:ring-amber-500 focus:ring-offset-0"
                  />
                </label>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <VoiceTestArea
              settings={settings}
              onSpeak={handleSpeak}
              onStop={stop}
              voices={voices}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <CustomVoiceUpload
              customSounds={settings.customSounds}
              onUpload={handleUpload}
              onDelete={handleDelete}
            />
          </motion.div>
        </div>

        {isSaving && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed bottom-4 right-4 px-4 py-2 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium"
          >
            保存中...
          </motion.div>
        )}
      </div>
    </div>
  );
}
