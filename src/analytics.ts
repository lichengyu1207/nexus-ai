const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID || 'G-XXXXXXXXXX';

const isProduction = import.meta.env.PROD;

declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

export const initGA = () => {
  if (!isProduction || !GA_MEASUREMENT_ID) {
    console.log('[Analytics] Skipped in development mode');
    return;
  }

  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag(...args: any[]) {
    window.dataLayer.push(args);
  };
  window.gtag('js', new Date());
  window.gtag('config', GA_MEASUREMENT_ID, {
    send_page_view: false,
  });

  console.log('[Analytics] Initialized with ID:', GA_MEASUREMENT_ID);
};

export const pageview = (url: string) => {
  if (!isProduction || !window.gtag) {
    console.log('[Analytics] Pageview:', url);
    return;
  }

  window.gtag('config', GA_MEASUREMENT_ID, {
    page_path: url,
  });
};

export const event = (action: string, params?: Record<string, any>) => {
  if (!isProduction || !window.gtag) {
    console.log('[Analytics] Event:', action, params);
    return;
  }

  window.gtag('event', action, params);
};

export const trackAuth = {
  login: (method: string = 'email') => {
    event('login', { method });
  },
  register: (method: string = 'email') => {
    event('sign_up', { method });
  },
  logout: () => {
    event('logout');
  },
};

export const trackTask = {
  create: (taskType: string) => {
    event('create_task', { task_type: taskType });
  },
  view: (taskId: string) => {
    event('view_task', { task_id: taskId });
  },
  complete: (taskId: string) => {
    event('complete_task', { task_id: taskId });
  },
  delete: (taskId: string) => {
    event('delete_task', { task_id: taskId });
  },
};

export const trackReport = {
  generate: (reportType: string) => {
    event('generate_report', { report_type: reportType });
  },
  view: (reportId: string) => {
    event('view_report', { report_id: reportId });
  },
  download: (reportId: string, format: string) => {
    event('download_report', { report_id: reportId, format });
  },
  share: (reportId: string) => {
    event('share_report', { report_id: reportId });
  },
};

export const trackFeedback = {
  submit: (type: string) => {
    event('submit_feedback', { feedback_type: type });
  },
  view: (feedbackId: string) => {
    event('view_feedback', { feedback_id: feedbackId });
  },
};

export const trackReportContent = {
  submit: (contentType: string, reason: string) => {
    event('report_content', { content_type: contentType, reason });
  },
};

export const trackSearch = (query: string, resultsCount: number) => {
  event('search', {
    search_term: query,
    results_count: resultsCount,
  });
};

export const trackError = (errorType: string, errorMessage: string) => {
  event('error', {
    error_type: errorType,
    error_message: errorMessage,
  });
};

export const trackUserEngagement = {
  pageView: (pageName: string) => {
    event('page_view', { page_name: pageName });
  },
  buttonClick: (buttonName: string, location: string) => {
    event('button_click', { button_name: buttonName, location });
  },
  formSubmit: (formName: string, success: boolean) => {
    event('form_submit', { form_name: formName, success });
  },
};

export const trackFeatureUsage = {
  useAIModel: (modelName: string) => {
    event('use_ai_model', { model_name: modelName });
  },
  useVisualization: (chartType: string) => {
    event('use_visualization', { chart_type: chartType });
  },
  useExport: (format: string) => {
    event('use_export', { format });
  },
  useTeamFeature: (featureName: string) => {
    event('use_team_feature', { feature_name: featureName });
  },
};

export default {
  init: initGA,
  pageview,
  event,
  trackAuth,
  trackTask,
  trackReport,
  trackFeedback,
  trackReportContent,
  trackSearch,
  trackError,
  trackUserEngagement,
  trackFeatureUsage,
};
