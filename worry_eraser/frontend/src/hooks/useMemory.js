import { useState, useCallback } from 'react';
import { chatApi } from '../api';
export const useMemory = () => {
    const [report, setReport] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const fetchReport = useCallback(async (reportId) => {
        setIsLoading(true);
        try {
            const data = await chatApi.getReport(reportId);
            setReport(data);
            return data;
        }
        catch (error) {
            console.error('Failed to fetch report:', error);
            throw error;
        }
        finally {
            setIsLoading(false);
        }
    }, []);
    const clearReport = useCallback(() => {
        setReport(null);
    }, []);
    return {
        report,
        isLoading,
        fetchReport,
        clearReport,
    };
};
