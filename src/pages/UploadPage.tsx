import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  GiftIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

interface DataType {
  id: string;
  name: string;
  display_name: string;
  base_reward: number;
  max_reward: number;
  unit: string;
  description: string | null;
}

interface Upload {
  id: string;
  data_type_id: string;
  data_type_name: string;
  raw_data: Record<string, any>;
  status: string;
  reward_tokens: number | null;
  reward_integral: number | null;
  submitted_at: string;
  reviewed_at: string | null;
  review_notes: string | null;
}

const formFields: Record<string, { key: string; label: string; type: string; required: boolean; placeholder: string }[]> = {
  community: [
    { key: 'name', label: '小区名称', type: 'text', required: true, placeholder: '请输入小区名称' },
    { key: 'address', label: '详细地址', type: 'text', required: true, placeholder: '请输入详细地址' },
    { key: 'city', label: '城市', type: 'text', required: true, placeholder: '如：深圳' },
    { key: 'district', label: '区域', type: 'text', required: false, placeholder: '如：南山区' },
    { key: 'build_year', label: '建成年代', type: 'number', required: false, placeholder: '如：2020' },
    { key: 'developer', label: '开发商', type: 'text', required: false, placeholder: '开发商名称' },
    { key: 'property_company', label: '物业公司', type: 'text', required: false, placeholder: '物业公司名称' },
    { key: 'green_rate', label: '绿化率(%)', type: 'number', required: false, placeholder: '如：30' },
    { key: 'plot_ratio', label: '容积率', type: 'number', required: false, placeholder: '如：2.5' },
  ],
  price: [
    { key: 'community_name', label: '小区名称', type: 'text', required: true, placeholder: '请输入小区名称' },
    { key: 'avg_price', label: '均价(元/㎡)', type: 'number', required: true, placeholder: '如：50000' },
    { key: 'price_date', label: '价格日期', type: 'date', required: true, placeholder: '' },
    { key: 'source', label: '数据来源', type: 'text', required: false, placeholder: '如：链家、贝壳' },
  ],
  house: [
    { key: 'community_name', label: '小区名称', type: 'text', required: true, placeholder: '请输入小区名称' },
    { key: 'layout', label: '户型', type: 'text', required: true, placeholder: '如：3室2厅' },
    { key: 'area', label: '面积(㎡)', type: 'number', required: true, placeholder: '如：120' },
    { key: 'floor', label: '楼层', type: 'text', required: false, placeholder: '如：中层/15楼' },
    { key: 'orientation', label: '朝向', type: 'text', required: false, placeholder: '如：南北通透' },
    { key: 'decoration', label: '装修', type: 'text', required: false, placeholder: '如：精装修' },
    { key: 'price', label: '挂牌价(万)', type: 'number', required: false, placeholder: '如：500' },
  ],
  poi: [
    { key: 'community_name', label: '小区名称', type: 'text', required: true, placeholder: '请输入小区名称' },
    { key: 'poi_type', label: '配套类型', type: 'select', required: true, placeholder: '', options: ['学校', '医院', '地铁', '商场', '公园', '银行', '其他'] },
    { key: 'poi_name', label: '配套名称', type: 'text', required: true, placeholder: '如：深圳湾学校' },
    { key: 'distance', label: '距离(米)', type: 'number', required: false, placeholder: '如：500' },
  ],
};

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [dataTypes, setDataTypes] = useState<DataType[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [stats, setStats] = useState({ total_uploads: 0, pending: 0, approved: 0, total_reward_integral: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [typesRes, uploadsRes, statsRes] = await Promise.all([
        api.get('/uploads/data-types'),
        api.get('/uploads', { params: { limit: 10 } }),
        api.get('/uploads/stats'),
      ]);
      
      setDataTypes(typesRes.data.data_types || []);
      setUploads(uploadsRes.data.uploads || []);
      setStats(statsRes.data);
      
      if (typesRes.data.data_types?.length > 0 && !selectedType) {
        setSelectedType(typesRes.data.data_types[0].id);
      }
    } catch (error) {
      showToast.error('加载数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [selectedType]);

  useEffect(() => {
    loadData();
  }, []);

  const handleTypeChange = (typeId: string) => {
    setSelectedType(typeId);
    setFormData({});
  };

  const handleFieldChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const fields = formFields[selectedType] || [];
    const requiredFields = fields.filter(f => f.required);
    
    for (const field of requiredFields) {
      if (!formData[field.key]) {
        showToast.error(`请填写${field.label}`);
        return;
      }
    }
    
    setIsSubmitting(true);
    try {
      await api.post('/uploads', {
        data_type_id: selectedType,
        raw_data: formData,
      });
      
      showToast.success('数据已提交，等待审核');
      setFormData({});
      await loadData();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'rejected':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
    };
    return labels[status] || status;
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const selectedDataType = dataTypes.find(t => t.id === selectedType);
  const currentFields = formFields[selectedType] || [];

  if (isLoading) {
    return <LoadingCard message="加载中..." />;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <CloudArrowUpIcon className="w-7 h-7 text-primary-600" />
            上传房产数据
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            上传房产数据获取积分奖励，数据审核通过后自动发放
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg px-4 py-2 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400">已获得积分</div>
            <div className="text-lg font-bold text-primary-600 dark:text-primary-400">
              {stats.total_reward_integral.toFixed(2)}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg px-4 py-2 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400">已上传</div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">{stats.total_uploads}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <DocumentTextIcon className="w-5 h-5" />
            数据上传表单
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                数据类型 <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedType}
                onChange={(e) => handleTypeChange(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                {dataTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.display_name} (奖励: {type.base_reward}-{type.max_reward} Token)
                  </option>
                ))}
              </select>
            </div>

            {selectedDataType && (
              <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-3 flex items-start gap-2">
                <InformationCircleIcon className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-primary-700 dark:text-primary-300">
                  <p>基础奖励: {selectedDataType.base_reward} Token ({(selectedDataType.base_reward / 100).toFixed(2)}积分)</p>
                  <p>最高奖励: {selectedDataType.max_reward} Token ({(selectedDataType.max_reward / 100).toFixed(2)}积分)</p>
                  {selectedDataType.description && <p className="mt-1">{selectedDataType.description}</p>}
                </div>
              </div>
            )}

            <div className="border-t border-gray-100 dark:border-gray-700 pt-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">数据详情</h3>
              <div className="space-y-3">
                {currentFields.map(field => (
                  <div key={field.key}>
                    <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                      {field.label} {field.required && <span className="text-red-500">*</span>}
                    </label>
                    {field.type === 'select' ? (
                      <select
                        value={formData[field.key] || ''}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                      >
                        <option value="">请选择</option>
                        {field.options?.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={field.type}
                        value={formData[field.key] || ''}
                        onChange={(e) => handleFieldChange(field.key, field.type === 'number' ? parseFloat(e.target.value) || '' : e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                <CloudArrowUpIcon className="w-5 h-5" />
                {isSubmitting ? '提交中...' : '提交数据'}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <ClockIcon className="w-5 h-5" />
            上传历史
          </h2>

          {uploads.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">暂无上传记录</p>
            </div>
          ) : (
            <div className="space-y-3">
              {uploads.map(upload => (
                <div
                  key={upload.id}
                  className="border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {upload.data_type_name}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusClass(upload.status)}`}>
                      {getStatusLabel(upload.status)}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                    提交时间: {formatTime(upload.submitted_at)}
                  </div>

                  {upload.status === 'approved' && upload.reward_integral && (
                    <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                      <GiftIcon className="w-4 h-4" />
                      获得 {upload.reward_integral.toFixed(2)} 积分
                    </div>
                  )}

                  {upload.status === 'rejected' && upload.review_notes && (
                    <div className="text-sm text-red-600 dark:text-red-400">
                      拒绝原因: {upload.review_notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">奖励规则说明</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {dataTypes.map(type => (
            <div key={type.id} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 dark:text-white">{type.display_name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                基础: {type.base_reward} Token | 最高: {type.max_reward} Token
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                1积分 = 100 Token
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
