import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { Coins, ArrowUpCircle, ArrowDownCircle, Download, Gift, Calendar } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';
import SigninModal from '@/components/SigninModal';

interface IntegralLog {
  id: string;
  change: number;
  balance_after: number;
  token_change: number;
  token_balance_after: number;
  reason: string;
  action_type: string | null;
  resource_id: string | null;
  resource_type: string | null;
  created_at: string;
}

interface BalanceData {
  integral: number;
  tokens: number;
  today_earned: number;
  today_consumed: number;
  total_earned: number;
  total_consumed: number;
}

interface LogsResponse {
  logs: IntegralLog[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface ActionType {
  value: string;
  label: string;
}

const ACTION_TYPE_LABELS: Record<string, string> = {
  signin: '签到奖励',
  makeup_signin: '补签奖励',
  task_create: '任务消耗',
  task_reward: '任务奖励',
  recharge: '充值',
  admin_add: '管理员增加',
  admin_deduct: '管理员扣除',
  consult: '咨询消耗',
  export: '导出消耗',
  reward: '系统奖励',
};

export default function IntegralPage() {
  const [balance, setBalance] = useState<BalanceData | null>(null);
  const [logs, setLogs] = useState<IntegralLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [actionTypes, setActionTypes] = useState<ActionType[]>([]);
  
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedActionType, setSelectedActionType] = useState('');
  
  const [signinModalOpen, setSigninModalOpen] = useState(false);

  useEffect(() => {
    fetchBalance();
    fetchActionTypes();
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [page, startDate, endDate, selectedActionType]);

  const fetchBalance = async () => {
    try {
      const response = await api.get('/user/integral/balance');
      setBalance(response.data);
    } catch (error) {
      console.error('Failed to fetch balance:', error);
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('limit', '20');
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (selectedActionType) params.append('action_type', selectedActionType);

      const response = await api.get(`/user/integral/logs?${params.toString()}`);
      setLogs(response.data.logs);
      setTotal(response.data.total);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActionTypes = async () => {
    try {
      const response = await api.get('/user/integral/action-types');
      setActionTypes(response.data.types);
    } catch (error) {
      console.error('Failed to fetch action types:', error);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (selectedActionType) params.append('action_type', selectedActionType);

      const response = await api.get(`/user/integral/logs/export?${params.toString()}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `integral_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('导出成功');
    } catch (error) {
      toast.error('导出失败');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSigninSuccess = () => {
    fetchBalance();
    fetchLogs();
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">积分中心</h1>
        <Button onClick={() => setSigninModalOpen(true)} className="text-base px-6 py-3">
          <Gift className="mr-2 h-5 w-5" />
          每日签到
        </Button>
      </div>

      {/* 积分余额卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-gray-700">
              当前积分
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Coins className="h-10 w-10 text-blue-600" />
              <div>
                <div className="text-4xl font-bold text-gray-900">{balance?.integral.toFixed(2) || '0.00'}</div>
                <div className="text-base text-gray-600 mt-1">
                  ≈ {balance?.tokens.toLocaleString() || 0} Token
                </div>
              </div>
            </div>
            <div className="mt-3 text-sm text-gray-500">
              1 积分 = 100 Token
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-gray-700">
              今日变动
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ArrowUpCircle className="h-6 w-6 text-green-500" />
                <span className="text-xl font-bold text-green-600">
                  +{balance?.today_earned.toFixed(2) || '0.00'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <ArrowDownCircle className="h-6 w-6 text-red-500" />
                <span className="text-xl font-bold text-red-600">
                  -{balance?.today_consumed.toFixed(2) || '0.00'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-2 border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-gray-700">
              累计统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500">总收入</div>
                <div className="text-xl font-bold text-green-600">
                  +{balance?.total_earned.toFixed(2) || '0.00'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">总支出</div>
                <div className="text-xl font-bold text-red-600">
                  -{balance?.total_consumed.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选栏 */}
      <Card className="border-2 border-gray-200">
        <CardContent className="py-5">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
              <Label className="text-base font-medium">开始日期</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-44 text-base"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-base font-medium">结束日期</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-44 text-base"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-base font-medium">操作类型</Label>
              <Select value={selectedActionType} onValueChange={setSelectedActionType}>
                <SelectTrigger className="w-44 text-base">
                  <SelectValue placeholder="全部类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">全部类型</SelectItem>
                  {actionTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" className="text-base px-5 py-2" onClick={() => { setStartDate(''); setEndDate(''); setSelectedActionType(''); }}>
              重置
            </Button>
            <Button variant="outline" className="text-base px-5 py-2" onClick={handleExport}>
              <Download className="mr-2 h-5 w-5" />
              导出CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 积分明细表格 */}
      <Card className="border-2 border-gray-200">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-gray-900">积分明细</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-lg">
              暂无积分记录
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="text-base font-semibold text-gray-700">时间</TableHead>
                    <TableHead className="text-base font-semibold text-gray-700">操作类型</TableHead>
                    <TableHead className="text-base font-semibold text-gray-700">原因</TableHead>
                    <TableHead className="text-base font-semibold text-gray-700 text-right">积分变动</TableHead>
                    <TableHead className="text-base font-semibold text-gray-700 text-right">Token变动</TableHead>
                    <TableHead className="text-base font-semibold text-gray-700 text-right">变动后余额</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id} className="hover:bg-gray-50">
                      <TableCell className="text-base text-gray-700">
                        {formatDate(log.created_at)}
                      </TableCell>
                      <TableCell>
                        {log.action_type ? (
                          <Badge variant="outline" className="text-base px-3 py-1">
                            {ACTION_TYPE_LABELS[log.action_type] || log.action_type}
                          </Badge>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-base text-gray-700 max-w-xs truncate">
                        {log.reason}
                      </TableCell>
                      <TableCell className={`text-right text-lg font-bold ${log.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {log.change >= 0 ? '+' : ''}{log.change.toFixed(2)}
                      </TableCell>
                      <TableCell className={`text-right text-lg font-bold ${log.token_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {log.token_change >= 0 ? '+' : ''}{log.token_change}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="text-base font-medium text-gray-900">{log.balance_after.toFixed(2)} 积分</div>
                        <div className="text-sm text-gray-500">
                          {log.token_balance_after} Token
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* 分页 */}
              {totalPages > 1 && (
                <div className="mt-4 flex justify-center">
                  <Pagination>
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious
                          onClick={() => setPage(Math.max(1, page - 1))}
                          className={page === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                        />
                      </PaginationItem>
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const pageNum = Math.max(1, Math.min(page - 2 + i, totalPages - 4 + i));
                        return (
                          <PaginationItem key={pageNum}>
                            <PaginationLink
                              onClick={() => setPage(pageNum)}
                              isActive={page === pageNum}
                              className="cursor-pointer"
                            >
                              {pageNum}
                            </PaginationLink>
                          </PaginationItem>
                        );
                      })}
                      <PaginationItem>
                        <PaginationNext
                          onClick={() => setPage(Math.min(totalPages, page + 1))}
                          className={page === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                </div>
              )}

              <div className="mt-4 text-center text-sm text-muted-foreground">
                共 {total} 条记录
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* 签到弹窗 */}
      <SigninModal
        open={signinModalOpen}
        onOpenChange={setSigninModalOpen}
        onSigninSuccess={handleSigninSuccess}
      />
    </div>
  );
}
