/**
 * 用户行为分析埋点工具
 */

const SESSION_KEY = 'analytics_session_id';
const DEVICE_KEY = 'analytics_device_id';

const getSessionId = (): string => {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
};

const getDeviceId = (): string => {
  let deviceId = localStorage.getItem(DEVICE_KEY);
  if (!deviceId) {
    deviceId = generateUUID();
    localStorage.setItem(DEVICE_KEY, deviceId);
  }
  return deviceId;
};

const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

const getDeviceInfo = () => {
  return {
    userAgent: navigator.userAgent,
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    language: navigator.language,
    platform: navigator.platform,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
};

export interface TrackEventOptions {
  eventType: string;
  elementId?: string;
  properties?: Record<string, any>;
}

export const trackEvent = async (options: TrackEventOptions): Promise<void> => {
  const { eventType, elementId, properties = {} } = options;

  const eventData = {
    event_type: eventType,
    element_id: elementId,
    properties,
    page_url: window.location.pathname,
    session_id: getSessionId(),
    device_info: getDeviceInfo(),
  };

  try {
    const response = await fetch('/api/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
      keepalive: true,
    });

    if (!response.ok) {
      console.error('Analytics track failed:', response.status);
    }
  } catch (error) {
    console.error('Analytics error:', error);
  }
};

export const trackPageView = (path?: string): void => {
  trackEvent({
    eventType: 'page_view',
    properties: { path: path || window.location.pathname },
  });
};

export const trackButtonClick = (buttonName: string, properties?: Record<string, any>): void => {
  trackEvent({
    eventType: 'button_click',
    elementId: buttonName,
    properties,
  });
};

export const trackTaskCreate = (taskId: string): void => {
  trackEvent({
    eventType: 'task_create',
    properties: { task_id: taskId },
  });
};

export const trackReportView = (reportId: string): void => {
  trackEvent({
    eventType: 'report_view',
    properties: { report_id: reportId },
  });
};

export const trackLogin = (method: string = 'email'): void => {
  trackEvent({
    eventType: 'login',
    properties: { method },
  });
};

export const trackRegister = (method: string = 'email'): void => {
  trackEvent({
    eventType: 'register',
    properties: { method },
  });
};

export const trackLogout = (): void => {
  trackEvent({
    eventType: 'logout',
  });
};

export const trackSearch = (query: string, resultsCount?: number): void => {
  trackEvent({
    eventType: 'search',
    properties: { query, results_count: resultsCount },
  });
};

export const trackExport = (format: string, reportId?: string): void => {
  trackEvent({
    eventType: 'export',
    properties: { format, report_id: reportId },
  });
};

export const trackError = (errorType: string, errorMessage: string): void => {
  trackEvent({
    eventType: 'error',
    properties: { error_type: errorType, error_message: errorMessage },
  });
};

export const initAnalytics = (): void => {
  getSessionId();
  getDeviceId();
  
  console.log('Analytics initialized');
};

export default {
  trackEvent,
  trackPageView,
  trackButtonClick,
  trackTaskCreate,
  trackReportView,
  trackLogin,
  trackRegister,
  trackLogout,
  trackSearch,
  trackExport,
  trackError,
  initAnalytics,
};
