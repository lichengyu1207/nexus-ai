import { onLCP, onFID, onCLS, onFCP, onTTFB, Metric } from 'web-vitals';

const VITALS_ENDPOINT = '/api/performance/vitals';
const BATCH_SIZE = 5;
const FLUSH_INTERVAL = 10000;

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: string;
  timestamp: number;
  url: string;
  userAgent: string;
  connectionType?: string;
  memoryUsage?: number;
}

interface VitalsBatch {
  metrics: PerformanceMetric[];
  sessionId: string;
  userId?: string;
  pageLoadTime: number;
}

let metricsQueue: PerformanceMetric[] = [];
let sessionId: string;
let userId: string | undefined;
let flushTimer: ReturnType<typeof setInterval> | null = null;

function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
}

function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const thresholds: Record<string, [number, number]> = {
    LCP: [2500, 4000],
    FID: [100, 300],
    CLS: [0.1, 0.25],
    FCP: [1800, 3000],
    TTFB: [800, 1800],
  };

  const [good, poor] = thresholds[name] || [0, Infinity];
  
  if (value <= good) return 'good';
  if (value <= poor) return 'needs-improvement';
  return 'poor';
}

function getConnectionType(): string | undefined {
  const nav = navigator as Navigator & { connection?: { effectiveType?: string } };
  return nav.connection?.effectiveType;
}

function getMemoryUsage(): number | undefined {
  const perf = performance as Performance & { memory?: { usedJSHeapSize: number } };
  return perf.memory?.usedJSHeapSize;
}

async function sendMetrics(batch: VitalsBatch): Promise<void> {
  try {
    const response = await fetch(VITALS_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch),
      keepalive: true,
    });

    if (!response.ok) {
      console.warn('[Performance] Failed to send metrics:', response.status);
    }
  } catch (error) {
    console.warn('[Performance] Error sending metrics:', error);
  }
}

function flushQueue(): void {
  if (metricsQueue.length === 0) return;

  const batch: VitalsBatch = {
    metrics: [...metricsQueue],
    sessionId,
    userId,
    pageLoadTime: performance.now(),
  };

  metricsQueue = [];
  sendMetrics(batch);
}

function handleMetric(metric: Metric): void {
  const performanceMetric: PerformanceMetric = {
    name: metric.name,
    value: metric.value,
    rating: metric.rating as 'good' | 'needs-improvement' | 'poor',
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    timestamp: Date.now(),
    url: window.location.href,
    userAgent: navigator.userAgent,
    connectionType: getConnectionType(),
    memoryUsage: getMemoryUsage(),
  };

  metricsQueue.push(performanceMetric);

  if (metricsQueue.length >= BATCH_SIZE) {
    flushQueue();
  }
}

export function initPerformanceMonitoring(options?: { userId?: string }): void {
  if (typeof window === 'undefined') return;

  sessionId = generateSessionId();
  userId = options?.userId;

  try {
    onLCP(handleMetric);
    onFID(handleMetric);
    onCLS(handleMetric);
    onFCP(handleMetric);
    onTTFB(handleMetric);
  } catch (e) {
    console.warn('[Performance] Failed to initialize metrics:', e);
  }

  flushTimer = setInterval(flushQueue, FLUSH_INTERVAL);

  window.addEventListener('pagehide', () => {
    flushQueue();
    if (flushTimer) {
      clearInterval(flushTimer);
    }
  });

  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      flushQueue();
    }
  });

  console.log('[Performance] Monitoring initialized');
}

export function setPerformanceUserId(id: string): void {
  userId = id;
}

export function getPerformanceSummary(): {
  lcp: number | null;
  fid: number | null;
  cls: number | null;
  fcp: number | null;
  ttfb: number | null;
} {
  const getMetric = (name: string): number | null => {
    const entries = performance.getEntriesByName(name);
    if (entries.length === 0) return null;
    return (entries[entries.length - 1] as PerformanceEntry & { value?: number }).value ?? null;
  };

  return {
    lcp: getMetric('largest-contentful-paint'),
    fid: getMetric('first-input-delay'),
    cls: getMetric('cumulative-layout-shift'),
    fcp: getMetric('first-contentful-paint'),
    ttfb: getMetric('time-to-first-byte'),
  };
}

export function measureCustomMetric(name: string, startTime: number, endTime?: number): void {
  const duration = (endTime || performance.now()) - startTime;
  
  metricsQueue.push({
    name: `CUSTOM_${name}`,
    value: duration,
    rating: duration < 100 ? 'good' : duration < 500 ? 'needs-improvement' : 'poor',
    delta: duration,
    id: `custom-${name}-${Date.now()}`,
    navigationType: 'navigate',
    timestamp: Date.now(),
    url: window.location.href,
    userAgent: navigator.userAgent,
  });
}

export function startMeasure(name: string): () => void {
  const startTime = performance.now();
  return () => measureCustomMetric(name, startTime);
}

export default {
  init: initPerformanceMonitoring,
  setUserId: setPerformanceUserId,
  getSummary: getPerformanceSummary,
  measureCustom: measureCustomMetric,
  startMeasure,
};
