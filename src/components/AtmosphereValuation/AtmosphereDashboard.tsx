import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '@/services/api';
import { slideIn } from '@/config/animation';

interface AtmosphereFactors {
  community: number;
  environment: number;
  convenience: number;
  safety: number;
  culture: number;
  potential: number;
}

interface EstimateResult {
  base_value: number;
  atmosphere_score: number;
  final_value: number;
  factors: AtmosphereFactors;
}

interface HistoryItem {
  id: string;
  address: string;
  value: number;
  timestamp: string;
}

const AtmosphereDashboard: React.FC = () => {
  const [address, setAddress] = useState('');
  const [estimate, setEstimate] = useState<EstimateResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await api.get('/atmosphere/history');
      setHistory(response.data || []);
    } catch (error) {
      console.error('加载历史记录失败:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleEstimate = async () => {
    if (!address.trim()) return;

    setIsLoading(true);
    try {
      const response = await api.post('/atmosphere/estimate', {
        address
      });
      setEstimate(response.data);
      loadHistory();
    } catch (error) {
      console.error('估价失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getFactorColor = (score: number) => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 80) return 'bg-blue-500';
    if (score >= 70) return 'bg-yellow-500';
    if (score >= 60) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const factorData = estimate ? Object.entries(estimate.factors).map(([name, value]) => ({
    name: {
      community: '社区氛围',
      environment: '自然环境',
      convenience: '生活便利',
      safety: '安全指数',
      culture: '文化底蕴',
      potential: '发展潜力'
    }[name as keyof AtmosphereFactors],
    value
  })) : [];

  return (
    <motion.div {...slideIn} className="space-y-6">
      {/* 估价表单 */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">氛围估价</h2>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Label htmlFor="address">房产地址</Label>
              <Input
                id="address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="请输入详细地址"
                className="mt-1"
              />
            </div>
            <Button
              onClick={handleEstimate}
              disabled={isLoading || !address.trim()}
              className="mt-6 md:mt-0 px-8"
            >
              {isLoading ? '估价中...' : '开始估价'}
            </Button>
          </div>
        </div>
      </Card>

      {/* 估价结果 */}
      {estimate && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* 价值卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <h3 className="text-sm text-text-secondary mb-2">基础价值</h3>
              <p className="text-2xl font-bold text-text-primary">{formatCurrency(estimate.base_value)}</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm text-text-secondary mb-2">氛围评分</h3>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-accent-gold">{estimate.atmosphere_score.toFixed(1)}</p>
                <p className="text-text-secondary">/ 100</p>
              </div>
              <ProgressBar
                progress={estimate.atmosphere_score}
                className="mt-2"
              />
            </Card>
            <Card className="p-6">
              <h3 className="text-sm text-text-secondary mb-2">最终价值</h3>
              <p className="text-2xl font-bold text-status-success">{formatCurrency(estimate.final_value)}</p>
              <p className="text-xs text-text-secondary mt-1">
                氛围调整: {(estimate.final_value / estimate.base_value * 100 - 100).toFixed(1)}%
              </p>
            </Card>
          </div>

          {/* 氛围因素分析 */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-text-primary mb-4">氛围因素分析</h3>
            <div className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={factorData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="name" width={100} />
                    <Tooltip
                      formatter={(value) => [`${value}分`, '评分']}
                      contentStyle={{ backgroundColor: 'rgba(10, 35, 66, 0.9)', borderColor: 'rgba(212, 175, 55, 0.3)' }}
                    />
                    <Bar dataKey="value" fill="#D4AF37" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(estimate.factors).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${getFactorColor(value)}`}></div>
                    <span className="text-sm text-text-secondary">
                      {{ 
                        community: '社区氛围',
                        environment: '自然环境',
                        convenience: '生活便利',
                        safety: '安全指数',
                        culture: '文化底蕴',
                        potential: '发展潜力'
                      }[key as keyof AtmosphereFactors]}
                    </span>
                    <span className="text-sm font-medium text-text-primary ml-auto">
                      {value.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* 历史记录 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-text-primary">历史估价记录</h3>
          <Button variant="ghost" size="sm" onClick={loadHistory} disabled={isLoadingHistory}>
            {isLoadingHistory ? '加载中...' : '刷新'}
          </Button>
        </div>
        {history.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-text-secondary">暂无估价记录</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 border border-border-light rounded-lg hover:bg-bg-tertiary transition-colors">
                <div>
                  <p className="font-medium text-text-primary">{item.address}</p>
                  <p className="text-xs text-text-secondary">
                    {new Date(item.timestamp).toLocaleString('zh-CN')}
                  </p>
                </div>
                <p className="font-bold text-status-success">{formatCurrency(item.value)}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </motion.div>
  );
};

export default AtmosphereDashboard;