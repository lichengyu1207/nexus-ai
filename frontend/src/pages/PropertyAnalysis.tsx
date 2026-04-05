import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const PropertyAnalysis: React.FC = () => {
  const navigate = useNavigate()
  const [activeMode, setActiveMode] = useState<'form' | 'natural'>('form')
  const [formData, setFormData] = useState({
    address: '',
    propertyType: '',
    area: '',
    age: '',
    description: ''
  })
  const [naturalQuery, setNaturalQuery] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    try {
      let requestBody = {}
      
      if (activeMode === 'natural') {
        // 自然语言查询模式
        const query = naturalQuery.trim()
        
        // 判断是否只输入了小区名（简单判断：长度较短且不包含数字和特殊字符）
        const isSimpleCommunityName = query.length <= 20 && 
          !query.includes('市') && 
          !query.includes('区') && 
          !query.includes('号') &&
          !query.includes('单元') &&
          !query.includes('室') &&
          !query.includes('平米') &&
          !query.includes('平方米')
        
        if (isSimpleCommunityName) {
          // 只输入了小区名，自动补全为标准格式
          requestBody = {
            query: `分析${query}的房产价值`,
            address: query
          }
        } else {
          // 完整的自然语言查询
          requestBody = {
            query: query
          }
        }
      } else {
        // 结构化表单模式
        requestBody = {
          query: `分析${formData.address}的房产价值`,
          address: formData.address,
          property_type: formData.propertyType,
          area: formData.area ? parseFloat(formData.area) : undefined,
          age: formData.age ? parseInt(formData.age) : undefined,
          description: formData.description
        }
      }
      
      console.log('提交数据:', requestBody)
      
      // 调用后端API创建任务
      const response = await fetch('http://localhost:8000/api/v1/tasks/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('任务创建成功:', data)
        
        // 使用真实的task_id跳转到虚拟办公室
        navigate(`/virtual-office/${data.task_id}`)
      } else {
        console.error('任务创建失败:', response.status)
        alert('任务创建失败，请检查后端服务是否正常运行')
      }
    } catch (error) {
      console.error('提交失败:', error)
      alert('提交失败，请检查网络连接')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">房产分析</h1>
      
      {/* 双模式切换 */}
      <div className="flex justify-center mb-8">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            className={`px-6 py-2 text-sm font-medium ${activeMode === 'form' ? 'bg-primary text-white' : 'bg-white text-gray-700 hover:bg-gray-100'} rounded-l-lg border border-gray-200`}
            onClick={() => setActiveMode('form')}
          >
            结构化表单
          </button>
          <button
            type="button"
            className={`px-6 py-2 text-sm font-medium ${activeMode === 'natural' ? 'bg-primary text-white' : 'bg-white text-gray-700 hover:bg-gray-100'} rounded-r-lg border border-gray-200`}
            onClick={() => setActiveMode('natural')}
          >
            自然语言查询
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
        {activeMode === 'form' ? (
          <div className="space-y-6">
            <div>
              <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
                地址
              </label>
              <input
                type="text"
                id="address"
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                placeholder="请输入详细地址"
                required
              />
            </div>

            <div>
              <label htmlFor="propertyType" className="block text-sm font-medium text-gray-700 mb-1">
                房产类型
              </label>
              <select
                id="propertyType"
                name="propertyType"
                value={formData.propertyType}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                required
              >
                <option value="">请选择房产类型</option>
                <option value="apartment">公寓</option>
                <option value="house">别墅</option>
                <option value="townhouse">联排别墅</option>
                <option value="commercial">商业地产</option>
                <option value="other">其他</option>
              </select>
            </div>

            <div>
              <label htmlFor="area" className="block text-sm font-medium text-gray-700 mb-1">
                面积 (平方米)
              </label>
              <input
                type="number"
                id="area"
                name="area"
                value={formData.area}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                placeholder="请输入面积"
                min="1"
                step="0.1"
                required
              />
            </div>

            <div>
              <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-1">
                房龄 (年)
              </label>
              <input
                type="number"
                id="age"
                name="age"
                value={formData.age}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                placeholder="请输入房龄"
                min="0"
                step="1"
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                placeholder="请输入房产描述（可选）"
                rows={4}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <label htmlFor="naturalQuery" className="block text-sm font-medium text-gray-700 mb-1">
                自然语言查询
              </label>
              <textarea
                id="naturalQuery"
                value={naturalQuery}
                onChange={(e) => setNaturalQuery(e.target.value)}
                className="w-full px-4 py-4 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
                placeholder="支持多种输入方式：&#10;• 只输入小区名：小堰堤社区&#10;• 输入地址：泰安市高铁南片区小堰堤社区5号楼2单元2202室&#10;• 详细描述：帮我分析上海市浦东新区张江高科技园区的一套89平米的两居室公寓，房龄5年"
                rows={6}
                required
              />
              <p className="text-sm text-gray-500 mt-2">
                💡 提示：您可以只输入小区名称，系统会自动识别并启动分析
              </p>
            </div>
          </div>
        )}

        <div className="mt-8">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-primary hover:bg-primaryDark text-white font-medium py-3 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? '分析中...' : '开始分析'}
          </button>
        </div>
      </form>

      <div className="mt-12 bg-gray-50 p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-medium mb-4">为什么选择房都督AI？</h3>
        <ul className="space-y-2 text-gray-700">
          <li className="flex items-start">
            <span className="text-primary mr-2">•</span>
            <span>采用多AI智能体协作，提供深度、全面的房产分析</span>
          </li>
          <li className="flex items-start">
            <span className="text-primary mr-2">•</span>
            <span>全流程可视化，实时查看AI分析过程</span>
          </li>
          <li className="flex items-start">
            <span className="text-primary mr-2">•</span>
            <span>数据可溯源，每个结论都能追踪到原始数据</span>
          </li>
          <li className="flex items-start">
            <span className="text-primary mr-2">•</span>
            <span>传统调研需要几天，房都督AI仅需10-15分钟</span>
          </li>
          <li className="flex items-start">
            <span className="text-primary mr-2">•</span>
            <span>并行处理50+数据源，确保分析的全面性</span>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default PropertyAnalysis