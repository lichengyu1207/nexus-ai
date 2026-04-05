import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  MinusIcon,
  UsersIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';

interface UserIntegralInfo {
  id: string;
  email: string;
  full_name: string | null;
  integral: number;
  membership_level: string;
  membership_expires: string | null;
  is_member: boolean;
  created_at: string;
}

interface IntegralLog {
  id: string;
  user_id: string;
  change: number;
  balance_after: number;
  reason: string;
  admin_note: string | null;
  admin_id: string | null;
  created_at: string;
}

interface IntegralSummary {
  total_users: number;
  total_integral: number;
  total_consumed: number;
  total_admin_added: number;
  total_register: number;
}

const AdminIntegralPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState<UserIntegralInfo | null>(null);
  const [adjustAmount, setAdjustAmount] = useState(1);
  const [adjustReason, setAdjustReason] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [userListPage, setUserListPage] = useState(0);
  const pageSize = 10;

  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ['adminUserSearch', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return { users: [] };
      const response = await api.get(`/admin/users/search`, {
        params: { q: searchQuery, limit: 10 },
      });
      return response.data;
    },
    enabled: searchQuery.length > 0,
  });

  const { data: userIntegral, isFetching: isLoadingUser } = useQuery({
    queryKey: ['adminUserIntegral', selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return null;
      const response = await api.get(`/admin/users/${selectedUser.id}/integral`);
      return response.data;
    },
    enabled: !!selectedUser,
  });

  const { data: userLogs } = useQuery({
    queryKey: ['adminUserLogs', selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return { logs: [] };
      const response = await api.get(`/admin/users/${selectedUser.id}/integral/logs`, {
        params: { limit: 20 },
      });
      return response.data;
    },
    enabled: !!selectedUser,
  });

  const { data: summary, isLoading: isLoadingSummary, error: summaryError } = useQuery({
    queryKey: ['integralSummary'],
    queryFn: async () => {
      const response = await api.get<IntegralSummary>('/admin/users/integral/summary');
      return response.data;
    },
  });

  const { data: topUsers, isFetching: isLoadingTopUsers, error: topUsersError } = useQuery({
    queryKey: ['topUsers', userListPage],
    queryFn: async () => {
      const response = await api.get('/admin/users/integral/top', {
        params: { limit: pageSize, offset: userListPage * pageSize },
      });
      return response.data;
    },
  });

  const adjustMutation = useMutation({
    mutationFn: async (data: { user_id: string; change: number; reason: string }) => {
      const response = await api.post('/admin/users/integral/adjust', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUserIntegral'] });
      queryClient.invalidateQueries({ queryKey: ['adminUserLogs'] });
      queryClient.invalidateQueries({ queryKey: ['integralSummary'] });
      queryClient.invalidateQueries({ queryKey: ['topUsers'] });
      setShowConfirm(false);
      setAdjustReason('');
      setAdjustAmount(1);
    },
  });

  const handleAdjust = (isAdd: boolean) => {
    if (!selectedUser || !adjustReason.trim()) return;
    const change = isAdd ? Math.abs(adjustAmount) : -Math.abs(adjustAmount);
    adjustMutation.mutate({
      user_id: selectedUser.id,
      change,
      reason: adjustReason,
    });
  };

  const getReasonLabel = (reason: string): string => {
    const labels: Record<string, string> = {
      register: '注册赠送',
      consume_task: '分析消耗',
      admin_adjust: '管理员调整',
      purchase: '购买充值',
      signin: '签到奖励',
    };
    return labels[reason] || reason;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">积分管理</h1>
        <p className="text-gray-500 mt-1">管理用户积分，查看积分变动记录</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {isLoadingSummary ? (
          <div className="col-span-4 text-center py-4 text-gray-500">加载统计数据...</div>
        ) : summaryError ? (
          <div className="col-span-4 text-center py-4 text-red-500">
            加载统计数据失败: {(summaryError as Error).message}
          </div>
        ) : (
          <>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <UsersIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">总用户数</p>
              <p className="text-xl font-bold text-gray-900">{summary?.total_users ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CurrencyDollarIcon className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">总发放积分</p>
              <p className="text-xl font-bold text-gray-900">{summary?.total_integral ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <ArrowTrendingDownIcon className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">总消耗积分</p>
              <p className="text-xl font-bold text-gray-900">{summary?.total_consumed ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <ArrowTrendingUpIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">管理员充值</p>
              <p className="text-xl font-bold text-gray-900">{summary?.total_admin_added ?? 0}</p>
            </div>
          </div>
        </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 bg-white rounded-xl border border-gray-100 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">搜索用户</h2>
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入邮箱或用户名搜索..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {isSearching && (
            <div className="mt-3 text-center text-gray-500 text-sm">
              搜索中...
            </div>
          )}

          {searchResults?.users?.length > 0 && (
            <div className="mt-3 space-y-2 max-h-[300px] overflow-y-auto">
              {searchResults.users.map((user: UserIntegralInfo) => (
                <button
                  key={user.id}
                  onClick={() => {
                    setSelectedUser(user);
                    setSearchQuery('');
                  }}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedUser?.id === user.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <p className="font-medium text-gray-900">{user.email}</p>
                  <p className="text-sm text-gray-500">
                    积分: {user.integral} | {user.membership_level === 'free' ? '免费版' : '会员'}
                  </p>
                </button>
              ))}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">高积分用户</h3>
            {isLoadingTopUsers ? (
              <div className="text-center py-4 text-gray-500 text-sm">加载中...</div>
            ) : topUsersError ? (
              <div className="text-center py-4 text-red-500 text-sm">
                加载失败: {(topUsersError as Error).message}
              </div>
            ) : !topUsers?.users?.length ? (
              <div className="text-center py-4 text-gray-500 text-sm">暂无数据</div>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {topUsers?.users?.map((user: UserIntegralInfo, index: number) => (
                  <button
                    key={user.id}
                    onClick={() => setSelectedUser(user)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedUser?.id === user.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index < 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {userListPage * pageSize + index + 1}
                        </span>
                        <div>
                          <p className="font-medium text-gray-900 text-sm">{user.email}</p>
                          <p className="text-xs text-gray-500">{user.full_name || '未设置姓名'}</p>
                        </div>
                      </div>
                      <span className="font-bold text-blue-600">{user.integral}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
            {topUsers && topUsers.total > pageSize && (
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
                <button
                  onClick={() => setUserListPage(p => Math.max(0, p - 1))}
                  disabled={userListPage === 0}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                </button>
                <span className="text-sm text-gray-500">
                  {userListPage + 1} / {Math.ceil(topUsers.total / pageSize)}
                </span>
                <button
                  onClick={() => setUserListPage(p => p + 1)}
                  disabled={(userListPage + 1) * pageSize >= topUsers.total}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRightIcon className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="col-span-2 bg-white rounded-xl border border-gray-100 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">积分调整</h2>

          {!selectedUser ? (
            <div className="text-center py-12 text-gray-500">
              <UsersIcon className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p>请先搜索或从左侧列表选择用户</p>
            </div>
          ) : isLoadingUser ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{userIntegral?.email}</p>
                    <p className="text-sm text-gray-500">
                      {userIntegral?.full_name || '未设置姓名'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">
                      {userIntegral?.integral ?? 0}
                    </p>
                    <p className="text-sm text-gray-500">当前积分</p>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                  <span>
                    会员等级: {userIntegral?.membership_level === 'free' ? '免费版' : 
                    userIntegral?.membership_level === 'professional' ? '专业版' : '企业版'}
                  </span>
                  {userIntegral?.is_member && (
                    <span className="text-green-600">
                      有效期至 {userIntegral.membership_expires ? 
                        formatDate(userIntegral.membership_expires) : '永久'}
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    调整数量
                  </label>
                  <input
                    type="number"
                    value={adjustAmount}
                    onChange={(e) => setAdjustAmount(Math.abs(parseInt(e.target.value) || 0))}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    调整原因 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={adjustReason}
                    onChange={(e) => setAdjustReason(e.target.value)}
                    placeholder="例如：用户充值10元"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowConfirm('add')}
                    disabled={!adjustReason.trim() || adjustMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <PlusIcon className="w-5 h-5" />
                    增加积分
                  </button>
                  <button
                    onClick={() => setShowConfirm('subtract')}
                    disabled={!adjustReason.trim() || adjustMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <MinusIcon className="w-5 h-5" />
                    减少积分
                  </button>
                </div>
              </div>

              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">最近变动记录</h3>
                <div className="max-h-[200px] overflow-y-auto space-y-2">
                  {userLogs?.logs?.map((log: IntegralLog) => (
                    <div key={log.id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                      <div>
                        <span className={log.change > 0 ? 'text-green-600' : 'text-red-600'}>
                          {log.change > 0 ? '+' : ''}{log.change}
                        </span>
                        <span className="text-gray-500 ml-2">{getReasonLabel(log.reason)}</span>
                        {log.admin_note && (
                          <span className="text-gray-400 ml-2">({log.admin_note})</span>
                        )}
                      </div>
                      <span className="text-gray-400">
                        {new Date(log.created_at).toLocaleString('zh-CN')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900">确认调整积分</h3>
            <p className="mt-2 text-gray-600">
              确定要为用户 <span className="font-medium">{selectedUser?.email}</span>{' '}
              {showConfirm === 'add' ? '增加' : '减少'}{' '}
              <span className="font-bold text-blue-600">{adjustAmount}</span> 积分吗？
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleAdjust(showConfirm === 'add')}
                disabled={adjustMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {adjustMutation.isPending ? '处理中...' : '确认'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminIntegralPage;
