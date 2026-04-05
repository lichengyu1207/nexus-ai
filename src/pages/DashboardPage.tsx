import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag, Avatar } from 'antd';
import {
  UserOutlined, FileTextOutlined, ThunderboltOutlined,
  RiseOutlined, TeamOutlined, SafetyCertificateOutlined
} from '@ant-design/icons';

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState({
    totalUsers: 12847, totalTasks: 45632, activeAgents: 42,
    successRate: 98.6, avgResponseTime: 1.23, todayReports: 328
  });
  const [recentTasks, setRecentTasks] = useState([
    { id: 1, title: '深圳南山区学区房分析', status: '已完成', user: '张三', time: '2分钟前' },
    { id: 2, title: '北京朝阳区投资评估', status: '执行中', user: '李四', time: '5分钟前' },
    { id: 3, title: '上海浦东新区趋势预测', status: '排队中', user: '王五', time: '10分钟前' },
    { id: 4, title: '广州天河区政策解读', status: '已完成', user: '赵六', time: '15分钟前' },
    { id: 5, title: '杭州西湖区房价分析', status: '已完成', user: '孙七', time: '20分钟前' }
  ]);

  const agentHealth = [
    { name: '中书省', health: 98, tasks: 156, cpu: 45 },
    { name: '门下省', health: 95, tasks: 89, cpu: 38 },
    { name: '尚书省', health: 99, tasks: 234, cpu: 62 },
    { name: '户部', health: 97, tasks: 445, cpu: 55 },
    { name: '工部', health: 96, tasks: 312, cpu: 48 },
    { name: '刑部', health: 94, tasks: 67, cpu: 25 }
  ];

  return (
    <div style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: 24 }}>仪表盘总览</h2>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="用户总数" value={stats.totalUsers} prefix={<UserOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="任务总数" value={stats.totalTasks} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="活跃智能体" value={stats.activeAgents} prefix={<ThunderboltOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="成功率" value={stats.successRate} suffix="%" prefix={<RiseOutlined />} valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="平均响应(s)" value={stats.avgResponseTime} precision={2} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="今日报告" value={stats.todayReports} prefix={<SafetyCertificateOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="最近任务" extra={<a>查看全部</a>}>
            <Table dataSource={recentTasks} rowKey="id" pagination={false} size="small"
              columns={[
                { title: '任务', dataIndex: 'title', key: 'title' },
                { title: '状态', dataIndex: 'status', key: 'status',
                  render: (s: string) => <Tag color={s === '已完成' ? 'green' : s === '执行中' ? 'blue' : 'orange'}>{s}</Tag>
                },
                { title: '用户', dataIndex: 'user', key: 'user' },
                { title: '时间', dataIndex: 'time', key: 'time' }
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="三省六部健康度">
            {agentHealth.map(a => (
              <div key={a.name} style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                <Avatar size="small" style={{ background: a.health > 95 ? '#52c41a' : '#faad14' }}>{a.name[0]}</Avatar>
                <span style={{ width: 60, marginLeft: 8 }}>{a.name}</span>
                <Progress percent={a.health} size="small" showInfo={false} style={{ flex: 1 }} />
                <span style={{ width: 40, textAlign: 'right', fontSize: 12, color: '#888' }}>{a.health}%</span>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;
