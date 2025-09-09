'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'
import DataFlowDiagram from '../../components/DataFlowDiagram'
import DeploymentArchitecture from '../../components/DeploymentArchitecture'

export default function Solutions() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header Section */}
      <section className="pt-32 pb-20 bg-gradient-to-br from-primary-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Solutions & Deployment
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Explore WaddleAI's architecture, deployment scenarios, and integration options. 
              From local development to enterprise-scale production deployments.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Interactive Architecture Diagrams */}
      <DataFlowDiagram />
      <DeploymentArchitecture />

      {/* Implementation Guide */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Implementation Guide
            </h2>
            <p className="text-xl text-gray-600">
              Step-by-step guides for each deployment scenario
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Docker Compose Guide */}
            <motion.div
              className="bg-white rounded-2xl p-8 shadow-xl"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
            >
              <div className="bg-blue-600 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M13.5 3c-.8 0-1.5.7-1.5 1.5v15c0 .8.7 1.5 1.5 1.5h6c.8 0 1.5-.7 1.5-1.5v-15c0-.8-.7-1.5-1.5-1.5h-6z"/>
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Docker Compose</h3>
              <p className="text-gray-600 mb-6">Quick start for development and small-scale deployments</p>
              
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-blue-600 font-semibold text-sm">1</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Clone Repository</h4>
                    <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      git clone https://github.com/penguintechinc/waddleai
                    </code>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-blue-600 font-semibold text-sm">2</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Configure Environment</h4>
                    <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      cp .env.testing .env
                    </code>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-blue-600 font-semibold text-sm">3</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Launch Stack</h4>
                    <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      docker-compose -f docker-compose.testing.yml up
                    </code>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <h5 className="font-semibold text-blue-900 mb-2">What You Get:</h5>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• WaddleAI Proxy (Port 8000)</li>
                  <li>• Management Portal (Port 8001)</li>
                  <li>• OpenWebUI (Port 3001)</li>
                  <li>• PostgreSQL & Redis</li>
                </ul>
              </div>
            </motion.div>

            {/* Kubernetes Guide */}
            <motion.div
              className="bg-white rounded-2xl p-8 shadow-xl"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <div className="bg-green-600 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M10.9 2.1l-5.5 5.5c-.6.6-.6 1.6 0 2.2l5.5 5.5c.6.6 1.6.6 2.2 0l5.5-5.5c.6-.6.6-1.6 0-2.2L13.1 2.1c-.6-.6-1.6-.6-2.2 0z"/>
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Kubernetes</h3>
              <p className="text-gray-600 mb-6">Production-ready scalable deployment with high availability</p>
              
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="bg-green-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-green-600 font-semibold text-sm">1</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Setup Cluster</h4>
                    <p className="text-sm text-gray-600">Kubernetes 1.25+ with Ingress controller</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-green-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-green-600 font-semibold text-sm">2</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Deploy Helm Chart</h4>
                    <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      helm install waddleai ./helm/waddleai
                    </code>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-green-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-green-600 font-semibold text-sm">3</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Configure Auto-scaling</h4>
                    <p className="text-sm text-gray-600">HPA and VPA for dynamic scaling</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 p-4 bg-green-50 rounded-lg">
                <h5 className="font-semibold text-green-900 mb-2">Production Features:</h5>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Auto-scaling (3-10 replicas)</li>
                  <li>• High availability PostgreSQL</li>
                  <li>• Redis clustering</li>
                  <li>• Ingress with SSL termination</li>
                </ul>
              </div>
            </motion.div>

            {/* Cloud Native Guide */}
            <motion.div
              className="bg-white rounded-2xl p-8 shadow-xl"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              viewport={{ once: true }}
            >
              <div className="bg-purple-600 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Cloud Native</h3>
              <p className="text-gray-600 mb-6">Fully managed enterprise deployment with global scale</p>
              
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="bg-purple-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-purple-600 font-semibold text-sm">1</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Contact Sales</h4>
                    <p className="text-sm text-gray-600">Discuss requirements with Penguin Technologies</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-purple-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-purple-600 font-semibold text-sm">2</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Architecture Design</h4>
                    <p className="text-sm text-gray-600">Custom cloud architecture for your needs</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <div className="bg-purple-100 w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-purple-600 font-semibold text-sm">3</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Managed Deployment</h4>
                    <p className="text-sm text-gray-600">We handle hosting, monitoring, and maintenance</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 p-4 bg-purple-50 rounded-lg">
                <h5 className="font-semibold text-purple-900 mb-2">Enterprise Benefits:</h5>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>• 99.9% uptime SLA</li>
                  <li>• Global CDN deployment</li>
                  <li>• 24/7 monitoring</li>
                  <li>• Automatic disaster recovery</li>
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Integration Examples */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Integration Examples
            </h2>
            <p className="text-xl text-gray-600">
              Real-world examples of WaddleAI integrations across different platforms
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* VS Code Integration */}
            <motion.div
              className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-8"
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="flex items-center mb-6">
                <div className="bg-blue-600 w-12 h-12 rounded-lg flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352z"/>
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">VS Code Extension</h3>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-4 mb-6">
                <div className="text-green-400 font-mono text-sm">
                  <div className="text-gray-500">// Install WaddleAI VS Code Extension</div>
                  <div className="mt-2">1. Press F5 to launch Extension Development Host</div>
                  <div>2. Set API key: "WaddleAI: Set API Key"</div>
                  <div>3. Open Chat panel and type:</div>
                  <div className="text-blue-300 ml-4">@waddleai Help me write a REST API</div>
                  <div className="text-gray-400 ml-4">✓ Context-aware assistance with full workspace info</div>
                </div>
              </div>
              
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  Context-aware code assistance
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  Multi-model support (GPT-4, Claude, LLaMA)
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  Streaming responses in chat
                </li>
              </ul>
            </motion.div>

            {/* API Integration */}
            <motion.div
              className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-8"
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="flex items-center mb-6">
                <div className="bg-green-600 w-12 h-12 rounded-lg flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">OpenAI API Drop-in</h3>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-4 mb-6">
                <div className="text-green-400 font-mono text-sm">
                  <div className="text-gray-500"># Python Example</div>
                  <div className="mt-2 text-yellow-300">import openai</div>
                  <div className="mt-1">
                    <span className="text-white">client = openai.</span>
                    <span className="text-blue-300">OpenAI</span>
                    <span className="text-white">(</span>
                  </div>
                  <div className="ml-4 text-orange-300">api_key="wa-your-key",</div>
                  <div className="ml-4 text-orange-300">base_url="http://localhost:8000/v1"</div>
                  <div className="text-white">)</div>
                  <div className="mt-2 text-gray-400"># Use exactly like OpenAI API</div>
                  <div className="text-white">response = client.chat.completions.create(...)</div>
                </div>
              </div>
              
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  100% OpenAI API compatible
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  Drop-in replacement for existing code
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  Enhanced security and routing
                </li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-20 bg-primary-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold mb-6">
              Ready to Deploy WaddleAI?
            </h2>
            <p className="text-xl mb-8 text-primary-200 max-w-3xl mx-auto">
              Choose the deployment option that fits your needs, from quick Docker setup 
              to enterprise cloud deployment with full management.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="https://github.com/penguintechinc/waddleai"
                className="bg-white text-primary-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center justify-center"
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg className="mr-2 w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                Start with Docker
              </a>
              <a
                href="/pricing"
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-900 transition-colors inline-flex items-center justify-center"
              >
                <svg className="mr-2 w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                View Pricing Plans
              </a>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}