import api from './api';

export interface SEOLandingData {
  query: string;
  location: {
    city: string | null;
    district: string | null;
    community: string | null;
    intent: string | null;
  };
  page_title: string;
  page_description: string;
  market_data: {
    avg_price: number;
    price_trend: string;
    year_change: number;
    transaction_volume: string;
    liquidity: string;
    highlights: string[];
  };
  price_chart_data: Array<{
    month: string;
    price: number;
    volume: number;
  }>;
  key_metrics: {
    avg_price_per_sqm: number;
    total_listings: number;
    avg_days_on_market: number;
    price_range: {
      min: number;
      max: number;
    };
  };
  mascot_message: string;
  registration_cta: {
    title: string;
    subtitle: string;
    button_text: string;
  };
}

export const seoApi = {
  getLandingData: async (query: string): Promise<SEOLandingData> => {
    const response = await api.get('/seo/landing', { params: { q: query } });
    return response.data;
  },
};
