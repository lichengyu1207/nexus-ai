import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  UserPlus, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Globe, 
  Users, 
  DollarSign,
  TrendingUp,
  Shield
} from 'lucide-react';
import axios from 'axios';

const platformOptions = [
  { value: 'wechat', label: '微信公众号/视频号', icon: '📱' },
  { value: 'zhihu', label: '知乎', icon: '🔵' },
  { value: 'bilibili', label: 'B站', icon: '📺' },
  { value: 'douyin', label: '抖音', icon: '🎵' },
  { value: 'redbook', label: '小红书', icon: '📕' },
  { value: 'toutiao', label: '今日头条', icon: '📰' },
  { value: 'weibo', label: '微博', icon: '🐦' },
  { value: 'other', label: '其他平台', icon: '🌐' },
];

const benefits = [
  {
    icon: <DollarSign className="h-6 w-6 text-green-500" />,
    title: '高额佣金',
    description: '最高可达20%的推广佣金，多推广多收益'
  },
  {
    icon: <TrendingUp className="h-6 w-6 text-blue-500" />,
    title: '阶梯奖励',
    description: '推广越多，佣金比例越高，上不封顶'
  },
  {
    icon: <Users className="h-6 w-6 text-purple-500" />,
    title: '专属粉丝',
    description: '通过您链接注册的用户终身绑定，持续收益'
  },
  {
    icon: <Shield className="h-6 w-6 text-orange-500" />,
    title: '数据透明',
    description: '实时查看推广数据、收益明细，清晰透明'
  },
];

export default function IPApplyPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    email: '',
    platform_type: '',
    platform_id: '',
    platform_name: '',
    followers: 0,
    introduction: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/ip/apply', formData);
      
      if (response.data.success) {
        setSuccess(true);
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '申请提交失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-8 pb-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">申请已提交！</h2>
            <p className="text-gray-600 mb-6">
              我们将在1-3个工作日内完成审核，届时会通过您留下的联系方式通知您。
            </p>
            <Button onClick={() => navigate('/')} className="w-full">
              返回首页
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <Badge className="mb-4" variant="secondary">
            创作者招募计划
          </Badge>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            成为房产IP创作者
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            加入我们的创作者生态，通过分享专业的房产分析内容，获得丰厚的推广收益
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          {benefits.map((benefit, index) => (
            <Card key={index} className="text-center">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  {benefit.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-sm text-gray-600">{benefit.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="h-5 w-5" />
                  填写申请信息
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">姓名/昵称 *</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        placeholder="您的称呼"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contact">联系方式 *</Label>
                      <Input
                        id="contact"
                        value={formData.contact}
                        onChange={(e) => handleChange('contact', e.target.value)}
                        placeholder="微信号/手机号"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">邮箱（选填）</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      placeholder="your@email.com"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="platform">主要平台 *</Label>
                      <Select
                        value={formData.platform_type}
                        onValueChange={(value) => handleChange('platform_type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择您的平台" />
                        </SelectTrigger>
                        <SelectContent>
                          {platformOptions.map((platform) => (
                            <SelectItem key={platform.value} value={platform.value}>
                              {platform.icon} {platform.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="followers">粉丝数量</Label>
                      <Input
                        id="followers"
                        type="number"
                        value={formData.followers}
                        onChange={(e) => handleChange('followers', parseInt(e.target.value) || 0)}
                        placeholder="0"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="platform_id">平台账号ID</Label>
                      <Input
                        id="platform_id"
                        value={formData.platform_id}
                        onChange={(e) => handleChange('platform_id', e.target.value)}
                        placeholder="账号ID或链接"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="platform_name">账号名称</Label>
                      <Input
                        id="platform_name"
                        value={formData.platform_name}
                        onChange={(e) => handleChange('platform_name', e.target.value)}
                        placeholder="账号昵称"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="introduction">个人简介</Label>
                    <Textarea
                      id="introduction"
                      value={formData.introduction}
                      onChange={(e) => handleChange('introduction', e.target.value)}
                      placeholder="介绍一下您的创作领域、内容风格等..."
                      rows={4}
                    />
                  </div>

                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        提交中...
                      </>
                    ) : (
                      '提交申请'
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>佣金规则</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">基础佣金</span>
                    <span className="font-semibold text-green-600">5%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">月推广≥1000元</span>
                    <span className="font-semibold text-green-600">6%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">月推广≥5000元</span>
                    <span className="font-semibold text-green-600">7%</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">月推广≥10000元</span>
                    <span className="font-semibold text-green-600">8%+</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>申请须知</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>拥有房产、财经、生活等相关领域创作经验</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>粉丝数量不限，但需要有真实活跃粉丝</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>认可平台价值观，愿意长期合作</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>遵守平台规则，不进行虚假推广</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Globe className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">有问题？</p>
                    <p className="text-sm text-gray-600">联系客服微信：svip6763</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
