import apiClient from './client';
export const chatApi = {
    sendMessage: async (message, agent) => {
        const response = await apiClient.post('/chat', {
            message,
            agent,
        });
        return response.data;
    },
    getReport: async (reportId) => {
        const response = await apiClient.get(`/report/${reportId}`);
        return response.data;
    },
    getAgents: async () => {
        const response = await apiClient.get('/agents');
        return response.data;
    },
    healthCheck: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    },
};
