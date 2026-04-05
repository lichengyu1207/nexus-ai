import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
  Link as LinkIcon, 
  Plus, 
  Copy, 
  QrCode, 
  Trash2, 
  Eye,
  Loader2,
  CheckCircle,
  ExternalLink
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';
import { toast } from 'sonner';

interface Link {
  id: string;
  link_type: string;
  url: string;
  code: string;
  channel: string;
  description: string;
  click_count: number;
  register_count: number;
  is_active: number;
  created_at: string;
}

export default function IPLinksPage() {
  const [links, setLinks] = useState<Link[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    link_type: 'short_url',
    channel: '',
    description: '',
  });

  useEffect(() => {
    fetchLinks();
  }, []);

  const fetchLinks = async () => {
    try {
      const response = await axios.get('/api/ip/links');
      setLinks(response.data.links);
    } catch (err) {
      toast.error('加载链接失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      const response = await axios.post('/api/ip/links', formData);
      if (response.data.success) {
        toast.success('链接创建成功');
        setDialogOpen(false);
        fetchLinks();
        setFormData({ link_type: 'short_url', channel: '', description: '' });
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '创建失败');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (linkId: string) => {
    if (!confirm('确定要删除此链接吗？')) return;
    
    try {
      await axios.delete(`/api/ip/links/${linkId}`);
      toast.success('链接已删除');
      fetchLinks();
    } catch (err) {
      toast.error('删除失败');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('已复制到剪贴板');
  };

  const showQrCode = (url: string) => {
    setQrCodeUrl(url);
  };

  const getLinkTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      short_url: '短链接',
      qrcode: '二维码',
      poster: '海报',
    };
    return types[type] || type;
  };

  const getChannelLabel = (channel: string) => {
    if (!channel) return '-';
    const channels: Record<string, string> = {
      wechat: '微信',
      zhihu: '知乎',
      douyin: '抖音',
      bilibili: 'B站',
      redbook: '小红书',
      weibo: '微博',
    };
    return channels[channel] || channel;
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
          <h1 className="text-3xl font-bold text-gray-900">推广链接管理</h1>
          <p className="text-gray-600 mt-1">创建和管理您的专属推广链接</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              创建链接
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建推广链接</DialogTitle>
              <DialogDescription>
                选择链接类型和推广渠道，系统将为您生成专属推广链接
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>链接类型</Label>
                <Select
                  value={formData.link_type}
                  onValueChange={(value) => setFormData({ ...formData, link_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="short_url">短链接</SelectItem>
                    <SelectItem value="qrcode">二维码</SelectItem>
                    <SelectItem value="poster">海报</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>推广渠道（选填）</Label>
                <Select
                  value={formData.channel}
                  onValueChange={(value) => setFormData({ ...formData, channel: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择渠道" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="wechat">微信</SelectItem>
                    <SelectItem value="zhihu">知乎</SelectItem>
                    <SelectItem value="douyin">抖音</SelectItem>
                    <SelectItem value="bilibili">B站</SelectItem>
                    <SelectItem value="redbook">小红书</SelectItem>
                    <SelectItem value="weibo">微博</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>备注说明</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="例如：公众号文章底部"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleCreate} disabled={creating}>
                {creating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    创建中...
                  </>
                ) : (
                  '创建'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          {links.length === 0 ? (
            <div className="text-center py-12">
              <LinkIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">暂无推广链接</p>
              <p className="text-sm text-gray-400 mt-1">点击上方按钮创建您的第一个推广链接</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>链接类型</TableHead>
                  <TableHead>推广链接</TableHead>
                  <TableHead>渠道</TableHead>
                  <TableHead>点击/注册</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {links.map((link) => (
                  <TableRow key={link.id}>
                    <TableCell>
                      <Badge variant="outline">{getLinkTypeLabel(link.link_type)}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {link.url}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(link.url)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>{getChannelLabel(link.channel)}</TableCell>
                    <TableCell>
                      <span className="font-medium">{link.click_count}</span>
                      <span className="text-gray-400"> / </span>
                      <span className="text-green-600">{link.register_count}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={link.is_active ? 'default' : 'secondary'}>
                        {link.is_active ? '正常' : '已禁用'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-500">
                      {new Date(link.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => showQrCode(link.url)}
                          title="查看二维码"
                        >
                          <QrCode className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(link.url, '_blank')}
                          title="打开链接"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(link.id)}
                          className="text-red-500 hover:text-red-700"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {qrCodeUrl && (
        <Dialog open={!!qrCodeUrl} onOpenChange={() => setQrCodeUrl(null)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>推广二维码</DialogTitle>
              <DialogDescription>
                扫描二维码即可访问推广页面
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col items-center py-4">
              <div className="bg-white p-4 rounded-lg border">
                <QRCodeSVG value={qrCodeUrl} size={200} />
              </div>
              <p className="text-sm text-gray-500 mt-4 text-center break-all">
                {qrCodeUrl}
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setQrCodeUrl(null)}>
                关闭
              </Button>
              <Button onClick={() => copyToClipboard(qrCodeUrl)}>
                <Copy className="h-4 w-4 mr-2" />
                复制链接
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
