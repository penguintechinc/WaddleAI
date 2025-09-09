'use client'

import Hero from '../components/Hero'
import FeatureGrid from '../components/FeatureGrid'
import Testimonials from '../components/Testimonials'
import { motion } from 'framer-motion'

export default function Home() {
  return (
    <>
      <Hero />
      
      <motion.section 
        className="py-20 bg-gray-50"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Why Choose WaddleAI?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Enterprise-grade AI proxy that provides OpenAI-compatible APIs with advanced routing, 
              security, and management capabilities for organizations of all sizes.
            </p>
          </div>
          
          <FeatureGrid />
        </div>
      </motion.section>

      <motion.section 
        className="py-20 bg-white"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-12">
              Simple integration with powerful features under the hood
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Deploy WaddleAI</h3>
              <p className="text-gray-600">
                Set up WaddleAI proxy and management servers in your infrastructure using Docker or Kubernetes.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-primary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Configure Providers</h3>
              <p className="text-gray-600">
                Connect your OpenAI, Anthropic, and Ollama providers through the management interface.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-primary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Start Building</h3>
              <p className="text-gray-600">
                Use the OpenAI-compatible API in your applications with enhanced security and management.
              </p>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section 
        className="py-20 bg-primary-900 text-white"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl mb-8 text-primary-200">
            Deploy WaddleAI in minutes and start managing your AI infrastructure today.
          </p>
          <div className="space-x-4">
            <a
              href="/docs/"
              className="bg-white text-primary-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block"
            >
              View Documentation
            </a>
            <a
              href="https://github.com/your-org/waddleai"
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-900 transition-colors inline-block"
            >
              GitHub Repository
            </a>
          </div>
        </div>
      </motion.section>

      <Testimonials />
    </>
  )
}