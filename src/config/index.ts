const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws`;
const FILE_BASE_URL = import.meta.env.VITE_FILE_URL || '/api';

interface Config {
  apiBaseUrl: string;
  wsBaseUrl: string;
  fileBaseUrl: string;
  environment: 'development' | 'production' | 'test';
  isProduction: boolean;
  isDevelopment: boolean;
  features: {
    enableWebSocket: boolean;
    enableAnalytics: boolean;
    enableDebugPanel: boolean;
  };
  timeouts: {
    apiTimeout: number;
    wsReconnectInterval: number;
    wsMaxReconnectAttempts: number;
    taskPollingInterval: number;
  };
}

const config: Config = {
  apiBaseUrl: API_BASE_URL,
  wsBaseUrl: WS_BASE_URL,
  fileBaseUrl: FILE_BASE_URL,
  environment: (import.meta.env.MODE as Config['environment']) || 'development',
  isProduction: import.meta.env.PROD === 'true',
  isDevelopment: import.meta.env.DEV === 'true',
  features: {
    enableWebSocket: import.meta.env.VITE_ENABLE_WS !== 'false',
    enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    enableDebugPanel: import.meta.env.VITE_ENABLE_DEBUG === 'true',
  },
  timeouts: {
    apiTimeout: 30000,
    wsReconnectInterval: 2000,
    wsMaxReconnectAttempts: 5,
    taskPollingInterval: 2000,
  },
};

export function getApiUrl(path: string): string {
  return `${config.apiBaseUrl}${path}`;
}

export function getWsUrl(path: string): string {
  return `${config.wsBaseUrl}${path}`;
}

export function getFileUrl(path: string): string {
  return `${config.fileBaseUrl}${path}`;
}

export default config;
