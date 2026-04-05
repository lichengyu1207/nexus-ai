import React, { useState, useEffect } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import LanguageSwitcher from '../LanguageSwitcher'

const Navbar: React.FC = () => {
  const { t } = useTranslation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navLinks = [
    { path: '/', label: t('nav.home') },
    { path: '/property-analysis', label: t('nav.propertyAnalysis') },
    { path: '/report', label: t('nav.analysisReport') },
  ]

  return (
    <header className={`bg-white shadow-md transition-all duration-300 ${isScrolled ? 'shadow-lg' : ''}`}>
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="text-primary-600 text-2xl font-bold">{t('landing.appNameEn')}</div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            {navLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) =>
                  `text-sm font-medium transition-colors ${isActive ? 'text-primary-600' : 'text-gray-600 hover:text-primary-500'}`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* Language Switcher & Mobile Menu Toggle */}
          <div className="flex items-center gap-4">
            <LanguageSwitcher compact />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden text-gray-600 hover:text-primary-600 focus:outline-none"
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <nav className={`md:hidden py-4 space-y-4 ${isMobileMenuOpen ? 'fixed inset-0 z-50 bg-white shadow-2xl' : ''}`}>
          <div className="px-4">
            <div className="flex justify-between items-center mb-4">
              <span className="text-lg font-semibold text-gray-900 dark:text-white">菜单</span>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              {navLinks.map((link) => (
                <NavLink
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block w-full px-4 py-3 text-left rounded-lg transition-colors ${
                      isActive ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
          </div>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
