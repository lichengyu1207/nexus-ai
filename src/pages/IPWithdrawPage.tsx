import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
  Wallet, 
  Plus, 
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

interface Withdrawal {
  id: string;
  amount: number;
  fee: number;
  actual_amount: number;
  account_type: string;
  account_name: string;
  status: string;
  admin_notes: string;
  created_at: string;
  processed_at: string;
}

export default function IPWithdrawPage() {
  const [balance, setBalance] = useState(0);
  const [withdrawals, setWithdrawals] = useState<Withdrawal[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    account_type: 'wechat',
    account_name: '',
    account_info: '',
  });

  const minWithdraw = 10;
  const feeRate = 0.01;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [profileRes, withdrawalsRes] = await Promise.all([
        axios.get('/api/ip/profile'),
        axios.get('/api/ip/withdrawals'),
      ]);
      setBalance(profileRes.data.balance);
      setWithdrawals(withdrawalsRes.data.withdrawals);
    } catch (err) {
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    const amount = parseFloat(formData.amount);
    
    if (isNaN(amount) || amount < minWithdraw) {
      toast.error(`最低提现金额为 ¥${minWithdraw}`);
      return;
    }
    
    if (amount > balance) {
      toast.error('余额不足');
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post('/api/ip/withdraw', {
        amount,
        account_type: formData.account_type,
        account_name: formData.account_name,
        account_info: formData.account_info,
      });
      
      if (response.data.success) {
        toast.success('提现申请已提交');
        setDialogOpen(false);
        setFormData({
          amount: '',
          account_type: 'wechat',
          account_name: '',
          account_info: '',
        });
        fetchData();
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '提现申请失败');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', label: string, icon: any }> = {
      pending: { variant: 'secondary', label: '待审核', icon: Clock },
      approved: { variant: 'default', label: '已通过', icon: CheckCircle },
      rejected: { variant: 'destructive', label: '已拒绝', icon: XCircle },
      completed: { variant: 'default', label: '已完成', icon: CheckCircle },
    };
    
    const { variant, label, icon: Icon } = config[status] || { variant: 'secondary', label: status, icon: Clock };
    return (
      <Badge variant={variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {label}
      </Badge>
    );
  };

  const getAccountTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      wechat: '微信',
      alipay: '支付宝',
      bank: '银行卡',
    };
    return types[type] || type;
  };

  const calculateFee = () => {
    const amount = parseFloat(formData.amount) || 0;
    return (amount * feeRate).toFixed(2);
  };

  const calculateActual = () => {
    const amount = parseFloat(formData.amount) || 0;
    return (amount * (1 - feeRate)).toFixed(2);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">提现管理</h1>
          <p className="text-gray-600 mt-1">申请提现您的推广收益</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">可提现余额</p>
                <p className="text-3xl font-bold text-green-600 mt-1">¥{balance.toFixed(2)}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Wallet className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">最低提现</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">¥{minWithdraw}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">手续费率</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{(feeRate * 100).toFixed(0)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>申请提现</CardTitle>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button disabled={balance < minWithdraw}>
                  <Plus className="h-4 w-4 mr-2" />
                  申请提现
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>申请提现</DialogTitle>
                  <DialogDescription>
                    填写提现金额和收款账户信息
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      可提现余额: ¥{balance.toFixed(2)}，最低提现 ¥{minWithdraw}
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-2">
                    <Label>提现金额</Label>
                    <Input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      placeholder={`最低 ¥${minWithdraw}`}
                      min={minWithdraw}
                      max={balance}
                      step="0.01"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">手续费</p>
                      <p className="font-medium">¥{calculateFee()}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <p className="text-gray-500">实际到账</p>
                      <p className="font-medium text-green-600">¥{calculateActual()}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>收款方式</Label>
                    <Select
                      value={formData.account_type}
                      onValueChange={(value) => setFormData({ ...formData, account_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="wechat">微信</SelectItem>
                        <SelectItem value="alipay">支付宝</SelectItem>
                        <SelectItem value="bank">银行卡</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>收款人姓名</Label>
                    <Input
                      value={formData.account_name}
                      onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                      placeholder="请输入真实姓名"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>
                      {formData.account_type === 'wechat' ? '微信号' : 
                       formData.account_type === 'alipay' ? '支付宝账号' : '银行卡号'}
                    </Label>
                    <Input
                      value={formData.account_info}
                      onChange={(e) => setFormData({ ...formData, account_info: e.target.value })}
                      placeholder={
                        formData.account_type === 'wechat' ? '请输入微信号' :
                        formData.account_type === 'alipay' ? '请输入支付宝账号' : '请输入银行卡号'
                      }
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleSubmit} disabled={submitting}>
                    {submitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        提交中...
                      </>
                    ) : (
                      '提交申请'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>提现记录</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {withdrawals.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">暂无提现记录</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>申请金额</TableHead>
                  <TableHead>手续费</TableHead>
                  <TableHead>实际到账</TableHead>
                  <TableHead>收款方式</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>申请时间</TableHead>
                  <TableHead>备注</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {withdrawals.map((withdrawal) => (
                  <TableRow key={withdrawal.id}>
                    <TableCell className="font-medium">
                      ¥{withdrawal.amount.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-gray-500">
                      ¥{withdrawal.fee.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-green-600 font-medium">
                      ¥{withdrawal.actual_amount.toFixed(2)}
                    </TableCell>
                    <TableCell>
                      {getAccountTypeLabel(withdrawal.account_type)}
                    </TableCell>
                    <TableCell>{getStatusBadge(withdrawal.status)}</TableCell>
                    <TableCell className="text-gray-500">
                      {new Date(withdrawal.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {withdrawal.admin_notes || '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
