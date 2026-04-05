import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'

interface UserInfo {
  id: string
  email: string
  username: string
  role: string
  integral: number
  source: string | null
  source_name: string | null
  bonus_label: string | null
}

const Navbar: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [user, setUser] = useState<UserInfo | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token')
      if (!token) return

      try {
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        }
      } catch (error) {
        console.error('Failed to fetch user:', error)
      }
    }

    fetchUser()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    navigate('/')
  }

  return (
    <header className="acrylic sticky top-0 z-50 border-b border-white/20">
      <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-xl flex items-center justify-center text-xl shadow-fluent-sm group-hover:shadow-gold-glow transition-all duration-300">
            🏠
          </div>
          <span className="text-xl font-bold text-fluent-deepOcean-500">房都督AI</span>
        </Link>
        
        <ul className="hidden md:flex space-x-8">
          <li>
            <Link to="/" className="text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium">
              首页
            </Link>
          </li>
          <li>
            <Link to="/property-analysis" className="text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium">
              房产分析
            </Link>
          </li>
          <li>
            <Link to="/trilogy-showcase" className="text-fluent-gold-500 hover:text-fluent-gold-600 transition-colors font-medium flex items-center gap-1">
              ✨ 三部曲演示
            </Link>
          </li>
          <li>
            <Link to="/articles" className="text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium">
              资讯中心
            </Link>
          </li>
          <li>
            <Link to="/about" className="text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium">
              关于我们
            </Link>
          </li>
        </ul>
        
        <div className="hidden md:flex items-center space-x-4">
          {user ? (
            <>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 text-white flex items-center justify-center text-sm font-bold">
                  {user.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="text-sm text-fluent-deepOcean-500 font-medium">{user.username}</span>
                {user.bonus_label && (
                  <span className="bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 text-xs px-2 py-1 rounded-full font-medium">
                    {user.bonus_label}
                  </span>
                )}
                <span className="bg-fluent-deepOcean-100 text-fluent-deepOcean-500 text-sm px-3 py-1 rounded-full font-medium">
                  {user.integral} 积分
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-fluent-deepOcean-400 hover:text-fluent-gold-500 transition-colors font-medium"
              >
                退出
              </button>
            </>
          ) : (
            <Link 
              to="/login" 
              className="bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-5 py-2 rounded-xl hover:shadow-gold-glow transition-all duration-300 font-medium"
            >
              登录
            </Link>
          )}
        </div>
        
        <button 
          className="md:hidden text-fluent-deepOcean-500 p-2" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {isMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </nav>
      
      {isMenuOpen && (
        <div className="md:hidden acrylic border-t border-white/20">
          <ul className="container mx-auto px-4 py-4 space-y-4">
            <li>
              <Link 
                to="/" 
                className="block text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium py-2"
                onClick={() => setIsMenuOpen(false)}
              >
                首页
              </Link>
            </li>
            <li>
              <Link 
                to="/property-analysis" 
                className="block text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium py-2"
                onClick={() => setIsMenuOpen(false)}
              >
                房产分析
              </Link>
            </li>
            <li>
              <Link 
                to="/articles" 
                className="block text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium py-2"
                onClick={() => setIsMenuOpen(false)}
              >
                资讯中心
              </Link>
            </li>
            <li>
              <Link 
                to="/about" 
                className="block text-fluent-deepOcean-500 hover:text-fluent-gold-500 transition-colors font-medium py-2"
                onClick={() => setIsMenuOpen(false)}
              >
                关于我们
              </Link>
            </li>
            {user ? (
              <>
                <li className="pt-2 border-t border-white/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 text-white flex items-center justify-center text-sm font-bold">
                      {user.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <span className="text-sm text-fluent-deepOcean-500 font-medium">{user.username}</span>
                    {user.bonus_label && (
                      <span className="bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 text-xs px-2 py-1 rounded-full font-medium">
                        {user.bonus_label}
                      </span>
                    )}
                  </div>
                  <span className="text-sm text-fluent-gold-500 font-medium">{user.integral} 积分</span>
                </li>
                <li>
                  <button
                    onClick={() => {
                      handleLogout()
                      setIsMenuOpen(false)
                    }}
                    className="text-fluent-deepOcean-400 hover:text-fluent-gold-500 transition-colors font-medium py-2"
                  >
                    退出登录
                  </button>
                </li>
              </>
            ) : (
              <li className="pt-2 border-t border-white/20">
                <Link 
                  to="/login" 
                  className="block bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-4 py-2 rounded-xl text-center font-medium"
                  onClick={() => setIsMenuOpen(false)}
                >
                  登录
                </Link>
              </li>
            )}
          </ul>
        </div>
      )}
    </header>
  )
}

export default Navbar
