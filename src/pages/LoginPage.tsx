import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Input, Button, Checkbox, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', remember: true });
  const navigate = useNavigate();

  const handleLogin = async () => {
    if (!form.email || !form.password) {
      message.warning('请输入邮箱和密码');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        message.success('登录成功');
        navigate('/dashboard');
      } else {
        message.error(data.detail || '登录失败');
      }
    } catch (e) {
      message.error('网络错误');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)'
    }}>
      <Card style={{ width: 420, borderRadius: 16, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, margin: 0, color: '#e94560' }}>房都督</h1>
          <p style={{ color: '#888', marginTop: 8 }}>AI大模型智能决策中枢平台</p>
        </div>
        <Input
          prefix={<UserOutlined />}
          placeholder="邮箱"
          size="large"
          value={form.email}
          onChange={e => setForm({ ...form, email: e.target.value })}
          style={{ marginBottom: 16 }}
        />
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="密码"
          size="large"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          onPressEnter={handleLogin}
          style={{ marginBottom: 24 }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
          <Checkbox checked={form.remember} onChange={e => setForm({ ...form, remember: e.target.checked })}>
            记住我
          </Checkbox>
          <a style={{ color: '#e94560' }}>忘记密码？</a>
        </div>
        <Button type="primary" size="large" block loading={loading} onClick={handleLogin}
          style={{ height: 48, fontSize: 16, background: '#e94560', border: 'none' }}>
          登录
        </Button>
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <span style={{ color: '#888' }}>还没有账号？</span>
          <a style={{ color: '#e94560', marginLeft: 8 }}>立即注册</a>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
