import React from 'react';
import { Link } from 'react-router-dom';

const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="bg-white rounded-lg shadow p-8">
        <h1 className="text-3xl font-bold mb-6">隐私政策</h1>
        <p className="text-gray-500 mb-4">最后更新：2024年1月1日</p>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">1. 信息收集</h2>
          <p className="mb-4">
            我们收集您在使用服务时提供的以下信息：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>注册信息：邮箱、用户名、密码</li>
            <li>使用数据：分析记录、报告查询历史</li>
            <li>支付信息：充值记录（不包含支付密码）</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">2. 信息使用</h2>
          <p className="mb-4">
            您的信息将用于：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>提供房产分析服务</li>
            <li>生成个性化报告</li>
            <li>改善服务质量</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">3. 信息保护</h2>
          <p className="mb-4">
            我们采取以下措施保护您的信息：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>数据加密存储</li>
            <li>访问权限控制</li>
            <li>定期安全审计</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">4. 信息共享</h2>
          <p className="mb-4">
            我们不会向第三方分享您的个人信息，除非：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>获得您的明确同意</li>
            <li>法律法规要求</li>
            <li>保护我们的权利</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">5. Cookie 使用</h2>
          <p className="mb-4">
            我们使用 Cookie 来：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>保持登录状态</li>
            <li>记住用户偏好</li>
            <li>分析网站使用情况</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">6. 您的权利</h2>
          <p className="mb-4">
            根据相关法律法规，您享有以下权利：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>访问和获取您的个人数据</li>
            <li>更正不准确的信息</li>
            <li>删除您的账户和数据</li>
            <li>撤回同意</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">7. 联系我们</h2>
          <p className="mb-4">
            如果您对隐私政策有任何疑问，请通过以下方式联系我们：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>邮箱：privacy@fangtan.ai</li>
            <li>微信：fangtan_ai</li>
          </ul>
        </div>

        <div className="mt-8 pt-6 border-t text-center">
          <p className="text-gray-500">
            如有任何问题，请{' '}
            <Link to="/help" className="text-primary hover:underline">
              联系客服
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;
