import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { MascotEmotion, MascotPose } from '@/components/mascot/Mascot';

interface MascotState {
  emotion: MascotEmotion;
  pose?: MascotPose;
  message?: string;
  isVisible: boolean;
}

interface MascotPreferences {
  enabled: boolean;
  size: 'sm' | 'md' | 'lg' | 'xl';
  showInAllScenes: boolean;
  position: { x: number; y: number };
}

interface MascotContextType {
  state: MascotState;
  preferences: MascotPreferences;
  setMascotState: (state: Partial<MascotState>) => void;
  setPreferences: (prefs: Partial<MascotPreferences>) => void;
  showMascot: () => void;
  hideMascot: () => void;
  showMessage: (message: string, emotion?: MascotEmotion, pose?: MascotPose) => void;
  clearMessage: () => void;
  resetPosition: () => void;
}

const defaultPreferences: MascotPreferences = {
  enabled: true,
  size: 'lg',
  showInAllScenes: false,
  position: { x: 20, y: 20 },
};

const defaultState: MascotState = {
  emotion: 'default',
  pose: undefined,
  message: undefined,
  isVisible: true,
};

const MascotContext = createContext<MascotContextType | undefined>(undefined);

const PREFERENCES_STORAGE_KEY = 'mascot_preferences';
const POSITION_STORAGE_KEY = 'mascot_position';

export const MascotProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<MascotState>(defaultState);
  const [preferences, setPreferencesState] = useState<MascotPreferences>(() => {
    try {
      const saved = localStorage.getItem(PREFERENCES_STORAGE_KEY);
      if (saved) {
        return { ...defaultPreferences, ...JSON.parse(saved) };
      }
    } catch {
      // ignore
    }
    return defaultPreferences;
  });

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const IDLE_TIMEOUT = 30000; // 30秒无操作回到默认状态

  useEffect(() => {
    try {
      localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
    } catch {
      // ignore
    }
  }, [preferences]);

  const resetIdleTimer = useCallback(() => {
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
    }
    idleTimerRef.current = setTimeout(() => {
      setState(prev => ({
        ...prev,
        emotion: 'default',
        pose: undefined,
        message: undefined,
      }));
    }, IDLE_TIMEOUT);
  }, []);

  useEffect(() => {
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach(event => {
      window.addEventListener(event, resetIdleTimer);
    });
    resetIdleTimer();

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, resetIdleTimer);
      });
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [resetIdleTimer]);

  const setMascotState = useCallback((newState: Partial<MascotState>) => {
    setState(prev => ({ ...prev, ...newState }));
    resetIdleTimer();
  }, [resetIdleTimer]);

  const setPreferences = useCallback((prefs: Partial<MascotPreferences>) => {
    setPreferencesState(prev => ({ ...prev, ...prefs }));
  }, []);

  const showMascot = useCallback(() => {
    setState(prev => ({ ...prev, isVisible: true }));
  }, []);

  const hideMascot = useCallback(() => {
    setState(prev => ({ ...prev, isVisible: false }));
  }, []);

  const showMessage = useCallback((message: string, emotion?: MascotEmotion, pose?: MascotPose) => {
    setState(prev => ({
      ...prev,
      message,
      emotion: emotion || prev.emotion,
      pose: pose || prev.pose,
    }));
    resetIdleTimer();
  }, [resetIdleTimer]);

  const clearMessage = useCallback(() => {
    setState(prev => ({ ...prev, message: undefined }));
  }, []);

  const resetPosition = useCallback(() => {
    setPreferencesState(prev => ({
      ...prev,
      position: { x: 20, y: 20 },
    }));
    try {
      localStorage.removeItem(POSITION_STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return (
    <MascotContext.Provider
      value={{
        state,
        preferences,
        setMascotState,
        setPreferences,
        showMascot,
        hideMascot,
        showMessage,
        clearMessage,
        resetPosition,
      }}
    >
      {children}
    </MascotContext.Provider>
  );
};

export const useMascot = (): MascotContextType => {
  const context = useContext(MascotContext);
  if (!context) {
    throw new Error('useMascot must be used within a MascotProvider');
  }
  return context;
};

export const useMascotScene = () => {
  const { setMascotState, showMessage, clearMessage } = useMascot();

  const setTaskLoading = useCallback(() => {
    setMascotState({
      emotion: 'thinking',
      pose: 'standing',
      message: '正在分析中，请稍候...',
    });
  }, [setMascotState]);

  const setTaskComplete = useCallback(() => {
    setMascotState({
      emotion: 'happy',
      pose: 'waving',
      message: '分析完成！快来看看结果吧～',
    });
    setTimeout(() => {
      clearMessage();
    }, 3000);
  }, [setMascotState, clearMessage]);

  const setTaskError = useCallback((errorMessage?: string) => {
    setMascotState({
      emotion: 'comforting',
      pose: 'sitting',
      message: errorMessage || '出错了，别担心，我们再试一次～',
    });
  }, [setMascotState]);

  const setWelcome = useCallback((username?: string) => {
    setMascotState({
      emotion: 'happy',
      pose: 'waving',
      message: username ? `欢迎回来，${username}！` : '欢迎来到房都督AI！',
    });
    setTimeout(() => {
      clearMessage();
    }, 3000);
  }, [setMascotState, clearMessage]);

  const setIdle = useCallback(() => {
    setMascotState({
      emotion: 'default',
      pose: undefined,
      message: undefined,
    });
  }, [setMascotState]);

  return {
    setTaskLoading,
    setTaskComplete,
    setTaskError,
    setWelcome,
    setIdle,
    showMessage,
    clearMessage,
  };
};

export default MascotContext;
