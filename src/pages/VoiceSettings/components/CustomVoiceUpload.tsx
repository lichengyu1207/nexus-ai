import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  CloudArrowUpIcon, 
  PlayIcon, 
  PauseIcon, 
  TrashIcon,
  MusicalNoteIcon 
} from '@heroicons/react/24/outline';
import type { VoiceEventType, CustomSounds } from '../types';
import { EVENT_LABELS } from '../types';

interface CustomVoiceUploadProps {
  customSounds: CustomSounds;
  onUpload: (type: VoiceEventType, file: File) => Promise<void>;
  onDelete: (type: VoiceEventType) => void;
}

export function CustomVoiceUpload({ customSounds, onUpload, onDelete }: CustomVoiceUploadProps) {
  const [uploadingType, setUploadingType] = useState<VoiceEventType | null>(null);
  const [playingType, setPlayingType] = useState<VoiceEventType | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const eventTypes: VoiceEventType[] = [
    'taskCompleted',
    'taskFailed',
    'taskProgress',
    'newNotification',
    'agentStatusChange',
    'collaborationEvent',
  ];

  const handleFileSelect = async (type: VoiceEventType, file: File) => {
    if (!file) return;
    
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3'];
    if (!validTypes.includes(file.type)) {
      alert('请上传 MP3 或 WAV 格式的音频文件');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert('文件大小不能超过 5MB');
      return;
    }

    setUploadingType(type);
    try {
      await onUpload(type, file);
    } finally {
      setUploadingType(null);
    }
  };

  const handlePlay = (type: VoiceEventType, url: string) => {
    if (playingType === type) {
      audioRef.current?.pause();
      setPlayingType(null);
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    audioRef.current = new Audio(url);
    audioRef.current.onended = () => setPlayingType(null);
    audioRef.current.play();
    setPlayingType(type);
  };

  const handleDelete = (type: VoiceEventType) => {
    if (playingType === type) {
      audioRef.current?.pause();
      setPlayingType(null);
    }
    onDelete(type);
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
      <div className="flex items-center gap-2 mb-4">
        <MusicalNoteIcon className="w-5 h-5 text-amber-400" />
        <h3 className="text-lg font-semibold text-white">自定义配音</h3>
      </div>

      <p className="text-sm text-slate-400 mb-4">
        上传自定义音频文件替换默认提示音（支持 MP3/WAV，最大 5MB）
      </p>

      <div className="space-y-3">
        {eventTypes.map((type) => {
          const hasCustomSound = !!customSounds[type];
          const isUploading = uploadingType === type;
          const isPlaying = playingType === type;

          return (
            <div
              key={type}
              className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700/30"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm text-white">{EVENT_LABELS[type]}</span>
                {hasCustomSound && (
                  <span className="text-xs text-amber-400">已自定义</span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {hasCustomSound && (
                  <>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handlePlay(type, customSounds[type]!)}
                      className="p-2 rounded-lg bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
                    >
                      {isPlaying ? (
                        <PauseIcon className="w-4 h-4" />
                      ) : (
                        <PlayIcon className="w-4 h-4" />
                      )}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleDelete(type)}
                      className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </motion.button>
                  </>
                )}

                <label className="relative cursor-pointer">
                  <input
                    type="file"
                    accept="audio/mpeg,audio/wav,audio/mp3"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileSelect(type, file);
                      e.target.value = '';
                    }}
                    className="sr-only"
                  />
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`
                      flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                      transition-colors
                      ${isUploading
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white'
                      }
                    `}
                  >
                    {isUploading ? (
                      <>
                        <div className="animate-spin w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full" />
                        上传中
                      </>
                    ) : (
                      <>
                        <CloudArrowUpIcon className="w-3.5 h-3.5" />
                        {hasCustomSound ? '替换' : '上传'}
                      </>
                    )}
                  </motion.div>
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
