import React from 'react';
import { Link } from 'react-router-dom';

const TermsPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="bg-white rounded-lg shadow p-8">
        <h1 className="text-3xl font-bold mb-6">服务条款</h1>
        <p className="text-gray-500 mb-4">最后更新：2024年1月1日</p>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">1. 服务说明</h2>
          <p className="mb-4">
            房都督AI是一个房产分析平台，为用户提供房产信息分析服务。使用本服务即表示您同意遵守以下条款。
          </p>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">2. 用户账户</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>您需要注册账户才能使用完整服务</li>
            <li>您有责任保护账户安全</li>
            <li>禁止共享账户或转让账户</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">3. 服务内容</h2>
          <p className="mb-4">
            我们提供以下服务：
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>房产信息分析</li>
            <li>市场价值评估</li>
            <li>投资建议参考</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">4. 免责声明</h2>
          <p className="mb-4">
            本服务提供的分析结果仅供参考，不构成投资建议。实际投资决策请咨询专业人士。
          </p>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">5. 付费服务</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>积分用于支付分析服务</li>
            <li>充值后积分不可退款</li>
            <li>价格可能随时调整</li>
          </ul>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">6. 知识产权</h2>
          <p className="mb-4">
            平台内容的知识产权归房都督AI所有。未经许可不得复制、传播或用于商业目的。
          </p>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">7. 服务变更</h2>
          <p className="mb-4">
            我们保留随时修改或终止服务的权利。重大变更将提前通知用户。
          </p>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">8. 争议解决</h2>
          <p className="mb-4">
            如有争议，双方应友好协商解决。协商不成的，可向有管辖权的法院提起诉讼。
          </p>
        </div>

        <div className="prose max-w-none">
          <h2 className="text-xl font-semibold mb-4">9. 联系方式</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>邮箱：support@fangtan.ai</li>
            <li>微信：fangtan_ai</li>
          </ul>
        </div>

        <div className="mt-8 pt-6 border-t text-center">
          <p className="text-gray-500">
            注册即表示您同意以上条款。如有疑问请{' '}
            <Link to="/help" className="text-primary hover:underline">
              联系客服
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;
