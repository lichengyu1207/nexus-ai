import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

interface ReportData {
  id: string
  title: string
  propertyInfo: {
    address: string
    propertyType: string
    area: number
    age: number
  }
  executiveSummary: string
  sections: {
    title: string
    content: string
    dataSources: {
      name: string
      url: string
      timestamp: string
    }[]
  }[]
  createdAt: string
}

const Report: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})

  useEffect(() => {
    // 模拟获取报告数据
    const fetchReport = async () => {
      try {
        // 这里将连接到后端API
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 模拟报告数据
        const mockReport: ReportData = {
          id: reportId || '1',
          title: '上海市浦东新区张江高科技园区房产分析报告',
          propertyInfo: {
            address: '上海市浦东新区张江高科技园区博云路2号',
            propertyType: '公寓',
            area: 89,
            age: 5
          },
          executiveSummary: '本报告对上海市浦东新区张江高科技园区的房产进行了全面分析，包括市场趋势、价格走势、周边配套等多个维度。分析结果显示，该区域房产价值稳定增长，未来潜力较大，但需注意短期市场波动风险。',
          sections: [
            {
              title: '市场趋势分析',
              content: '根据最近12个月的数据，张江高科技园区的房产价格呈现稳中有升的趋势，平均月涨幅为0.8%。与上海市整体市场相比，该区域表现更为强劲，主要受益于科技产业的持续发展和人才流入。',
              dataSources: [
                {
                  name: '上海市房地产交易中心',
                  url: 'https://www.fangdi.com.cn',
                  timestamp: '2026-02-12T10:00:00Z'
                },
                {
                  name: '贝壳找房',
                  url: 'https://www.ke.com',
                  timestamp: '2026-02-12T09:30:00Z'
                }
              ]
            },
            {
              title: '价格走势分析',
              content: '该区域二手房均价为每平方米85,000元，较去年同期上涨12%。新房均价为每平方米92,000元，主要受限于供应不足。租赁市场方面，平均租金为每月每平方米85元，租金回报率约为1.1%。',
              dataSources: [
                {
                  name: '链家',
                  url: 'https://www.lianjia.com',
                  timestamp: '2026-02-12T09:15:00Z'
                },
                {
                  name: '我爱我家',
                  url: 'https://www.5i5j.com',
                  timestamp: '2026-02-12T09:00:00Z'
                }
              ]
            },
            {
              title: '周边配套分析',
              content: '该区域配套设施完善，拥有多个大型购物中心、医院、学校和公园。交通便利，距离最近的地铁站仅500米，有多条公交线路经过。周边教育资源丰富，包括张江高科技园区实验小学和华东师范大学第二附属中学。',
              dataSources: [
                {
                  name: '高德地图',
                  url: 'https://www.amap.com',
                  timestamp: '2026-02-12T08:45:00Z'
                },
                {
                  name: '百度地图',
                  url: 'https://www.map.baidu.com',
                  timestamp: '2026-02-12T08:30:00Z'
                }
              ]
            },
            {
              title: '投资价值评估',
              content: '综合考虑多个因素，该区域房产具有较高的投资价值。长期来看，受益于科技创新中心的定位和持续的人才流入，房产价值有望保持稳定增长。短期来看，需注意市场调控政策的影响和短期波动风险。',
              dataSources: [
                {
                  name: '第一财经',
                  url: 'https://www.yicai.com',
                  timestamp: '2026-02-12T08:15:00Z'
                },
                {
                  name: '新浪财经',
                  url: 'https://finance.sina.com.cn',
                  timestamp: '2026-02-12T08:00:00Z'
                }
              ]
            }
          ],
          createdAt: '2026-02-12T10:30:00Z'
        }
        
        setReport(mockReport)
        
        // 初始化所有章节为展开状态
        const initialExpanded = mockReport.sections.reduce((acc, section) => {
          acc[section.title] = true
          return acc
        }, {} as Record<string, boolean>)
        setExpandedSections(initialExpanded)
      } catch (error) {
        console.error('获取报告失败:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchReport()
  }, [reportId])

  const toggleSection = (title: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [title]: !prev[title]
    }))
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">加载报告中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-96">
          <div className="text-center">
            <h2 className="text-2xl font-medium mb-4">报告不存在</h2>
            <p className="text-gray-600 mb-6">未找到指定的调研报告</p>
            <button
              onClick={() => navigate('/')}
              className="bg-primary hover:bg-primaryDark text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              返回首页
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">{report.title}</h1>
        <button
          onClick={() => navigate('/')}
          className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
        >
          返回首页
        </button>
      </div>

      {/* 房产基本信息 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8 border border-gray-200">
        <h2 className="text-xl font-medium mb-4">房产基本信息</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">地址</p>
            <p className="font-medium">{report.propertyInfo.address}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">房产类型</p>
            <p className="font-medium">{report.propertyInfo.propertyType}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">面积</p>
            <p className="font-medium">{report.propertyInfo.area} 平方米</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">房龄</p>
            <p className="font-medium">{report.propertyInfo.age} 年</p>
          </div>
        </div>
      </div>

      {/* 执行摘要 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8 border border-gray-200">
        <h2 className="text-xl font-medium mb-4">执行摘要</h2>
        <p className="text-gray-700 leading-relaxed">{report.executiveSummary}</p>
      </div>

      {/* 报告章节 */}
      <div className="space-y-6">
        {report.sections.map((section, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md border border-gray-200">
            <div 
              className="p-6 cursor-pointer flex justify-between items-center"
              onClick={() => toggleSection(section.title)}
            >
              <h3 className="text-lg font-medium">{section.title}</h3>
              <span className="text-gray-500">
                {expandedSections[section.title] ? '▼' : '▶'}
              </span>
            </div>
            
            {expandedSections[section.title] && (
              <div className="p-6 pt-0 border-t border-gray-100">
                <p className="text-gray-700 leading-relaxed mb-6">{section.content}</p>
                
                {/* 数据溯源 */}
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-500 mb-3">数据来源</h4>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <ul className="space-y-2">
                      {section.dataSources.map((source, sourceIndex) => (
                        <li key={sourceIndex} className="flex flex-col">
                          <div className="flex justify-between items-center">
                            <a 
                              href={source.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-primary hover:underline font-medium"
                            >
                              {source.name}
                            </a>
                            <span className="text-xs text-gray-500">
                              {new Date(source.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <a 
                            href={source.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-xs text-gray-500 mt-1"
                          >
                            {source.url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 报告元信息 */}
      <div className="mt-12 bg-gray-50 p-6 rounded-lg border border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-500">报告生成时间</p>
            <p className="text-gray-700">{new Date(report.createdAt).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">报告ID</p>
            <p className="text-gray-700">{report.id}</p>
          </div>
          <div>
            <button
              className="bg-primary hover:bg-primaryDark text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              下载PDF报告
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Report