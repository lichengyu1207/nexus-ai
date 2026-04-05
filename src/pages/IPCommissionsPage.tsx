import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  DollarSign, 
  Download, 
  Loader2,
  TrendingUp
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

interface Commission {
  id: string;
  order_id: string;
  order_type: string;
  order_amount: number;
  commission_rate: number;
  commission_amount: number;
  bonus_amount: number;
  total_amount: number;
  status: string;
  created_at: string;
  settled_at: string;
}

export default function IPCommissionsPage() {
  const [commissions, setCommissions] = useState<Commission[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>('');
  const limit = 20;

  useEffect(() => {
    fetchCommissions();
  }, [page, status]);

  const fetchCommissions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });
      if (status) params.append('status', status);
      
      const response = await axios.get(`/api/ip/commissions?${params}`);
      setCommissions(response.data.commissions);
      setTotal(response.data.total);
    } catch (err) {
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    const headers = ['订单ID', '订单类型', '订单金额', '佣金比例', '佣金金额', '奖励金额', '总金额', '状态', '创建时间'];
    const rows = commissions.map(c => [
      c.order_id,
      c.order_type || '-',
      c.order_amount.toFixed(2),
      `${c.commission_rate}%`,
      c.commission_amount.toFixed(2),
      c.bonus_amount.toFixed(2),
      c.total_amount.toFixed(2),
      c.status === 'settled' ? '已结算' : c.status === 'pending' ? '待结算' : '已取消',
      new Date(c.created_at).toLocaleString(),
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `commissions_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('导出成功');
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      pending: { variant: 'secondary', label: '待结算' },
      settled: { variant: 'default', label: '已结算' },
      cancelled: { variant: 'destructive', label: '已取消' },
    };
    const { variant, label } = config[status] || { variant: 'secondary', label: status };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">收益明细</h1>
          <p className="text-gray-600 mt-1">查看您的佣金收入记录</p>
        </div>
        <Button onClick={exportCSV} disabled={commissions.length === 0}>
          <Download className="h-4 w-4 mr-2" />
          导出CSV
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>佣金记录</CardTitle>
            <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="全部状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
                <SelectItem value="pending">待结算</SelectItem>
                <SelectItem value="settled">已结算</SelectItem>
                <SelectItem value="cancelled">已取消</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : commissions.length === 0 ? (
            <div className="text-center py-12">
              <DollarSign className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">暂无佣金记录</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>订单ID</TableHead>
                  <TableHead>订单类型</TableHead>
                  <TableHead className="text-right">订单金额</TableHead>
                  <TableHead className="text-right">佣金比例</TableHead>
                  <TableHead className="text-right">佣金金额</TableHead>
                  <TableHead className="text-right">奖励金额</TableHead>
                  <TableHead className="text-right">总金额</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {commissions.map((commission) => (
                  <TableRow key={commission.id}>
                    <TableCell className="font-mono text-sm">
                      {commission.order_id?.slice(0, 8)}...
                    </TableCell>
                    <TableCell>{commission.order_type || '-'}</TableCell>
                    <TableCell className="text-right">
                      ¥{commission.order_amount.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      {commission.commission_rate}%
                    </TableCell>
                    <TableCell className="text-right text-green-600">
                      ¥{commission.commission_amount.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {commission.bonus_amount > 0 ? `¥${commission.bonus_amount.toFixed(2)}` : '-'}
                    </TableCell>
                    <TableCell className="text-right font-medium text-green-600">
                      ¥{commission.total_amount.toFixed(2)}
                    </TableCell>
                    <TableCell>{getStatusBadge(commission.status)}</TableCell>
                    <TableCell className="text-gray-500">
                      {new Date(commission.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          <span className="text-gray-500">
            第 {page} / {totalPages} 页
          </span>
          <Button
            variant="outline"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  );
}
