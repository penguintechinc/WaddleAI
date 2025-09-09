'use client'

import Hero from '../components/Hero'
import FeatureGrid from '../components/FeatureGrid'
import DataFlowDiagram from '../components/DataFlowDiagram'
import DeploymentArchitecture from '../components/DeploymentArchitecture'
import { motion } from 'framer-motion'

export default function Home() {
  return (
    <>
      <Hero />
      
      <motion.section 
        id="features"
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
                Use in VS Code with @waddleai, OpenWebUI for testing, or the OpenAI-compatible API in applications.
              </p>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section 
        id="integrations"
        className="py-20 bg-gradient-to-r from-primary-50 to-blue-50"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Multiple Ways to Integrate
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Choose the integration method that works best for your workflow
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl p-8 shadow-lg text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352z"/>
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-4">VS Code Extension</h3>
              <p className="text-gray-600 mb-6">
                Native chat participant integration with full workspace context awareness and streaming responses.
              </p>
              <a href="https://docs.waddlebot.ai/integrations/vscode-extension/" className="text-blue-600 font-semibold hover:text-blue-700">
                Learn More →
              </a>
            </div>
            
            <div className="bg-white rounded-xl p-8 shadow-lg text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 13.363H13.11v6.452h-2.22v-6.452H6.432v-2.726h4.458V4.185h2.22v6.452h4.458v2.726z"/>
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-4">OpenWebUI</h3>
              <p className="text-gray-600 mb-6">
                Modern web interface for testing models, managing conversations, and exploring AI capabilities.
              </p>
              <a href="https://docs.waddlebot.ai/testing-setup/" className="text-purple-600 font-semibold hover:text-purple-700">
                Learn More →
              </a>
            </div>
            
            <div className="bg-white rounded-xl p-8 shadow-lg text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0L1.608 6v12L12 24l10.392-6V6L12 0zm-1 17.25h-3.5v-2.5H11v2.5zm0-5h-3.5v-2.5H11v2.5zm6 5h-3.5v-2.5H17v2.5zm0-5h-3.5v-2.5H17v2.5z"/>
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-4">OpenAI API</h3>
              <p className="text-gray-600 mb-6">
                Drop-in replacement for OpenAI API with enhanced security, routing, and enterprise features.
              </p>
              <a href="https://docs.waddlebot.ai/api/openai-compatible/" className="text-green-600 font-semibold hover:text-green-700">
                Learn More →
              </a>
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
              href="https://docs.waddlebot.ai/"
              className="bg-white text-primary-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block"
            >
              View Documentation
            </a>
            <a
              href="https://github.com/penguintechinc/waddleai"
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-900 transition-colors inline-block"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub Repository
            </a>
          </div>
        </div>
      </motion.section>

      <DataFlowDiagram />
      
      <DeploymentArchitecture />
    </>
  )
}