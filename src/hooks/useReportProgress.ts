import { useState, useEffect, useCallback, useRef } from 'react';

export interface TimelineHighlight {
  task_id: string;
  report_id: string;
  agent_name: string;
  step_name: string;
  section: string;
  status: 'started' | 'completed';
  description: string | null;
  content: unknown;
  timestamp: string;
}

export interface ReportProgressState {
  isGenerating: boolean;
  currentSection: string | null;
  currentAgent: string | null;
  highlights: Map<string, TimelineHighlight>;
  lastHighlight: TimelineHighlight | null;
}

interface UseReportProgressOptions {
  taskId: string | undefined;
  onHighlight?: (highlight: TimelineHighlight) => void;
  onSectionStart?: (section: string, agent: string) => void;
  onSectionComplete?: (section: string, agent: string, content: unknown) => void;
}

interface UseReportProgressReturn {
  isGenerating: boolean;
  currentSection: string | null;
  currentAgent: string | null;
  highlights: Map<string, TimelineHighlight>;
  lastHighlight: TimelineHighlight | null;
  clearHighlights: () => void;
  isAgentHighlighted: (agentName: string) => boolean;
  getAgentHighlight: (agentName: string) => TimelineHighlight | null;
  getSectionHighlight: (section: string) => TimelineHighlight | null;
}

const useReportProgress = (options: UseReportProgressOptions): UseReportProgressReturn => {
  const { taskId, onHighlight, onSectionStart, onSectionComplete } = options;

  const [state, setState] = useState<ReportProgressState>({
    isGenerating: false,
    currentSection: null,
    currentAgent: null,
    highlights: new Map(),
    lastHighlight: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const handleTimelineHighlight = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as TimelineHighlight;

        setState((prev) => {
          const newHighlights = new Map(prev.highlights);
          const key = `${data.agent_name}_${data.section}`;
          newHighlights.set(key, data);

          return {
            ...prev,
            isGenerating: data.status === 'started',
            currentSection: data.status === 'started' ? data.section : prev.currentSection,
            currentAgent: data.status === 'started' ? data.agent_name : prev.currentAgent,
            highlights: newHighlights,
            lastHighlight: data,
          };
        });

        if (onHighlight) {
          onHighlight(data);
        }

        if (data.status === 'started' && onSectionStart) {
          onSectionStart(data.section, data.agent_name);
        }

        if (data.status === 'completed' && onSectionComplete) {
          onSectionComplete(data.section, data.agent_name, data.content);
        }
      } catch (error) {
        console.error('Failed to parse timeline_highlight event:', error);
      }
    },
    [onHighlight, onSectionStart, onSectionComplete]
  );

  const handleReportComplete = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isGenerating: false,
      currentSection: null,
      currentAgent: null,
    }));
  }, []);

  const handleReportError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isGenerating: false,
    }));
  }, []);

  useEffect(() => {
    if (!taskId) return;

    const connectSSE = () => {
      const token = localStorage.getItem('token');
      const url = new URL(`/api/tasks/${taskId}/stream`, window.location.origin);
      if (token) {
        url.searchParams.set('token', token);
      }
      const eventSource = new EventSource(url.toString());

      eventSource.addEventListener('timeline_highlight', handleTimelineHighlight);
      eventSource.addEventListener('report_complete', handleReportComplete);
      eventSource.addEventListener('report_error', handleReportError);

      eventSource.onerror = (error) => {
        console.error('SSE error in useReportProgress:', error);
      };

      eventSourceRef.current = eventSource;
    };

    connectSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.removeEventListener('timeline_highlight', handleTimelineHighlight);
        eventSourceRef.current.removeEventListener('report_complete', handleReportComplete);
        eventSourceRef.current.removeEventListener('report_error', handleReportError);
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [taskId, handleTimelineHighlight, handleReportComplete, handleReportError]);

  const clearHighlights = useCallback(() => {
    setState((prev) => ({
      ...prev,
      highlights: new Map(),
      lastHighlight: null,
    }));
  }, []);

  const isAgentHighlighted = useCallback(
    (agentName: string): boolean => {
      for (const highlight of state.highlights.values()) {
        if (highlight.agent_name === agentName && highlight.status === 'started') {
          return true;
        }
      }
      return false;
    },
    [state.highlights]
  );

  const getAgentHighlight = useCallback(
    (agentName: string): TimelineHighlight | null => {
      for (const highlight of state.highlights.values()) {
        if (highlight.agent_name === agentName) {
          return highlight;
        }
      }
      return null;
    },
    [state.highlights]
  );

  const getSectionHighlight = useCallback(
    (section: string): TimelineHighlight | null => {
      return state.highlights.get(`analyst_${section}`) || null;
    },
    [state.highlights]
  );

  return {
    isGenerating: state.isGenerating,
    currentSection: state.currentSection,
    currentAgent: state.currentAgent,
    highlights: state.highlights,
    lastHighlight: state.lastHighlight,
    clearHighlights,
    isAgentHighlighted,
    getAgentHighlight,
    getSectionHighlight,
  };
};

export default useReportProgress;
