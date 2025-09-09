'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'
import { 
  Code, 
  Globe, 
  Shield, 
  Database, 
  Server, 
  Brain, 
  ArrowRight,
  Monitor,
  GitBranch,
  Lock,
  BarChart3
} from 'lucide-react'

const dataFlowSteps = [
  {
    id: 'user-input',
    title: 'User Input',
    description: 'Request from VS Code, OpenWebUI, or API client',
    icon: Code,
    color: 'bg-blue-500',
    position: { x: 50, y: 50 },
    connections: ['auth-security']
  },
  {
    id: 'auth-security',
    title: 'Authentication & Security',
    description: 'API key validation and prompt security scanning',
    icon: Shield,
    color: 'bg-red-500', 
    position: { x: 250, y: 50 },
    connections: ['routing']
  },
  {
    id: 'routing',
    title: 'Intelligent Routing',
    description: 'Model selection and request routing logic',
    icon: GitBranch,
    color: 'bg-purple-500',
    position: { x: 450, y: 50 },
    connections: ['llm-providers']
  },
  {
    id: 'llm-providers',
    title: 'LLM Providers',
    description: 'OpenAI, Anthropic, Ollama, and other providers',
    icon: Brain,
    color: 'bg-green-500',
    position: { x: 650, y: 50 },
    connections: ['response-processing']
  },
  {
    id: 'response-processing',
    title: 'Response Processing',
    description: 'Token counting, memory storage, and analytics',
    icon: Server,
    color: 'bg-orange-500',
    position: { x: 450, y: 200 },
    connections: ['user-response']
  },
  {
    id: 'user-response',
    title: 'User Response',
    description: 'Streaming response back to client interface',
    icon: Monitor,
    color: 'bg-cyan-500',
    position: { x: 250, y: 200 },
    connections: []
  }
]

const integrations = [
  {
    id: 'vscode',
    name: 'VS Code Extension',
    description: '@waddleai chat participant with context awareness',
    icon: Code,
    color: 'bg-blue-600'
  },
  {
    id: 'openwebui', 
    name: 'OpenWebUI',
    description: 'Modern web interface for model testing',
    icon: Globe,
    color: 'bg-purple-600'
  },
  {
    id: 'api',
    name: 'OpenAI API',
    description: 'Drop-in compatible API for existing applications',
    icon: Server,
    color: 'bg-green-600'
  }
]

export default function DataFlowDiagram() {
  const [activeStep, setActiveStep] = useState<string | null>(null)
  const [activeIntegration, setActiveIntegration] = useState<string>('vscode')

  return (
    <section id="architecture" className="py-20 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            How WaddleAI Processes Requests
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Interactive dataflow showing how requests move through WaddleAI's architecture
          </p>
        </motion.div>

        {/* Integration Selector */}
        <motion.div
          className="flex justify-center mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
        >
          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
              Choose Integration Method
            </h3>
            <div className="flex space-x-4">
              {integrations.map((integration) => (
                <button
                  key={integration.id}
                  onClick={() => setActiveIntegration(integration.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    activeIntegration === integration.id
                      ? `${integration.color} text-white shadow-lg transform scale-105`
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <integration.icon className="w-4 h-4" />
                  <span className="hidden sm:block">{integration.name}</span>
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Data Flow Diagram */}
        <motion.div
          className="relative bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
        >
          <div className="relative h-96 overflow-hidden">
            {/* Connection Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {dataFlowSteps.map((step) => 
                step.connections.map((connectionId) => {
                  const target = dataFlowSteps.find(s => s.id === connectionId)
                  if (!target) return null
                  
                  return (
                    <motion.line
                      key={`${step.id}-${connectionId}`}
                      x1={`${(step.position.x / 700) * 100}%`}
                      y1={`${(step.position.y / 300) * 100}%`}
                      x2={`${(target.position.x / 700) * 100}%`}
                      y2={`${(target.position.y / 300) * 100}%`}
                      stroke="#e5e7eb"
                      strokeWidth="2"
                      strokeDasharray="5,5"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 2, delay: 0.5, repeat: Infinity }}
                    />
                  )
                })
              )}
            </svg>

            {/* Flow Steps */}
            {dataFlowSteps.map((step, index) => (
              <motion.div
                key={step.id}
                className="absolute cursor-pointer"
                style={{ 
                  left: `${(step.position.x / 700) * 100}%`, 
                  top: `${(step.position.y / 300) * 100}%`,
                  transform: 'translate(-50%, -50%)'
                }}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                onHoverStart={() => setActiveStep(step.id)}
                onHoverEnd={() => setActiveStep(null)}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className={`${step.color} w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 ${
                  activeStep === step.id ? 'ring-4 ring-blue-300' : ''
                }`}>
                  <step.icon className="w-8 h-8 text-white" />
                </div>
                
                <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 text-center">
                  <h4 className="text-sm font-semibold text-gray-900 mb-1">
                    {step.title}
                  </h4>
                  {activeStep === step.id && (
                    <motion.div
                      className="bg-gray-900 text-white text-xs p-2 rounded-lg max-w-48 z-10"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                    >
                      {step.description}
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Current Integration Info */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            {(() => {
              const integration = integrations.find(i => i.id === activeIntegration)
              return integration ? (
                <div className="flex items-center justify-center space-x-4">
                  <div className={`${integration.color} w-12 h-12 rounded-full flex items-center justify-center`}>
                    <integration.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">
                      {integration.name}
                    </h4>
                    <p className="text-gray-600">{integration.description}</p>
                  </div>
                </div>
              ) : null
            })()}
          </div>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          className="grid md:grid-cols-4 gap-6"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          viewport={{ once: true }}
        >
          {[
            { icon: ArrowRight, label: 'Avg Latency', value: '< 50ms', color: 'bg-blue-500' },
            { icon: Shield, label: 'Security Scanned', value: '100%', color: 'bg-red-500' },
            { icon: BarChart3, label: 'Uptime SLA', value: '99.9%', color: 'bg-green-500' },
            { icon: Database, label: 'Requests/Min', value: '10K+', color: 'bg-purple-500' }
          ].map((metric, index) => (
            <div key={index} className="bg-white rounded-xl p-6 shadow-lg text-center">
              <div className={`${metric.color} w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4`}>
                <metric.icon className="w-6 h-6 text-white" />
              </div>
              <div className="text-2xl font-bold text-gray-900 mb-1">
                {metric.value}
              </div>
              <div className="text-sm text-gray-600">
                {metric.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}