import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { api } from '@/services/api';
import { slideIn } from '@/config/animation';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  estimate?: {
    base_value: number;
    atmosphere_score: number;
    final_value: number;
    factors: {
      community: number;
      environment: number;
      convenience: number;
      safety: number;
      culture: number;
      potential: number;
    };
  };
  timestamp: string;
}

const AtmosphereChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      const response = await api.post('/atmosphere/chat', {
        message: input,
        session_id: sessionId
      });

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.reply,
        estimate: response.data.estimate,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.data.session_id && !sessionId) {
        setSessionId(response.data.session_id);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '抱歉，处理您的请求时出现错误，请稍后重试。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
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

  return (
    <motion.div {...slideIn} className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-text-primary mb-4">智能氛围估价咨询</h2>
        
        {/* 消息区域 */}
        <div className="h-96 overflow-y-auto mb-4 p-4 border border-border-light rounded-lg bg-bg-tertiary">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-text-secondary">您好！我是氛围估价助手，请问有什么可以帮您的？</p>
              <p className="text-text-secondary text-sm mt-2">您可以告诉我房产地址，我会为您进行氛围估价分析。</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-4 ${message.role === 'user' 
                      ? 'bg-accent-gold text-gray-900' 
                      : 'bg-bg-secondary border border-border-light'}`}
                  >
                    <p className={message.role === 'user' ? 'text-gray-900' : 'text-text-primary'}>
                      {message.content}
                    </p>
                    
                    {/* 估价结果卡片 */}
                    {message.estimate && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mt-4 p-4 bg-bg-tertiary rounded-lg border border-border-light"
                      >
                        <h4 className="font-medium text-text-primary mb-3">氛围估价结果</h4>
                        <div className="grid grid-cols-3 gap-3 mb-3">
                          <div>
                            <p className="text-xs text-text-secondary">基础价值</p>
                            <p className="font-medium text-text-primary">{formatCurrency(message.estimate.base_value)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-text-secondary">氛围评分</p>
                            <p className="font-medium text-accent-gold">{message.estimate.atmosphere_score.toFixed(1)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-text-secondary">最终价值</p>
                            <p className="font-medium text-status-success">{formatCurrency(message.estimate.final_value)}</p>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <p className="text-xs text-text-secondary mb-2">氛围因素：</p>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(message.estimate.factors).map(([key, value]) => (
                              <div key={key} className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${getFactorColor(value)}`}></div>
                                <span className="text-xs text-text-secondary">
                                  {{ 
                                    community: '社区氛围',
                                    environment: '自然环境',
                                    convenience: '生活便利',
                                    safety: '安全指数',
                                    culture: '文化底蕴',
                                    potential: '发展潜力'
                                  }[key as keyof typeof message.estimate.factors]}
                                </span>
                                <span className="text-xs font-medium text-text-primary ml-auto">
                                  {value.toFixed(0)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="请描述您的房产需求..."
            disabled={isSending}
          />
          <Button
            onClick={sendMessage}
            disabled={isSending || !input.trim()}
          >
            {isSending ? '发送中...' : '发送'}
          </Button>
        </div>

        {/* 快捷问题 */}
        <div className="mt-4">
          <p className="text-sm text-text-secondary mb-2">快捷问题：</p>
          <div className="flex flex-wrap gap-2">
            {[
              '北京市朝阳区望京SOHO T1',
              '上海市浦东新区陆家嘴',
              '深圳市南山区科技园',
              '广州市天河区珠江新城'
            ].map((address) => (
              <Button
                key={address}
                variant="ghost"
                size="sm"
                onClick={() => setInput(address)}
              >
                {address}
              </Button>
            ))}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default AtmosphereChat;