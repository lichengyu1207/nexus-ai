import api from '@/services/api';

export interface Location {
  id: string;
  user_id: string;
  source: string;
  address: string;
  country: string | null;
  province: string | null;
  city: string | null;
  district: string | null;
  street: string | null;
  community: string | null;
  longitude: number | null;
  latitude: number | null;
  geocoded_at: string | null;
  created_at: string | null;
  user_email: string | null;
}

export interface LocationListResponse {
  locations: Location[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LocationStats {
  total: number;
  geocoded: number;
  not_geocoded: number;
  by_source: Record<string, number>;
  by_province: Array<{ province: string; count: number }>;
}

export interface LocationUpdate {
  address?: string;
  country?: string;
  province?: string;
  city?: string;
  district?: string;
  street?: string;
  community?: string;
  longitude?: number;
  latitude?: number;
}

export const adminLocationsApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    user_id?: string;
    source?: string;
    is_geocoded?: boolean;
    province?: string;
    city?: string;
    search?: string;
  }): Promise<LocationListResponse> => {
    const response = await api.get('/admin/locations', { params });
    return response.data;
  },

  getStats: async (): Promise<LocationStats> => {
    const response = await api.get('/admin/locations/stats');
    return response.data;
  },

  get: async (locationId: string): Promise<Location> => {
    const response = await api.get(`/admin/locations/${locationId}`);
    return response.data;
  },

  update: async (locationId: string, data: LocationUpdate): Promise<{ message: string; location_id: string }> => {
    const response = await api.put(`/admin/locations/${locationId}`, data);
    return response.data;
  },

  geocode: async (locationId: string): Promise<{ message: string; location_id: string; result: any }> => {
    const response = await api.post(`/admin/locations/${locationId}/geocode`);
    return response.data;
  },

  delete: async (locationId: string): Promise<{ message: string; location_id: string }> => {
    const response = await api.delete(`/admin/locations/${locationId}`);
    return response.data;
  },

  batchGeocode: async (): Promise<{
    message: string;
    success_count: number;
    fail_count: number;
    total_processed: number;
  }> => {
    const response = await api.post('/admin/locations/batch-geocode');
    return response.data;
  },
};
