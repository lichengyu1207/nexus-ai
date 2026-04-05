import React, { useState } from 'react';
import { Card, Form, Input, Select, Button, Radio, Slider, Upload, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const TaskCreatePage: React.FC = () => {
  const [form] = Form.useForm();
  const [taskType, setTaskType] = useState('property');

  const handleCreate = (values: any) => {
    message.success(`任务创建成功：${values.title || '新建任务'}`);
  };

  return (
    <div style={{ padding: 24, maxWidth: 800 }}>
      <Card title="智能咨询与任务创建">
        <Radio.Group value={taskType} onChange={e => setTaskType(e.target.value)} style={{ marginBottom: 24 }} buttonStyle="solid">
          <Radio.Button value="natural">自然语言输入</Radio.Button>
          <Radio.Button value="structured">结构化表单</Radio.Button>
          <Radio.Button value="batch">批量导入</Radio.Button>
        </Radio.Group>

        {taskType === 'natural' && (
          <Card size="small" title="自然语言输入" style={{ marginBottom: 16 }}>
            <p style={{ color: '#666', marginBottom: 12 }}>在聊天界面直接输入问题，系统将自动解析用户意图，拆解为多个子任务。</p>
            <Input.TextArea rows={4} placeholder="例如：帮我分析深圳南山区100平米学区房，预算1000万" />
            <Button type="primary" style={{ marginTop: 12 }}>提交分析</Button>
          </Card>
        )}

        {taskType === 'structured' && (
          <Form form={form} layout="vertical" onFinish={handleCreate}>
            <Form.Item label="任务类型" name="type" initialValue="房产分析">
              <Select options={[
                { value: 'property', label: '房产分析' }, { value: 'investment', label: '投资评估' },
                { value: 'trend', label: '趋势预测' }, { value: 'policy', label: '政策解读' }
              ]} />
            </Form.Item>
            <Form.Item label="城市" name="city">
              <Select showSearch options={['北京','上海','深圳','杭州','广州','成都','武汉','南京','苏州','长沙'].map(c => ({ value: c, label: c }))} />
            </Form.Item>
            <Form.Item label="区域" name="district">
              <Input placeholder="如：南山区、朝阳区、浦东新区" />
            </Form.Item>
            <Form.Item label="面积(㎡)" name="area"><Input type="number" /></Form.Item>
            <Form.Item label="预算(万元)" name="budget"><Input type="number" /></Form.Item>
            <Form.Item label="特殊需求" name="requirements">
              <Input.TextArea rows={3} placeholder="如：学区房、近地铁、三居室..." />
            </Form.Item>
            <Form.Item><Button type="primary" htmlType="submit" icon={<PlusOutlined />}>创建任务</Button></Form.Item>
          </Form>
        )}

        {taskType === 'batch' && (
          <Card size="small" title="批量导入">
            <p style={{ color: '#666', marginBottom: 12 }}>选择CSV或Excel文件，需包含列头：城市、区域、面积、预算等。</p>
            <Upload.Dragger accept=".csv,.xlsx,.xls" multiple={false}>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 CSV / Excel 格式</p>
            </Upload.Dragger>
            <Button type="primary" style={{ marginTop: 12 }}>上传并解析</Button>
          </Card>
        )}
      </Card>
    </div>
  );
};

export default TaskCreatePage;
