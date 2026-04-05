import React, { useState } from 'react';

interface FAQ {
  question: string;
  answer: string;
  category: string;
}

interface Category {
  id: string;
  name: string;
  icon: string;
}

const categories: Category[] = [
  { id: 'all', name: '全部', icon: '📋' },
  { id: 'getting-started', name: '入门指南', icon: '🚀' },
  { id: 'pricing', name: '积分与定价', icon: '💰' },
  { id: 'analysis', name: '房产分析', icon: '🏠' },
  { id: 'account', name: '账户相关', icon: '👤' },
  { id: 'other', name: '其他问题', icon: '❓' },
];

const faqs: FAQ[] = [
  {
    category: 'getting-started',
    question: '房都督AI是什么？',
    answer: '房都督AI是一个智能房产分析与估值平台，利用多智能体协同技术，为您提供专业的房产分析报告。只需输入房产地址，3分钟即可获得详细的分析报告。',
  },
  {
    category: 'getting-started',
    question: '如何开始使用？',
    answer: '1. 注册账号并登录\n2. 新用户赠送3积分\n3. 在首页或仪表盘输入房产地址\n4. 点击"开始分析"即可获得报告',
  },
  {
    category: 'pricing',
    question: '积分如何计算？',
    answer: '每次房产分析消耗1积分，对比分析消耗2积分。积分可通过充值获得，也可通过邀请好友获得奖励积分。',
  },
  {
    category: 'pricing',
    question: '如何充值积分？',
    answer: '在"积分充值"页面选择套餐，通过微信转账完成支付，填写转账单号提交申请，管理员审核后积分自动到账。',
  },
  {
    category: 'analysis',
    question: '分析报告包含哪些内容？',
    answer: '报告包含：\n• 房产基本信息\n• 区域市场分析\n• 价格估值\n• 投资建议\n• 风险提示\n• 周边配套设施分析',
  },
  {
    category: 'analysis',
    question: '分析结果准确吗？',
    answer: '我们的分析基于公开数据和AI算法，提供参考性建议。实际交易请以专业评估机构意见为准。我们会持续优化算法提高准确度。',
  },
  {
    category: 'account',
    question: '如何修改密码？',
    answer: '进入"账户设置"页面，在"修改密码"区域填写当前密码和新密码，点击"修改密码"按钮即可。',
  },
  {
    category: 'account',
    question: '忘记密码怎么办？',
    answer: '在登录页面点击"忘记密码"，输入注册邮箱，系统会发送重置密码链接到您的邮箱。',
  },
  {
    category: 'other',
    question: '如何联系客服？',
    answer: '您可以通过以下方式联系我们：\n• 微信：fangtan_ai\n• 邮箱：support@fangtan.ai\n• 在线反馈：点击页面右下角的反馈按钮',
  },
  {
    category: 'other',
    question: '数据安全吗？',
    answer: '我们采用银行级数据加密技术，您的个人信息和查询记录都受到严格保护。我们不会向第三方泄露任何用户数据。',
  },
];

const HelpPage: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState({
    type: 'question',
    title: '',
    content: '',
    email: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const filteredFAQs = faqs.filter(faq => {
    const matchCategory = activeCategory === 'all' || faq.category === activeCategory;
    const matchSearch = searchQuery === '' || 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  const handleSubmitFeedback = async () => {
    if (!feedbackForm.title || !feedbackForm.content) {
      alert('请填写完整信息');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers,
        body: JSON.stringify(feedbackForm),
      });

      if (response.ok) {
        alert('感谢您的反馈，我们会尽快处理');
        setShowFeedbackModal(false);
        setFeedbackForm({ type: 'question', title: '', content: '', email: '' });
      } else {
        const error = await response.json();
        alert(error.detail || '提交失败');
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-center mb-8">帮助中心</h1>
      
      {/* 搜索框 */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="max-w-xl mx-auto">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索问题..."
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
      </div>
      
      {/* 分类标签 */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-2 rounded-full flex items-center gap-2 transition-colors ${
              activeCategory === cat.id
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
          </button>
        ))}
      </div>
      
      {/* FAQ列表 */}
      <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
        {filteredFAQs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            没有找到相关问题
          </div>
        ) : (
          <div className="divide-y">
            {filteredFAQs.map((faq, index) => (
              <div key={index} className="border-b last:border-b-0">
                <button
                  onClick={() => setExpandedFAQ(expandedFAQ === index ? null : index)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50"
                >
                  <span className="font-medium">{faq.question}</span>
                  <span className={`transform transition-transform ${expandedFAQ === index ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </button>
                {expandedFAQ === index && (
                  <div className="px-6 pb-4 text-gray-600 whitespace-pre-line">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 联系我们 */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-medium mb-4">联系我们</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-3xl mb-2">💬</div>
            <h3 className="font-medium">微信客服</h3>
            <p className="text-sm text-gray-500">fangtan_ai</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-3xl mb-2">📧</div>
            <h3 className="font-medium">邮箱</h3>
            <p className="text-sm text-gray-500">support@fangtan.ai</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-100"
               onClick={() => setShowFeedbackModal(true)}>
            <div className="text-3xl mb-2">📝</div>
            <h3 className="font-medium">在线反馈</h3>
            <p className="text-sm text-gray-500">提交问题或建议</p>
          </div>
        </div>
      </div>
      
      {/* 快速链接 */}
      <div className="bg-gradient-to-r from-primary to-blue-600 rounded-lg shadow p-6 text-white">
        <h2 className="text-lg font-medium mb-4">还没找到答案？</h2>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => setShowFeedbackModal(true)}
            className="bg-white text-primary px-6 py-2 rounded-lg font-medium hover:bg-gray-100"
          >
            提交反馈
          </button>
          <a
            href="https://mp.weixin.qq.com"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white/20 text-white px-6 py-2 rounded-lg font-medium hover:bg-white/30"
          >
            关注公众号
          </a>
        </div>
      </div>
      
      {/* 反馈弹窗 */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">提交反馈</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                <select
                  value={feedbackForm.type}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, type: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="question">问题咨询</option>
                  <option value="feature">功能建议</option>
                  <option value="bug">Bug报告</option>
                  <option value="complaint">投诉</option>
                  <option value="other">其他</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                <input
                  type="text"
                  value={feedbackForm.title}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, title: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="简要描述您的问题"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">详细内容</label>
                <textarea
                  value={feedbackForm.content}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, content: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={4}
                  placeholder="请详细描述您的问题或建议..."
                />
              </div>
              
              {!localStorage.getItem('token') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">联系邮箱</label>
                  <input
                    type="email"
                    value={feedbackForm.email}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, email: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                    placeholder="您的邮箱地址"
                  />
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleSubmitFeedback}
                disabled={submitting}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
              >
                {submitting ? '提交中...' : '提交反馈'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HelpPage;
