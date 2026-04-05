import api from './api';

export interface PreviewResult {
  query: string;
  location: {
    city: string | null;
    district: string | null;
    community: string | null;
  };
  market_overview: {
    avg_price: number;
    price_trend: string;
    year_change: number;
    transaction_volume: string;
  } | null;
  price_range: {
    min: number;
    max: number;
    median: number;
  } | null;
  key_highlights: string[];
  sample_report_sections: string[];
  registration_incentive: {
    title: string;
    benefits: string[];
    cta_text: string;
  };
}

export const previewApi = {
  createPreview: async (query: string): Promise<PreviewResult> => {
    const response = await api.post('/preview/', { query });
    return response.data;
  },
};
