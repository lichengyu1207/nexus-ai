import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheckIcon,
  DocumentTextIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';

const AuditComplianceHelp: React.FC = () => {
  const [openSection, setOpenSection] = useState<string | null>('overview');

  const toggleSection = (section: string) => {
    setOpenSection(openSection === section ? null : section);
  };

  const sections = [
    {
      id: 'overview',
      title: '审计系统概述',
      icon: ShieldCheckIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            房都督AI平台审计系统是一个全面的日志记录和监控解决方案，旨在确保平台操作的可追溯性、安全性和合规性。
          </p>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">审计范围</h4>
            <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li>• 用户认证操作（登录、登出、密码修改）</li>
              <li>• 任务管理操作（创建、查看、更新、删除）</li>
              <li>• 报告操作（生成、导出、分享）</li>
              <li>• 管理员操作（用户管理、系统配置）</li>
              <li>• 数据访问和导出操作</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: 'retention',
      title: '日志保留政策',
      icon: ClockIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            平台遵循严格的日志保留政策，确保满足监管要求：
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="px-4 py-2 text-left">日志类型</th>
                <th className="px-4 py-2 text-left">保留期限</th>
                <th className="px-4 py-2 text-left">存储方式</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
              <tr>
                <td className="px-4 py-2">在线日志</td>
                <td className="px-4 py-2">150天</td>
                <td className="px-4 py-2">主数据库</td>
              </tr>
              <tr>
                <td className="px-4 py-2">归档日志</td>
                <td className="px-4 py-2">180天（可延长）</td>
                <td className="px-4 py-2">加密压缩文件</td>
              </tr>
              <tr>
                <td className="px-4 py-2">安全事件日志</td>
                <td className="px-4 py-2">365天</td>
                <td className="px-4 py-2">独立存储</td>
              </tr>
            </tbody>
          </table>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              <strong>注意：</strong>超过保留期限的日志将自动归档并从主数据库移除。归档文件可通过管理员界面恢复。
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 'query',
      title: '查询与导出',
      icon: DocumentTextIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            超级管理员可以通过审计日志管理页面进行多维查询和导出：
          </p>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">筛选条件</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  支持按时间范围、用户、操作类型、资源类型、状态、IP地址等条件筛选
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">排序选项</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  支持按时间、用户、操作类型、状态等字段排序
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">导出格式</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  支持CSV和JSON两种格式导出，包含完整日志信息
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">合规报告</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  可生成PDF格式的合规审计报告，包含统计摘要和日志明细
                </p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'integrity',
      title: '数据完整性保障',
      icon: ShieldCheckIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            审计日志采用哈希链技术确保数据不可篡改：
          </p>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">哈希链机制</h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li>• 每条日志记录包含唯一的SHA-256哈希值</li>
              <li>• 每条日志的哈希依赖于前一条日志的哈希</li>
              <li>• 任何修改都会导致后续所有日志的哈希验证失败</li>
              <li>• 定期对日志批次进行数字签名</li>
            </ul>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">验证功能</h4>
            <p className="text-sm text-green-700 dark:text-green-300">
              管理员可随时执行完整性验证，系统将检查所有日志的哈希链连续性，并生成完整性评分报告。
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 'alerts',
      title: '异常行为检测',
      icon: ExclamationTriangleIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            系统自动检测可疑行为并生成告警：
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="px-4 py-2 text-left">检测类型</th>
                <th className="px-4 py-2 text-left">触发条件</th>
                <th className="px-4 py-2 text-left">严重级别</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
              <tr>
                <td className="px-4 py-2">暴力破解</td>
                <td className="px-4 py-2">5分钟内5次登录失败</td>
                <td className="px-4 py-2"><span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">高</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">批量删除</td>
                <td className="px-4 py-2">10分钟内10次删除操作</td>
                <td className="px-4 py-2"><span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">高</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">权限提升</td>
                <td className="px-4 py-2">普通用户尝试特权操作</td>
                <td className="px-4 py-2"><span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">严重</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">批量导出</td>
                <td className="px-4 py-2">30分钟内20次导出</td>
                <td className="px-4 py-2"><span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">高</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">多IP登录</td>
                <td className="px-4 py-2">短时间多IP登录同一账号</td>
                <td className="px-4 py-2"><span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">高</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      ),
    },
    {
      id: 'compliance',
      title: '合规要求满足',
      icon: DocumentTextIcon,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            审计系统满足以下合规要求：
          </p>
          <div className="space-y-3">
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white">《网络安全法》</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                日志留存不少于6个月，支持追溯和审计
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white">《数据安全法》</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                数据操作全程记录，支持数据访问审计
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white">《个人信息保护法》</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                个人信息处理活动可追溯，支持隐私合规审计
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white">等级保护要求</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                满足等保三级审计要求，支持安全审计报告生成
              </p>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <ShieldCheckIcon className="w-8 h-8 text-primary-600" />
          合规审计系统
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          了解房都督AI平台的审计日志管理、合规要求和数据安全措施
        </p>
      </motion.div>

      <div className="space-y-4">
        {sections.map((section) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <section.icon className="w-5 h-5 text-primary-600" />
                <span className="font-medium text-gray-900 dark:text-white">
                  {section.title}
                </span>
              </div>
              <ChevronDownIcon
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  openSection === section.id ? 'rotate-180' : ''
                }`}
              />
            </button>
            {openSection === section.id && (
              <div className="px-6 pb-4">
                {section.content}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-8 bg-primary-50 dark:bg-primary-900/20 rounded-xl p-6"
      >
        <h3 className="font-semibold text-primary-800 dark:text-primary-200 mb-2">
          需要更多帮助？
        </h3>
        <p className="text-sm text-primary-700 dark:text-primary-300">
          如有合规相关问题，请联系我们的合规团队：
          <a href="mailto:compliance@fangtan.ai" className="underline ml-1">
            compliance@fangtan.ai
          </a>
        </p>
      </motion.div>
    </div>
  );
};

export default AuditComplianceHelp;
