import React from 'react'

const PropertyAnalysis: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-primary-600 mb-6">房产分析</h1>
      <div className="bg-white rounded-lg shadow-md p-6">
        <form className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="propertyAddress" className="block text-sm font-medium text-gray-700 mb-1">
                房产地址
              </label>
              <input
                type="text"
                id="propertyAddress"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="请输入房产地址"
              />
            </div>
            <div>
              <label htmlFor="propertyType" className="block text-sm font-medium text-gray-700 mb-1">
                房产类型
              </label>
              <select
                id="propertyType"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择房产类型</option>
                <option value="apartment">公寓</option>
                <option value="house">住宅</option>
                <option value="commercial">商业</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="propertyArea" className="block text-sm font-medium text-gray-700 mb-1">
                建筑面积 (㎡)
              </label>
              <input
                type="number"
                id="propertyArea"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="请输入建筑面积"
              />
            </div>
            <div>
              <label htmlFor="propertyAge" className="block text-sm font-medium text-gray-700 mb-1">
                房龄 (年)
              </label>
              <input
                type="number"
                id="propertyAge"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="请输入房龄"
              />
            </div>
          </div>
          <div>
            <label htmlFor="propertyDescription" className="block text-sm font-medium text-gray-700 mb-1">
              房产描述 (可选)
            </label>
            <textarea
              id="propertyDescription"
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="请输入房产描述"
            ></textarea>
          </div>
          <div>
            <button
              type="button"
              className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            >
              开始分析
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PropertyAnalysis
