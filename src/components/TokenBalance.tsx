import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

interface TokenBalance {
  integral: number;
  token_balance: number;
}

interface TokenPreview {
  input_tokens: number;
  estimated_total_tokens: number;
  estimated_cost_integral: number;
  action_type: string;
  pricing_type: string;
}

interface TokenBalanceDisplayProps {
  showTokens?: boolean;
  className?: string;
}

export const TokenBalanceDisplay: React.FC<TokenBalanceDisplayProps> = ({
  showTokens = true,
  className = ''
}) => {
  const { data: balance, isLoading } = useQuery<TokenBalance>({
    queryKey: ['token-balance'],
    queryFn: async () => {
      const response = await api.get('/token/balance');
      return response.data;
    },
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="flex items-center gap-1.5">
        <svg
          className="w-4 h-4 text-yellow-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.736 6.979C9.208 6.193 9.696 6 10 6c.304 0 .792.193 1.264.979a1 1 0 001.715-1.029C12.279 4.784 11.232 4 10 4s-2.279.784-2.979 1.95c-.285.475-.507 1-.67 1.55H6a1 1 0 000 2h.013a9.358 9.358 0 000 1H6a1 1 0 100 2h.351c.163.55.385 1.075.67 1.55C7.721 15.216 8.768 16 10 16s2.279-.784 2.979-1.95a1 1 0 10-1.715-1.029c-.472.786-.96.979-1.264.979-.304 0-.792-.193-1.264-.979a4.265 4.265 0 01-.264-.521H10a1 1 0 100-2H8.017a7.36 7.36 0 010-1H10a1 1 0 100-2H8.472a4.265 4.265 0 01.264-.521z" />
        </svg>
        <span className="font-medium text-gray-700">
          {balance?.integral?.toFixed(2) || '0.00'}
        </span>
        <span className="text-xs text-gray-500">积分</span>
      </div>
      
      {showTokens && (
        <div className="flex items-center gap-1.5 text-gray-500">
          <span className="text-xs">≈</span>
          <span className="text-sm">{balance?.token_balance?.toLocaleString() || 0}</span>
          <span className="text-xs">Token</span>
        </div>
      )}
    </div>
  );
};

export const TokenPreviewDisplay: React.FC<{
  text: string;
  actionType?: string;
  className?: string;
}> = ({ text, actionType = 'dialogue', className = '' }) => {
  const [preview, setPreview] = useState<TokenPreview | null>(null);

  const previewMutation = useMutation({
    mutationFn: async (data: { text: string; action_type: string }) => {
      const response = await api.post('/token/preview', data);
      return response.data;
    },
    onSuccess: (data) => {
      setPreview(data);
    },
  });

  useEffect(() => {
    if (!text) {
      setPreview(null);
      return;
    }

    const timer = setTimeout(() => {
      previewMutation.mutate({ text, action_type: actionType });
    }, 500);

    return () => clearTimeout(timer);
  }, [text, actionType]);

  if (!text || !preview) {
    return null;
  }

  return (
    <div className={`text-xs text-gray-500 flex items-center gap-2 ${className}`}>
      <span>预计消耗:</span>
      <span className="font-medium text-orange-500">
        {preview.estimated_cost_integral.toFixed(2)} 积分
      </span>
      <span className="text-gray-400">
        (约 {preview.estimated_total_tokens} token)
      </span>
      {preview.pricing_type === 'fixed' && (
        <span className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">
          固定消耗
        </span>
      )}
    </div>
  );
};

export const useTokenConsumption = () => {
  const queryClient = useQueryClient();

  const consumeMutation = useMutation({
    mutationFn: async (data: {
      action_type: string;
      input_text?: string;
      output_text?: string;
      metadata?: Record<string, unknown>;
    }) => {
      const response = await api.post('/token/consume', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['token-balance'] });
    },
  });

  return {
    consume: consumeMutation.mutateAsync,
    isConsuming: consumeMutation.isPending,
    error: consumeMutation.error,
  };
};

export default TokenBalanceDisplay;
