import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Avatar, message, Spin, Tag } from 'antd';
import { SendOutlined, PaperClipOutlined, ClearOutlined } from '@ant-design/icons';

interface Message { role: 'user' | 'assistant'; content: string; time: string; }

const ConsultPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '您好！我是房都督智能顾问周瑜。请问有什么可以帮您？我可以帮您分析房价走势、评估房产价值、解读政策法规等。', time: new Date().toLocaleTimeString() }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [personality] = useState('周瑜');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: input, time: new Date().toLocaleTimeString() };
    setMessages(prev => [...prev, userMsg]);
    setInput(''); setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: input, personality })
      });
      const data = await res.json();
      const assistantMsg: Message = {
        role: 'assistant',
        content: data.data?.response || data.reply || '抱歉，暂时无法回答',
        time: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      message.error('网络错误，请重试');
    }
    setLoading(false);
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#f0f2f5' }}>
      <div style={{ padding: '12px 24px', background: '#fff', borderBottom: '1px solid #e8e8e8', display: 'flex', alignItems: 'center', gap: 12 }}>
        <Avatar style={{ background: '#e94560' }}>{personality[0]}</Avatar>
        <div>
          <strong>{personality}</strong><span style={{ marginLeft: 8, color: '#888' }}>智能房产顾问</span>
        </div>
        <Tag color="blue" style={{ marginLeft: 'auto' }}>在线</Tag>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '70%', padding: '12px 16px', borderRadius: 12,
              background: m.role === 'user' ? '#e94560' : '#fff',
              color: m.role === 'user' ? '#fff' : '#333',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
              <div>{m.content}</div>
              <div style={{ fontSize: 11, marginTop: 6, opacity: 0.6 }}>{m.time}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: 12, borderRadius: 12, background: '#fff' }}><Spin size="small" /> 思考中...</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div style={{ padding: 16, background: '#fff', borderTop: '1px solid #e8e8e8', display: 'flex', gap: 8 }}>
        <Button icon={<PaperClipOutlined />} />
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onPressEnter={handleSend}
          placeholder="输入您的房产问题，如：帮我分析深圳南山区100平学区房..."
          size="large"
          style={{ flex: 1, borderRadius: 20 }}
        />
        <Button type="primary" icon={<SendOutlined />} onClick={handleSend} size="large"
          shape="circle" style={{ background: '#e94560', border: 'none' }} />
      </div>
    </div>
  );
};

export default ConsultPage;
