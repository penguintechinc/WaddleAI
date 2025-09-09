'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Menu, X, Github, ExternalLink } from 'lucide-react'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const navigation = [
    { name: 'Features', href: '#features' },
    { name: 'Solutions', href: '/solutions' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'Documentation', href: 'https://docs.waddlebot.ai' },
    { name: 'API', href: 'https://docs.waddlebot.ai/api' },
  ]

  return (
    <motion.header
      className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-gray-200 z-50"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <div className="flex items-center">
            <motion.a
              href="/"
              className="text-2xl font-bold text-primary-600"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              WaddleAI
            </motion.a>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                {item.name}
              </a>
            ))}
            
            <div className="flex items-center space-x-4">
              <a
                href="https://github.com/penguintechinc/waddleai"
                className="text-gray-700 hover:text-primary-600 transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="w-5 h-5" />
              </a>
              
              <motion.a
                href="https://docs.waddlebot.ai/getting-started"
                className="btn-primary inline-flex items-center"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Get Started
                <ExternalLink className="ml-2 w-4 h-4" />
              </motion.a>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-primary-600"
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <motion.div
            className="md:hidden py-4 border-t border-gray-200"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="flex flex-col space-y-4">
              {navigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className="text-gray-700 hover:text-primary-600 font-medium py-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.name}
                </a>
              ))}
              
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <a
                  href="https://github.com/penguintechinc/waddleai"
                  className="text-gray-700 hover:text-primary-600 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="w-5 h-5" />
                </a>
                
                <a
                  href="https://docs.waddlebot.ai/getting-started"
                  className="btn-primary inline-flex items-center"
                >
                  Get Started
                  <ExternalLink className="ml-2 w-4 h-4" />
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </nav>
    </motion.header>
  )
}