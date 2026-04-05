import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Users, 
  DollarSign, 
  TrendingUp, 
  Link as LinkIcon, 
  Copy, 
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  UserPlus
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import api from '@/services/api';

interface DashboardData {
  basic: {
    id: string;
    name: string;
    level: string;
    level_name: string;
    level_color: string;
    base_commission: number;
    balance: number;
    total_earned: number;
    total_referrals: number;
    status: string;
  };
  today: {
    new_users: number;
    commission: number;
  };
  month: {
    new_users: number;
    commission: number;
  };
  pending_commission: number;
  trend: {
    dates: string[];
    new_users: number[];
    commission: number[];
  };
  funnel: {
    clicks: number;
    registers: number;
    orders: number;
    conversion_rate: number;
  };
  recent_referrals: any[];
}

export default function IPDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/ip/dashboard');
      setData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <UserPlus className="h-10 w-10 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">成为IP创作者</h2>
          <p className="text-gray-600 mb-6">
            {error?.includes('未激活') || error?.includes('不是IP创作者')
              ? '您还不是IP创作者，申请成为创作者后即可享受推广收益'
              : error || '暂无数据，请先申请成为IP创作者'}
          </p>
          <div className="space-y-4">
            <Button 
              onClick={() => navigate('/ip-apply')}
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              立即申请
            </Button>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-50 rounded-lg p-4">
                <DollarSign className="h-6 w-6 text-green-500 mx-auto mb-2" />
                <p className="font-medium">高额佣金</p>
                <p className="text-gray-500">最高20%</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <TrendingUp className="h-6 w-6 text-blue-500 mx-auto mb-2" />
                <p className="font-medium">阶梯奖励</p>
                <p className="text-gray-500">多推多得</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const chartData = data?.trend?.dates?.map((date, index) => ({
    date: date.slice(5),
    users: data.trend.new_users[index],
    commission: data.trend.commission[index],
  })) || [];

  const levelProgress = {
    bronze: { next: 'silver', current: 0, target: 1000 },
    silver: { next: 'gold', current: 1000, target: 5000 },
    gold: { next: 'platinum', current: 5000, target: 20000 },
    platinum: { next: 'diamond', current: 20000, target: 100000 },
    diamond: { next: null, current: 100000, target: 100000 },
  };

  const currentLevel = levelProgress[data?.basic?.level as keyof typeof levelProgress] || levelProgress.bronze;
  const progressPercent = currentLevel.next 
    ? Math.min(((data?.basic?.total_earned || 0 - currentLevel.current) / (currentLevel.target - currentLevel.current)) * 100, 100)
    : 100;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">创作者中心</h1>
          <p className="text-gray-600 mt-1">欢迎回来，{data?.basic?.name || '创作者'}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge 
            style={{ backgroundColor: data?.basic?.level_color || '#888', color: 'white' }}
            className="px-3 py-1"
          >
            {data?.basic?.level_name || '普通'}
          </Badge>
          <Badge variant="outline" className="px-3 py-1">
            佣金比例: {data?.basic?.base_commission || 10}%
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">今日新增用户</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{data?.today?.new_users || 0}</p>
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
                <p className="text-sm text-gray-600">今日预估收益</p>
                <p className="text-3xl font-bold text-green-600 mt-1">¥{(data?.today?.commission || 0).toFixed(2)}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">可提现余额</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">¥{(data?.basic?.balance || 0).toFixed(2)}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">累计收益</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">¥{(data?.basic?.total_earned || 0).toFixed(2)}</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>收益趋势（近30天）</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="commission" 
                    stroke="#10b981" 
                    fill="#d1fae5" 
                    name="佣金(元)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>等级进度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">当前等级</span>
                <Badge style={{ backgroundColor: data?.basic?.level_color || '#888', color: 'white' }}>
                  {data?.basic?.level_name || '普通'}
                </Badge>
              </div>
              
              {currentLevel.next && (
                <>
                  <Progress value={progressPercent} className="h-3" />
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">
                      ¥{(data?.basic?.total_earned || 0).toFixed(0)} / ¥{currentLevel.target}
                    </span>
                    <span className="text-gray-500">
                      距离下一等级还需 ¥{(currentLevel.target - (data?.basic?.total_earned || 0)).toFixed(0)}
                    </span>
                  </div>
                </>
              )}

              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 mb-2">推广统计</p>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-500">总推广用户</span>
                    <span className="font-medium">{data?.basic?.total_referrals || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">本月新增</span>
                    <span className="font-medium">{data?.month?.new_users || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">本月收益</span>
                    <span className="font-medium text-green-600">¥{(data?.month?.commission || 0).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>转化漏斗</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Eye className="h-5 w-5 text-blue-600" />
                  <span>链接点击</span>
                </div>
                <span className="font-bold text-blue-600">{data?.funnel?.clicks || 0}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-purple-600" />
                  <span>注册用户</span>
                </div>
                <span className="font-bold text-purple-600">{data?.funnel?.registers || 0}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <span>消费用户</span>
                </div>
                <span className="font-bold text-green-600">{data?.funnel?.orders || 0}</span>
              </div>

              <div className="pt-4 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">转化率</span>
                  <span className="text-xl font-bold text-green-600">{data?.funnel?.conversion_rate || 0}%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最近推广用户</CardTitle>
          </CardHeader>
          <CardContent>
            {(data?.recent_referrals?.length || 0) === 0 ? (
              <p className="text-center text-gray-500 py-8">暂无推广用户</p>
            ) : (
              <div className="space-y-3">
                {data?.recent_referrals?.map((ref: any) => (
                  <div key={ref.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium">{ref.email || ref.username || '用户'}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(ref.registered_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">消费 ¥{ref.total_amount?.toFixed(2) || '0'}</p>
                      <Badge variant={ref.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                        {ref.status === 'active' ? '活跃' : '待激活'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
