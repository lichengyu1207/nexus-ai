import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';

const SitemapPage: React.FC = () => {
  return (
    <div className="min-h-screen py-12">
      <Helmet>
        <title>站点地图 - 房都督AI</title>
        <meta name="description" content="房都督AI站点地图，快速了解网站所有页面和功能" />
      </Helmet>

      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-text-primary mb-8">站点地图</h1>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* 主要功能 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">主要功能</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/" className="text-accent-gold hover:underline">
                  首页
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className="text-accent-gold hover:underline">
                  控制台
                </Link>
              </li>
              <li>
                <Link to="/tasks" className="text-accent-gold hover:underline">
                  任务中心
                </Link>
              </li>
              <li>
                <Link to="/compare" className="text-accent-gold hover:underline">
                  房源对比
                </Link>
              </li>
              <li>
                <Link to="/reports" className="text-accent-gold hover:underline">
                  报告列表
                </Link>
              </li>
            </ul>
          </div>

          {/* 智能体功能 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">智能体功能</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/agents" className="text-accent-gold hover:underline">
                  智能体仪表盘
                </Link>
              </li>
              <li>
                <Link to="/functional-integration" className="text-accent-gold hover:underline">
                  功能级融合平台
                </Link>
              </li>
              <li>
                <Link to="/counterstrike" className="text-accent-gold hover:underline">
                  反击系统
                </Link>
              </li>
              <li>
                <Link to="/evolution" className="text-accent-gold hover:underline">
                  进化系统
                </Link>
              </li>
              <li>
                <Link to="/cognition" className="text-accent-gold hover:underline">
                  认知面板
                </Link>
              </li>
            </ul>
          </div>

          {/* 团队与人才 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">团队与人才</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/teams" className="text-accent-gold hover:underline">
                  团队管理
                </Link>
              </li>
              <li>
                <Link to="/talent-market" className="text-accent-gold hover:underline">
                  人才市场
                </Link>
              </li>
              <li>
                <Link to="/recruit" className="text-accent-gold hover:underline">
                  招聘中心
                </Link>
              </li>
              <li>
                <Link to="/auto-work" className="text-accent-gold hover:underline">
                  自动工作
                </Link>
              </li>
            </ul>
          </div>

          {/* 数据与分析 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">数据与分析</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/data-engineering" className="text-accent-gold hover:underline">
                  数据工程
                </Link>
              </li>
              <li>
                <Link to="/fullchain" className="text-accent-gold hover:underline">
                  全链路追踪
                </Link>
              </li>
              <li>
                <Link to="/memory" className="text-accent-gold hover:underline">
                  记忆系统
                </Link>
              </li>
              <li>
                <Link to="/habits" className="text-accent-gold hover:underline">
                  习惯分析
                </Link>
              </li>
            </ul>
          </div>

          {/* IP计划 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">IP达人计划</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/ip-apply" className="text-accent-gold hover:underline">
                  IP申请
                </Link>
              </li>
              <li>
                <Link to="/ip" className="text-accent-gold hover:underline">
                  IP仪表盘
                </Link>
              </li>
              <li>
                <Link to="/ip/links" className="text-accent-gold hover:underline">
                  推广链接
                </Link>
              </li>
              <li>
                <Link to="/ip/commissions" className="text-accent-gold hover:underline">
                  佣金记录
                </Link>
              </li>
              <li>
                <Link to="/ip/withdraw" className="text-accent-gold hover:underline">
                  提现管理
                </Link>
              </li>
            </ul>
          </div>

          {/* 帮助与支持 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">帮助与支持</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/help" className="text-accent-gold hover:underline">
                  帮助中心
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-accent-gold hover:underline">
                  关于我们
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-accent-gold hover:underline">
                  联系我们
                </Link>
              </li>
              <li>
                <Link to="/feedback" className="text-accent-gold hover:underline">
                  意见反馈
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-accent-gold hover:underline">
                  隐私政策
                </Link>
              </li>
            </ul>
          </div>

          {/* 用户中心 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">用户中心</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/login" className="text-accent-gold hover:underline">
                  登录
                </Link>
              </li>
              <li>
                <Link to="/register" className="text-accent-gold hover:underline">
                  注册
                </Link>
              </li>
              <li>
                <Link to="/profile" className="text-accent-gold hover:underline">
                  个人资料
                </Link>
              </li>
              <li>
                <Link to="/settings" className="text-accent-gold hover:underline">
                  设置
                </Link>
              </li>
              <li>
                <Link to="/integral" className="text-accent-gold hover:underline">
                  积分中心
                </Link>
              </li>
            </ul>
          </div>

          {/* 其他功能 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">其他功能</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/consult" className="text-accent-gold hover:underline">
                  咨询服务
                </Link>
              </li>
              <li>
                <Link to="/upload" className="text-accent-gold hover:underline">
                  文件上传
                </Link>
              </li>
              <li>
                <Link to="/notifications" className="text-accent-gold hover:underline">
                  通知中心
                </Link>
              </li>
              <li>
                <Link to="/search" className="text-accent-gold hover:underline">
                  搜索
                </Link>
              </li>
            </ul>
          </div>

          {/* 高级功能 */}
          <div className="bg-bg-secondary rounded-lg p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">高级功能</h2>
            <ul className="space-y-3">
              <li>
                <Link to="/ecosystem" className="text-accent-gold hover:underline">
                  生态系统
                </Link>
              </li>
              <li>
                <Link to="/five-end" className="text-accent-gold hover:underline">
                  五端系统
                </Link>
              </li>
              <li>
                <Link to="/governance" className="text-accent-gold hover:underline">
                  治理系统
                </Link>
              </li>
              <li>
                <Link to="/learning" className="text-accent-gold hover:underline">
                  学习系统
                </Link>
              </li>
              <li>
                <Link to="/market" className="text-accent-gold hover:underline">
                  市场
                </Link>
              </li>
              <li>
                <Link to="/skills" className="text-accent-gold hover:underline">
                  技能
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 bg-bg-secondary rounded-lg p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">关于站点地图</h2>
          <p className="text-text-secondary">
            站点地图列出了房都督AI平台的所有主要页面和功能。您可以通过此页面快速了解网站结构，
            并找到您需要的功能。如果您有任何问题或建议，欢迎通过
            <Link to="/contact" className="text-accent-gold hover:underline">
              联系我们
            </Link>
            页面与我们取得联系。
          </p>
        </div>
      </div>
    </div>
  );
};

export default SitemapPage;
