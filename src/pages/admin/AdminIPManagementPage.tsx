import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Users, 
  DollarSign, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  Search
} from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

export default function AdminIPManagementPage() {
  const [activeTab, setActiveTab] = useState('applications');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>({});
  const [applications, setApplications] = useState<any[]>([]);
  const [ips, setIPs] = useState<any[]>([]);
  const [withdrawals, setWithdrawals] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [selectedApplication, setSelectedApplication] = useState<any>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  const [commissionRate, setCommissionRate] = useState(5);
  
  const [selectedWithdrawal, setSelectedWithdrawal] = useState<any>(null);
  const [withdrawalDialogOpen, setWithdrawalDialogOpen] = useState(false);
  const [withdrawalAction, setWithdrawalAction] = useState('');
  const [withdrawalNotes, setWithdrawalNotes] = useState('');

  useEffect(() => {
    fetchStats();
    fetchApplications();
    fetchIPs();
    fetchWithdrawals();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/ip/stats/overview');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats');
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await api.get('/admin/ip/applications?status=pending');
      setApplications(response.data.applications);
    } catch (err) {
      toast.error('加载申请列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchIPs = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);
      
      const response = await api.get(`/admin/ip?${params}`);
      setIPs(response.data.ips);
    } catch (err) {
      toast.error('加载IP列表失败');
    }
  };

  const fetchWithdrawals = async () => {
    try {
      const response = await api.get('/admin/ip/withdrawals?status=pending');
      setWithdrawals(response.data.withdrawals);
    } catch (err) {
      toast.error('加载提现列表失败');
    }
  };

  const handleReviewApplication = async () => {
    if (!selectedApplication) return;
    
    try {
      const response = await api.post(
        `/admin/ip/applications/${selectedApplication.id}/review`,
        {
          action: reviewAction,
          commission_rate: commissionRate,
          notes: reviewNotes,
        }
      );
      
      if (response.data.success) {
        toast.success('审核完成');
        setReviewDialogOpen(false);
        fetchApplications();
        fetchIPs();
        fetchStats();
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '审核失败');
    }
  };

  const handleProcessWithdrawal = async () => {
    if (!selectedWithdrawal) return;
    
    try {
      const response = await api.post(
        `/admin/ip/withdrawals/${selectedWithdrawal.id}/process`,
        {
          action: withdrawalAction,
          admin_notes: withdrawalNotes,
        }
      );
      
      if (response.data.success) {
        toast.success('处理完成');
        setWithdrawalDialogOpen(false);
        fetchWithdrawals();
        fetchStats();
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '处理失败');
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', label: string }> = {
      pending: { variant: 'secondary', label: '待审核' },
      trial: { variant: 'default', label: '试用期' },
      active: { variant: 'default', label: '正常' },
      suspended: { variant: 'destructive', label: '已暂停' },
      rejected: { variant: 'destructive', label: '已拒绝' },
      terminated: { variant: 'destructive', label: '已终止' },
    };
    
    const { variant, label } = config[status] || { variant: 'secondary', label: status };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const getPlatformLabel = (platform: string) => {
    const platforms: Record<string, string> = {
      wechat: '微信',
      zhihu: '知乎',
      bilibili: 'B站',
      douyin: '抖音',
      redbook: '小红书',
      weibo: '微博',
      toutiao: '头条',
      other: '其他',
    };
    return platforms[platform] || platform;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">IP创作者管理</h1>
          <p className="text-gray-600 mt-1">管理IP申请、创作者列表和提现审核</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总IP数</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.total_ips || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活跃IP</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{stats.active_ips || 0}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待审核申请</p>
                <p className="text-3xl font-bold text-orange-600 mt-1">{stats.pending_applications || 0}</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总佣金支出</p>
                <p className="text-3xl font-bold text-purple-600 mt-1">
                  ¥{(stats.total_commission || 0).toFixed(0)}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="applications">
            待审核申请 ({applications.length})
          </TabsTrigger>
          <TabsTrigger value="ips">IP列表</TabsTrigger>
          <TabsTrigger value="withdrawals">
            提现审核 ({withdrawals.length})
          </TabsTrigger>
          <TabsTrigger value="stats">数据统计</TabsTrigger>
        </TabsList>

        <TabsContent value="applications">
          <Card>
            <CardContent className="p-0">
              {applications.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">暂无待审核申请</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>姓名</TableHead>
                      <TableHead>联系方式</TableHead>
                      <TableHead>平台</TableHead>
                      <TableHead>粉丝数</TableHead>
                      <TableHead>申请时间</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {applications.map((app) => (
                      <TableRow key={app.id}>
                        <TableCell className="font-medium">{app.name}</TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{app.contact}</div>
                            {app.email && <div className="text-gray-500">{app.email}</div>}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{getPlatformLabel(app.platform_type)}</Badge>
                          {app.platform_name && (
                            <div className="text-sm text-gray-500 mt-1">{app.platform_name}</div>
                          )}
                        </TableCell>
                        <TableCell>{app.followers?.toLocaleString() || '-'}</TableCell>
                        <TableCell className="text-gray-500">
                          {new Date(app.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedApplication(app);
                              setReviewDialogOpen(true);
                            }}
                          >
                            审核
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ips">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      className="pl-10"
                      placeholder="搜索姓名、邮箱、联系方式..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="全部状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部状态</SelectItem>
                    <SelectItem value="active">正常</SelectItem>
                    <SelectItem value="trial">试用期</SelectItem>
                    <SelectItem value="suspended">已暂停</SelectItem>
                    <SelectItem value="terminated">已终止</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={fetchIPs}>搜索</Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>姓名</TableHead>
                    <TableHead>等级</TableHead>
                    <TableHead>佣金比例</TableHead>
                    <TableHead>累计收益</TableHead>
                    <TableHead>推广用户</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>注册时间</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ips.map((ip) => (
                    <TableRow key={ip.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{ip.name}</div>
                          <div className="text-sm text-gray-500">{ip.contact}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge style={{ backgroundColor: ip.level_color, color: 'white' }}>
                          {ip.level_name || ip.level}
                        </Badge>
                      </TableCell>
                      <TableCell>{ip.base_commission}%</TableCell>
                      <TableCell className="text-green-600 font-medium">
                        ¥{ip.total_earned?.toFixed(2) || '0.00'}
                      </TableCell>
                      <TableCell>{ip.total_referrals || 0}</TableCell>
                      <TableCell>{getStatusBadge(ip.status)}</TableCell>
                      <TableCell className="text-gray-500">
                        {new Date(ip.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="withdrawals">
          <Card>
            <CardContent className="p-0">
              {withdrawals.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">暂无待审核提现</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>IP名称</TableHead>
                      <TableHead>申请金额</TableHead>
                      <TableHead>手续费</TableHead>
                      <TableHead>实际到账</TableHead>
                      <TableHead>收款方式</TableHead>
                      <TableHead>申请时间</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {withdrawals.map((wd) => (
                      <TableRow key={wd.id}>
                        <TableCell className="font-medium">{wd.ip_name}</TableCell>
                        <TableCell>¥{wd.amount.toFixed(2)}</TableCell>
                        <TableCell className="text-gray-500">¥{wd.fee.toFixed(2)}</TableCell>
                        <TableCell className="text-green-600 font-medium">
                          ¥{wd.actual_amount.toFixed(2)}
                        </TableCell>
                        <TableCell>
                          <div>
                            <div>{wd.account_type === 'wechat' ? '微信' : 
                                  wd.account_type === 'alipay' ? '支付宝' : '银行卡'}</div>
                            <div className="text-sm text-gray-500">{wd.account_name}</div>
                          </div>
                        </TableCell>
                        <TableCell className="text-gray-500">
                          {new Date(wd.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedWithdrawal(wd);
                              setWithdrawalDialogOpen(true);
                            }}
                          >
                            处理
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>佣金统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">总佣金</span>
                    <span className="font-semibold">¥{(stats.total_commission || 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">已结算</span>
                    <span className="font-semibold text-green-600">¥{(stats.settled_commission || 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">待结算</span>
                    <span className="font-semibold text-orange-600">¥{(stats.pending_commission || 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">待处理提现</span>
                    <span className="font-semibold">¥{(stats.pending_withdrawal_amount || 0).toFixed(2)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>推广统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">总推广用户</span>
                    <span className="font-semibold">{stats.total_referrals || 0}</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">待处理提现申请</span>
                    <span className="font-semibold">{stats.pending_withdrawals || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* 审核对话框 */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>审核IP申请</DialogTitle>
            <DialogDescription>
              审核申请信息并决定是否通过
            </DialogDescription>
          </DialogHeader>
          
          {selectedApplication && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">姓名:</span>
                  <span className="ml-2 font-medium">{selectedApplication.name}</span>
                </div>
                <div>
                  <span className="text-gray-500">联系方式:</span>
                  <span className="ml-2">{selectedApplication.contact}</span>
                </div>
                <div>
                  <span className="text-gray-500">平台:</span>
                  <span className="ml-2">{getPlatformLabel(selectedApplication.platform_type)}</span>
                </div>
                <div>
                  <span className="text-gray-500">粉丝数:</span>
                  <span className="ml-2">{selectedApplication.followers?.toLocaleString()}</span>
                </div>
              </div>
              
              {selectedApplication.introduction && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">{selectedApplication.introduction}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label>佣金比例 (%)</Label>
                <Input
                  type="number"
                  value={commissionRate}
                  onChange={(e) => setCommissionRate(parseFloat(e.target.value))}
                  min={1}
                  max={50}
                />
              </div>

              <div className="space-y-2">
                <Label>审核备注</Label>
                <Textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="可选的审核备注..."
                />
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setReviewAction('reject');
                handleReviewApplication();
              }}
            >
              拒绝
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setReviewAction('trial');
                handleReviewApplication();
              }}
            >
              试用期
            </Button>
            <Button
              onClick={() => {
                setReviewAction('approve');
                handleReviewApplication();
              }}
            >
              通过
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 提现处理对话框 */}
      <Dialog open={withdrawalDialogOpen} onOpenChange={setWithdrawalDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>处理提现申请</DialogTitle>
            <DialogDescription>
              确认处理提现申请
            </DialogDescription>
          </DialogHeader>
          
          {selectedWithdrawal && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">IP名称:</span>
                  <span className="ml-2 font-medium">{selectedWithdrawal.ip_name}</span>
                </div>
                <div>
                  <span className="text-gray-500">申请金额:</span>
                  <span className="ml-2 font-medium">¥{selectedWithdrawal.amount.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-500">手续费:</span>
                  <span className="ml-2">¥{selectedWithdrawal.fee.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-500">实际到账:</span>
                  <span className="ml-2 text-green-600">¥{selectedWithdrawal.actual_amount.toFixed(2)}</span>
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm">
                  <span className="text-gray-500">收款账户:</span>
                  <span className="ml-2">{selectedWithdrawal.account_name} - {selectedWithdrawal.account_info}</span>
                </p>
              </div>

              <div className="space-y-2">
                <Label>处理备注</Label>
                <Textarea
                  value={withdrawalNotes}
                  onChange={(e) => setWithdrawalNotes(e.target.value)}
                  placeholder="可选的处理备注..."
                />
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setWithdrawalDialogOpen(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setWithdrawalAction('reject');
                handleProcessWithdrawal();
              }}
            >
              拒绝
            </Button>
            <Button
              onClick={() => {
                setWithdrawalAction('approve');
                handleProcessWithdrawal();
              }}
            >
              确认打款
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
