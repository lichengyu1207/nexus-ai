import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: () => void;
  description?: string;
  preventDefault?: boolean;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
  preventDefault?: boolean;
}

export const useKeyboardShortcuts = (options: UseKeyboardShortcutsOptions): void => {
  const { shortcuts, enabled = true, preventDefault = true } = options;
  const shortcutsRef = useRef(shortcuts);

  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        const isCtrlK = event.key.toLowerCase() === 'k' && (event.ctrlKey || event.metaKey);
        if (!isCtrlK) {
          return;
        }
      }

      for (const shortcut of shortcutsRef.current) {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          if (shortcut.preventDefault ?? preventDefault) {
            event.preventDefault();
          }
          shortcut.action();
          break;
        }
      }
    },
    [enabled, preventDefault]
  );

  useEffect(() => {
    if (enabled) {
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [enabled, handleKeyDown]);
};

export const createShortcuts = (
  config: Array<{
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    action: () => void;
    description?: string;
  }>
): KeyboardShortcut[] => {
  return config.map((item) => ({
    ...item,
    preventDefault: true,
  }));
};

export const defaultGlobalShortcuts = (
  actions: {
    onSearch?: () => void;
    onClose?: () => void;
    onSendMessage?: () => void;
    onNavigateUp?: () => void;
    onNavigateDown?: () => void;
  }
): KeyboardShortcut[] => {
  const shortcuts: KeyboardShortcut[] = [];

  if (actions.onSearch) {
    shortcuts.push({
      key: 'k',
      ctrl: true,
      action: actions.onSearch,
      description: '聚焦搜索/输入框',
    });
  }

  if (actions.onClose) {
    shortcuts.push({
      key: 'Escape',
      action: actions.onClose,
      description: '关闭模态框/侧边栏',
    });
  }

  if (actions.onSendMessage) {
    shortcuts.push({
      key: 'Enter',
      ctrl: true,
      action: actions.onSendMessage,
      description: '发送消息',
    });
  }

  if (actions.onNavigateUp) {
    shortcuts.push({
      key: 'ArrowUp',
      action: actions.onNavigateUp,
      description: '向上导航',
    });
  }

  if (actions.onNavigateDown) {
    shortcuts.push({
      key: 'ArrowDown',
      action: actions.onNavigateDown,
      description: '向下导航',
    });
  }

  return shortcuts;
};

export default useKeyboardShortcuts;
