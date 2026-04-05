import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface ValuationData {
  id: string
  propertyInfo: {
    address: string
    propertyType: string
    area: number
    age: number
  }
  valuation: {
    total: number
    currency: string
    unit: string
    confidence: number
    confidenceInterval: {
      min: number
      max: number
    }
    breakdown: {
      location: number
      layout: number
      market: number
    }
  }
  factors: {
    name: string
    weight: number
    value: number
  }[]
  agentAnalysis: {
    name: string
    avatar: string
    analysis: string
    suggestions: string[]
  }
  reasoning: {
    location: string[]
    layout: string[]
    market: string[]
  }
  createdAt: string
}

const ValuationReport: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>()
  const navigate = useNavigate()
  const [valuation, setValuation] = useState<ValuationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showReasoning, setShowReasoning] = useState(false)

  useEffect(() => {
    // 模拟获取估价报告数据
    const fetchValuation = async () => {
      try {
        // 这里将连接到后端API
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 模拟估价报告数据
        const mockValuation: ValuationData = {
          id: reportId || '1',
          propertyInfo: {
            address: '深圳市南山区科技园',
            propertyType: '公寓',
            area: 120,
            age: 10
          },
          valuation: {
            total: 60319.47,
            currency: 'CNY',
            unit: '元/㎡',
            confidence: 0.85,
            confidenceInterval: {
              min: 58000,
              max: 62000
            },
            breakdown: {
              location: 60000.00,
              layout: 66000.00,
              market: 55290.00
            }
          },
          factors: [
            { name: '区位因素', weight: 0.35, value: 85 },
            { name: '户型结构', weight: 0.30, value: 90 },
            { name: '市场趋势', weight: 0.20, value: 75 },
            { name: '配套设施', weight: 0.10, value: 80 },
            { name: '交通便利', weight: 0.05, value: 95 }
          ],
          agentAnalysis: {
            name: '周瑜',
            avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=portrait%20of%20Zhou%20Yu%20ancient%20Chinese%20general%20serious%20expression&image_size=square',
            analysis: '综合考虑区位、户型和市场因素，该房产估值合理。区位优势明显，交通便利，周边配套完善，这些因素都对房产价值形成了有力支撑。',
            suggestions: [
              '建议进一步考察周边环境和市场趋势',
              '可考虑在市场稳定时入手',
              '关注区域规划和未来发展潜力'
            ]
          },
          reasoning: {
            location: [
              '南山区科技园是深圳市的核心科技区域，具有较高的发展潜力',
              '周边有多条地铁线路，交通便利',
              '配套设施完善，有多个大型购物中心和医院',
              '教育资源丰富，有多所优质学校'
            ],
            layout: [
              '120平方米的三居室布局合理，满足家庭居住需求',
              '南北通透，采光良好',
              '楼层适中，视野开阔',
              '装修状况良好，可直接入住'
            ],
            market: [
              '近期南山区房价保持稳定增长趋势',
              '科技园区域需求旺盛，供应量有限',
              '周边同类房源成交价格在合理范围内',
              '政策环境对房地产市场形成一定支撑'
            ]
          },
          createdAt: new Date().toISOString()
        }
        
        setValuation(mockValuation)
      } catch (error) {
        console.error('获取估价报告失败:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchValuation()
  }, [reportId])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">加载估价报告中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!valuation) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-96">
          <div className="text-center">
            <h2 className="text-2xl font-medium mb-4">报告不存在</h2>
            <p className="text-gray-600 mb-6">未找到指定的估价报告</p>
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

  // 准备雷达图数据
  const radarData = valuation.factors.map(factor => ({
    name: factor.name,
    因素权重: factor.weight * 100,
    因素评分: factor.value
  }))

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">房产估价报告</h1>
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
            <p className="font-medium">{valuation.propertyInfo.address}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">房产类型</p>
            <p className="font-medium">{valuation.propertyInfo.propertyType}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">面积</p>
            <p className="font-medium">{valuation.propertyInfo.area} 平方米</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-500">房龄</p>
            <p className="font-medium">{valuation.propertyInfo.age} 年</p>
          </div>
        </div>
      </div>

      {/* 估价报告主体 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* 左侧：估价结果卡片 */}
        <div className="lg:col-span-4">
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 h-full">
            <h2 className="text-xl font-medium mb-6">估价结果</h2>
            
            <div className="text-center mb-8">
              <div className="text-4xl font-bold text-primary mb-2">
                {valuation.valuation.total.toLocaleString()}
              </div>
              <div className="text-gray-600">
                {valuation.valuation.currency} {valuation.valuation.unit}
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">置信区间</h3>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">{valuation.valuation.confidenceInterval.min.toLocaleString()} 元/㎡</span>
                <span className="text-gray-700">{valuation.valuation.confidenceInterval.max.toLocaleString()} 元/㎡</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: '85%' }}
                ></div>
              </div>
              <div className="text-right text-sm text-gray-500 mt-1">
                置信度: {Math.round(valuation.valuation.confidence * 100)}%
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">估价明细</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">区位因素</span>
                  <span className="font-medium">{valuation.valuation.breakdown.location.toLocaleString()} 元/㎡</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">户型结构</span>
                  <span className="font-medium">{valuation.valuation.breakdown.layout.toLocaleString()} 元/㎡</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">市场趋势</span>
                  <span className="font-medium">{valuation.valuation.breakdown.market.toLocaleString()} 元/㎡</span>
                </div>
              </div>
            </div>
            
            <div className="mt-8">
              <button
                onClick={() => setShowReasoning(!showReasoning)}
                className="w-full bg-primary hover:bg-primaryDark text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                {showReasoning ? '隐藏详情' : '查看详情'}
              </button>
            </div>
            
            {showReasoning && (
              <div className="mt-6 p-4 bg-gray-50 rounded-md">
                <h3 className="text-sm font-medium text-gray-500 mb-3">智能体推理过程</h3>
                
                <div className="mb-4">
                  <h4 className="font-medium text-gray-700 mb-2">区位因素推理</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {valuation.reasoning.location.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="mb-4">
                  <h4 className="font-medium text-gray-700 mb-2">户型结构推理</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {valuation.reasoning.layout.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">市场趋势推理</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {valuation.reasoning.market.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 中间：影响因素分析图 */}
        <div className="lg:col-span-4">
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 h-full">
            <h2 className="text-xl font-medium mb-6">影响因素分析</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart outerRadius={90} data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="name" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar name="因素权重" dataKey="因素权重" stroke="#36a2eb" fill="#36a2eb" fillOpacity={0.2} />
                  <Radar name="因素评分" dataKey="因素评分" stroke="#ff6384" fill="#ff6384" fillOpacity={0.2} />
                  <Legend />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-500 mb-3">因素权重说明</h3>
              <div className="space-y-2">
                {valuation.factors.map((factor, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-700">{factor.name}</span>
                    <span className="font-medium">{Math.round(factor.weight * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 右侧：智能体互动区域 */}
        <div className="lg:col-span-4">
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 h-full">
            <h2 className="text-xl font-medium mb-6">智能体分析</h2>
            
            <div className="flex items-center mb-6">
              <img 
                src={valuation.agentAnalysis.avatar} 
                alt={valuation.agentAnalysis.name} 
                className="w-16 h-16 rounded-full object-cover mr-4"
              />
              <div>
                <h3 className="text-lg font-medium">{valuation.agentAnalysis.name}</h3>
                <p className="text-sm text-gray-500">智能估价分析师</p>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md mb-6">
              <p className="text-gray-700">{valuation.agentAnalysis.analysis}</p>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">建议</h3>
              <ul className="space-y-2">
                {valuation.agentAnalysis.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-primary mr-2">•</span>
                    <span className="text-gray-700">{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 报告元信息 */}
      <div className="mt-8 bg-gray-50 p-6 rounded-lg border border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-500">报告生成时间</p>
            <p className="text-gray-700">{new Date(valuation.createdAt).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">报告ID</p>
            <p className="text-gray-700">{valuation.id}</p>
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

export default ValuationReport
