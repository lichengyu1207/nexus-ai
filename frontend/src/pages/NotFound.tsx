import React from 'react'
import { useNavigate } from 'react-router-dom'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-center items-center h-96">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">404</h1>
          <h2 className="text-2xl font-medium mb-4">页面不存在</h2>
          <p className="text-gray-600 mb-8">抱歉，您访问的页面不存在或已被移除</p>
          <button
            onClick={() => navigate('/')}
            className="bg-primary hover:bg-primaryDark text-white font-medium py-2 px-6 rounded-md transition-colors"
          >
            返回首页
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotFound