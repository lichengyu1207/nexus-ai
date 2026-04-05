import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../hooks/useWebSocket';
import type { WebSocketMessage } from '../types';

vi.mock('socket.io-client', () => {
  const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    connect: vi.fn(),
    connected: false,
    active: false,
  };

  return {
    io: vi.fn(() => mockSocket),
  };
});

import { io } from 'socket.io-client';

describe('useWebSocket', () => {
  let mockSocket: ReturnType<typeof io>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSocket = io();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should initialize with disconnected state', () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    expect(result.current.isConnected).toBe(false);
    expect(result.current.isReconnecting).toBe(false);
  });

  it('should call io with correct options', () => {
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
        autoReconnect: true,
      })
    );

    expect(io).toHaveBeenCalledWith('ws://test', expect.objectContaining({
      auth: { token: 'test-token' },
      transports: ['websocket', 'polling'],
      reconnection: true,
    }));
  });

  it('should set connected when socket connects', () => {
    const onConnect = vi.fn();
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
        onConnect,
      })
    );

    const connectHandler = mockSocket.on.mock.calls.find(
      (call) => call[0] === 'connect'
    )?.[1];

    act(() => {
      mockSocket.connected = true;
      connectHandler?.();
    });

    expect(onConnect).toHaveBeenCalled();
  });

  it('should handle incoming messages', () => {
    const onMessage = vi.fn();
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
        onMessage,
      })
    );

    const messageHandler = mockSocket.on.mock.calls.find(
      (call) => call[0] === 'message'
    )?.[1];

    const testMessage: WebSocketMessage = {
      id: '1',
      type: 'task.updated',
      payload: { taskId: '123', status: 'completed' },
      timestamp: Date.now(),
    };

    act(() => {
      messageHandler?.(testMessage);
    });

    expect(onMessage).toHaveBeenCalledWith(testMessage);
  });

  it('should send messages when connected', () => {
    mockSocket.connected = true;

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    act(() => {
      result.current.send('task.updated', { taskId: '123' });
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('message', {
      type: 'task.updated',
      payload: { taskId: '123' },
    });
  });

  it('should not send messages when disconnected', () => {
    mockSocket.connected = false;

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    act(() => {
      result.current.send('task.updated', { taskId: '123' });
    });

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });

  it('should subscribe to topics', () => {
    mockSocket.connected = true;

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    act(() => {
      result.current.subscribe('task:123');
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('message', {
      type: 'subscribe',
      payload: { topic: 'task:123' },
    });
  });

  it('should unsubscribe from topics', () => {
    mockSocket.connected = true;

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    act(() => {
      result.current.unsubscribe('task:123');
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('message', {
      type: 'unsubscribe',
      payload: { topic: 'task:123' },
    });
  });

  it('should handle disconnect', () => {
    const onDisconnect = vi.fn();
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
        onDisconnect,
      })
    );

    const disconnectHandler = mockSocket.on.mock.calls.find(
      (call) => call[0] === 'disconnect'
    )?.[1];

    act(() => {
      mockSocket.connected = false;
      disconnectHandler?.('io client disconnect');
    });

    expect(onDisconnect).toHaveBeenCalled();
  });

  it('should handle connection errors', () => {
    const onError = vi.fn();
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
        onError,
      })
    );

    const errorHandler = mockSocket.on.mock.calls.find(
      (call) => call[0] === 'connect_error'
    )?.[1];

    const testError = new Error('Connection failed');

    act(() => {
      errorHandler?.(testError);
    });

    expect(onError).toHaveBeenCalledWith(testError);
  });

  it('should disconnect on unmount', () => {
    const { unmount } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    unmount();

    expect(mockSocket.disconnect).toHaveBeenCalled();
  });

  it('should handle custom message handlers', () => {
    const customHandler = vi.fn();
    renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://test',
        token: 'test-token',
      })
    );

    const cleanup = result.current.onMessage(customHandler);

    const messageHandler = mockSocket.on.mock.calls.find(
      (call) => call[0] === 'message'
    )?.[1];

    const testMessage: WebSocketMessage = {
      id: '1',
      type: 'notification.new',
      payload: { id: 'n1', title: 'Test' },
      timestamp: Date.now(),
    };

    act(() => {
      messageHandler?.(testMessage);
    });

    expect(customHandler).toHaveBeenCalledWith(testMessage);

    cleanup();
  });
});
