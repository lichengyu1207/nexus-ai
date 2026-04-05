import React, { useState } from 'react';
import { Card, Select, Button, Space, Row, Col, Statistic, Table } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

const LoadAnalysisPage: React.FC = () => {
  const [timeRange] = useState('24h');

  const correlationData = [
    { time: '00:00', input: 120, output: 115 }, { time: '04:00', input: 45, output: 42 },
    { time: '08:00', input: 380, output: 365 }, { time: '12:00', input: 520, output: 498 },
    { time: '16:00', input: 480, output: 470 }, { time: '20:00', input: 320, output: 310 }
  ];

  const predictionData = [
    { time: '现在', queue: 245 }, { time: '+1h', queue: 312 },
    { time: '+2h', queue: 428 }, { time: '+3h', queue: 385 },
    { time: '+4h', queue: 290 }, { time: '+5h', queue: 220 }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="负载压力分析">
        <Space style={{ marginBottom: 16 }}>
          <Select defaultValue="queue1" options={[{ value: 'queue1', label: '主任务队列' }]} />
          <Select defaultValue="24h" options={[{ value: '1h', label: '1小时' }, { value: '6h', label: '6小时' }, { value: '24h', label: '24小时' }, { value: '7d', label: '7天' }]} />
          <Button type="primary">查询分析数据</Button>
        </Space>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="滞后时间相关性分析" size="small">
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={correlationData}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" /><YAxis />
                  <Tooltip /><Legend />
                  <Line type="monotone" dataKey="input" stroke="#1890ff" name="任务入队速率" />
                  <Line type="monotone" dataKey="output" stroke="#52c41a" name="智能体处理速率" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="任务负载预测" size="small">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={predictionData}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" /><YAxis />
                  <Tooltip /><Legend />
                  <Bar dataKey="queue" fill="#e94560" name="预测队列长度" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={8}><Card><Statistic title="当前积压时长" value={12.3} suffix="分钟" /></Card></Col>
          <Col span={8}><Card><Statistic title="平均响应时间" value={2.34} suffix="秒" /></Card></Col>
          <Col span={8}><Card><Statistic title="系统负载偏差" value={8.5} suffix="%" /></Card></Col>
        </Row>

        <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
          <Button>执行互相关分析</Button>
          <Button>自动标定滞后时间</Button>
          <Button>计算任务累积序列</Button>
          <Button>执行影响组合</Button>
          <Button type="primary">下载分析报告</Button>
        </div>
      </Card>
    </div>
  );
};

export default LoadAnalysisPage;
