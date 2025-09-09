'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Zap, Shield, BarChart3 } from 'lucide-react'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-10 left-10 w-72 h-72 bg-primary-300 rounded-full filter blur-3xl animate-float"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-primary-400 rounded-full filter blur-3xl animate-float" style={{animationDelay: '1s'}}></div>
      </div>
      
      <div className="relative container">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="text-left"
          >
            <div className="flex items-center space-x-2 mb-6">
              <span className="bg-primary-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                Enterprise AI Platform
              </span>
              <span className="text-primary-600 font-semibold">v1.0</span>
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              WaddleAI
              <span className="block text-primary-600">Proxy Platform</span>
            </h1>
            
            <p className="text-xl lg:text-2xl text-gray-600 mb-8 leading-relaxed">
              Enterprise-grade AI proxy with OpenAI-compatible APIs, advanced routing, 
              security scanning, and comprehensive token management.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <motion.a
                href="/docs/getting-started/installation/"
                className="btn-primary inline-flex items-center justify-center"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Get Started
                <ArrowRight className="ml-2 w-5 h-5" />
              </motion.a>
              
              <motion.a
                href="/docs/claude/"
                className="btn-secondary inline-flex items-center justify-center"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                View Documentation
              </motion.a>
            </div>
            
            <div className="grid grid-cols-3 gap-6 pt-8 border-t border-gray-200">
              <div className="text-center">
                <Zap className="w-8 h-8 text-primary-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900">99.9%</div>
                <div className="text-sm text-gray-600">Uptime</div>
              </div>
              <div className="text-center">
                <Shield className="w-8 h-8 text-primary-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900">100%</div>
                <div className="text-sm text-gray-600">Security Scanned</div>
              </div>
              <div className="text-center">
                <BarChart3 className="w-8 h-8 text-primary-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900">50ms</div>
                <div className="text-sm text-gray-600">Avg Latency</div>
              </div>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
              <div className="mb-4">
                <span className="text-sm text-gray-500">Terminal</span>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6 text-green-400 font-mono text-sm">
                <div className="flex items-center mb-2">
                  <span className="text-blue-400">$</span>
                  <span className="ml-2">pip install waddleai</span>
                </div>
                <div className="text-gray-400 mb-4">✓ Installing WaddleAI...</div>
                
                <div className="border-t border-gray-700 pt-4">
                  <div className="text-yellow-400 mb-2"># Start proxy server</div>
                  <div className="mb-2">
                    <span className="text-blue-400">$</span>
                    <span className="ml-2">waddleai start --proxy</span>
                  </div>
                  <div className="text-gray-400 mb-2">✓ Proxy server running on :8000</div>
                  
                  <div className="text-yellow-400 mb-2"># Configure OpenAI client</div>
                  <div className="text-white">
                    <div>client = OpenAI(</div>
                    <div className="ml-4">api_key="wa-your-key",</div>
                    <div className="ml-4">base_url="http://localhost:8000/v1"</div>
                    <div>)</div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating elements */}
            <motion.div
              className="absolute -top-6 -right-6 bg-primary-500 text-white rounded-lg px-4 py-2 text-sm font-semibold shadow-lg"
              animate={{ y: [0, -10, 0] }}
              transition={{ repeat: Infinity, duration: 3, delay: 1 }}
            >
              OpenAI Compatible
            </motion.div>
            
            <motion.div
              className="absolute -bottom-6 -left-6 bg-green-500 text-white rounded-lg px-4 py-2 text-sm font-semibold shadow-lg"
              animate={{ y: [0, -10, 0] }}
              transition={{ repeat: Infinity, duration: 3, delay: 2 }}
            >
              Enterprise Ready
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}