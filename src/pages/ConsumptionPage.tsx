import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface ConsumptionRecord {
  id: string;
  action_type: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_integral: number;
  metadata?: Record<string, any>;
  created_at: string;
}

interface ConsumptionHistory {
  records: ConsumptionRecord[];
  total: number;
  limit: number;
  offset: number;
}

const actionTypeLabels: Record<string, string> = {
  'task_create': '创建任务',
  'consult_query': '咨询对话',
  'report_generate': '报告生成',
  'export_pdf': '导出PDF',
  'dialogue': '智能咨询'
};

const actionTypeColors: Record<string, string> = {
  'task_create': 'bg-blue-100 text-blue-700',
  'consult_query': 'bg-green-100 text-green-700',
  'report_generate': 'bg-purple-100 text-purple-700',
  'export_pdf': 'bg-orange-100 text-orange-700',
  'dialogue': 'bg-indigo-100 text-indigo-700'
};

export default function ConsumptionPage() {
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data: balance } = useQuery({
    queryKey: ['tokenBalance'],
    queryFn: async () => {
      const response = await api.get('/token/balance');
      return response.data;
    }
  });

  const { data, isLoading, refetch } = useQuery<ConsumptionHistory>({
    queryKey: ['consumptionHistory', page, selectedAction],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString()
      });
      if (selectedAction) {
        params.append('action_type', selectedAction);
      }
      const response = await api.get(`/token/history?${params.toString()}`);
      return response.data;
    }
  });

  const records = data?.records || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">消费记录</h1>
          <p className="text-gray-500 mt-1">查看您的Token消耗明细</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">当前余额</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {balance?.integral?.toFixed(2) || '0.00'}
                <span className="text-lg font-normal text-gray-500 ml-1">积分</span>
              </p>
              <p className="text-sm text-gray-500 mt-1">
                ≈ {balance?.token_balance?.toLocaleString() || 0} Token
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">兑换比例</p>
              <p className="text-lg font-semibold text-gray-700">1 积分 = 100 Token</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">消费明细</h2>
              <select
                value={selectedAction}
                onChange={(e) => {
                  setSelectedAction(e.target.value);
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">全部类型</option>
                {Object.entries(actionTypeLabels).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-gray-500">
              加载中...
            </div>
          ) : records.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              暂无消费记录
            </div>
          ) : (
            <>
              <div className="divide-y divide-gray-100">
                {records.map((record) => (
                  <div key={record.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          actionTypeColors[record.action_type] || 'bg-gray-100 text-gray-700'
                        }`}>
                          {actionTypeLabels[record.action_type] || record.action_type}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            消耗 {record.total_tokens} Token
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            输入: {record.input_tokens} | 输出: {record.output_tokens}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-red-600">
                          -{record.cost_integral.toFixed(2)} 积分
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatDistanceToNow(new Date(record.created_at), { 
                            addSuffix: true, 
                            locale: zhCN 
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="p-4 border-t border-gray-200 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    共 {total} 条记录
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(Math.max(0, page - 1))}
                      disabled={page === 0}
                      className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      上一页
                    </button>
                    <span className="px-3 py-1.5 text-sm text-gray-600">
                      {page + 1} / {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                      disabled={page >= totalPages - 1}
                      className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">定价规则</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">创建任务</span>
              <span className="text-sm font-medium">固定 5 Token</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">智能咨询</span>
              <span className="text-sm font-medium">输入Token + 输出Token × 0.3</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">报告生成</span>
              <span className="text-sm font-medium">生成内容Token × 0.1</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600">导出PDF</span>
              <span className="text-sm font-medium">固定 2 Token</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
