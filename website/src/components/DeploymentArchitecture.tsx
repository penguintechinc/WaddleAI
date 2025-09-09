'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'
import { 
  Server, 
  Database, 
  Shield, 
  Cloud, 
  Container,
  Network,
  Monitor,
  GitBranch,
  Lock,
  Globe,
  Cpu,
  HardDrive,
  Zap
} from 'lucide-react'

const deploymentScenarios = [
  {
    id: 'docker',
    name: 'Docker Compose',
    description: 'Quick local testing and development',
    icon: Container,
    color: 'bg-blue-600',
    complexity: 'Simple'
  },
  {
    id: 'kubernetes',
    name: 'Kubernetes',
    description: 'Production-ready scalable deployment',
    icon: Cloud,
    color: 'bg-green-600', 
    complexity: 'Advanced'
  },
  {
    id: 'cloud',
    name: 'Cloud Native',
    description: 'Managed services with auto-scaling',
    icon: Globe,
    color: 'bg-purple-600',
    complexity: 'Expert'
  }
]

const architectureComponents = {
  docker: [
    {
      id: 'proxy',
      name: 'WaddleAI Proxy',
      description: 'OpenAI-compatible API gateway',
      icon: Server,
      color: 'bg-blue-500',
      position: { x: 200, y: 100 },
      specs: { cpu: '2 cores', memory: '4GB', storage: '10GB' }
    },
    {
      id: 'mgmt',
      name: 'Management Server',
      description: 'Admin portal and configuration',
      icon: Monitor,
      color: 'bg-green-500',
      position: { x: 400, y: 100 },
      specs: { cpu: '1 core', memory: '2GB', storage: '5GB' }
    },
    {
      id: 'openwebui',
      name: 'OpenWebUI',
      description: 'Web interface for testing',
      icon: Globe,
      color: 'bg-purple-500',
      position: { x: 100, y: 200 },
      specs: { cpu: '1 core', memory: '1GB', storage: '2GB' }
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      description: 'Primary database',
      icon: Database,
      color: 'bg-indigo-500',
      position: { x: 300, y: 200 },
      specs: { cpu: '2 cores', memory: '4GB', storage: '50GB' }
    },
    {
      id: 'redis',
      name: 'Redis',
      description: 'Cache and session store',
      icon: Zap,
      color: 'bg-red-500',
      position: { x: 500, y: 200 },
      specs: { cpu: '1 core', memory: '2GB', storage: '10GB' }
    }
  ],
  kubernetes: [
    {
      id: 'ingress',
      name: 'Ingress Controller',
      description: 'Load balancer and SSL termination',
      icon: Network,
      color: 'bg-orange-500',
      position: { x: 300, y: 50 },
      specs: { replicas: '2', cpu: '500m', memory: '1Gi' }
    },
    {
      id: 'proxy-pods',
      name: 'Proxy Pods',
      description: 'Stateless API gateways',
      icon: Server,
      color: 'bg-blue-500',
      position: { x: 150, y: 150 },
      specs: { replicas: '3-10', cpu: '1000m', memory: '2Gi' }
    },
    {
      id: 'mgmt-pods',
      name: 'Management Pods',
      description: 'Admin and config services',
      icon: Monitor,
      color: 'bg-green-500',
      position: { x: 450, y: 150 },
      specs: { replicas: '2', cpu: '500m', memory: '1Gi' }
    },
    {
      id: 'postgres-cluster',
      name: 'PostgreSQL Cluster',
      description: 'High availability database',
      icon: Database,
      color: 'bg-indigo-500',
      position: { x: 200, y: 250 },
      specs: { replicas: '3', cpu: '2000m', memory: '4Gi' }
    },
    {
      id: 'redis-cluster', 
      name: 'Redis Cluster',
      description: 'Distributed cache',
      icon: Zap,
      color: 'bg-red-500',
      position: { x: 400, y: 250 },
      specs: { replicas: '6', cpu: '500m', memory: '2Gi' }
    }
  ],
  cloud: [
    {
      id: 'cdn',
      name: 'Global CDN',
      description: 'Edge caching and DDoS protection',
      icon: Globe,
      color: 'bg-cyan-500',
      position: { x: 300, y: 50 },
      specs: { locations: '200+', latency: '<50ms' }
    },
    {
      id: 'load-balancer',
      name: 'Application Load Balancer',
      description: 'Auto-scaling and health checks',
      icon: Network,
      color: 'bg-orange-500',
      position: { x: 300, y: 120 },
      specs: { zones: '3', throughput: '100K RPS' }
    },
    {
      id: 'proxy-service',
      name: 'Proxy Service',
      description: 'Serverless API functions',
      icon: Server,
      color: 'bg-blue-500',
      position: { x: 150, y: 200 },
      specs: { scaling: 'Auto', memory: '10GB max' }
    },
    {
      id: 'mgmt-service',
      name: 'Management Service',
      description: 'Container-based admin portal',
      icon: Monitor,
      color: 'bg-green-500',
      position: { x: 450, y: 200 },
      specs: { instances: '2-5', memory: '8GB' }
    },
    {
      id: 'managed-db',
      name: 'Managed Database',
      description: 'Cloud PostgreSQL with backups',
      icon: Database,
      color: 'bg-indigo-500',
      position: { x: 200, y: 280 },
      specs: { sla: '99.95%', backup: 'Auto' }
    },
    {
      id: 'managed-cache',
      name: 'Managed Cache',
      description: 'Redis with high availability', 
      icon: Zap,
      color: 'bg-red-500',
      position: { x: 400, y: 280 },
      specs: { sla: '99.9%', memory: '100GB max' }
    }
  ]
}

export default function DeploymentArchitecture() {
  const [activeScenario, setActiveScenario] = useState<string>('docker')
  const [activeComponent, setActiveComponent] = useState<string | null>(null)

  const currentComponents = architectureComponents[activeScenario as keyof typeof architectureComponents] || []

  return (
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
            Deployment Architecture Scenarios
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose your deployment strategy based on scale, complexity, and requirements
          </p>
        </motion.div>

        {/* Scenario Selector */}
        <motion.div
          className="flex justify-center mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
        >
          <div className="bg-gray-50 rounded-xl p-6 shadow-inner">
            <div className="grid md:grid-cols-3 gap-4">
              {deploymentScenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  onClick={() => setActiveScenario(scenario.id)}
                  className={`p-6 rounded-xl text-left transition-all duration-300 ${
                    activeScenario === scenario.id
                      ? 'bg-white shadow-lg ring-2 ring-blue-500 transform scale-105'
                      : 'bg-white hover:shadow-md'
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className={`${scenario.color} w-12 h-12 rounded-lg flex items-center justify-center`}>
                      <scenario.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{scenario.name}</h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        scenario.complexity === 'Simple' ? 'bg-green-100 text-green-700' :
                        scenario.complexity === 'Advanced' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {scenario.complexity}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 text-sm">{scenario.description}</p>
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Architecture Diagram */}
        <motion.div
          className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-8 shadow-xl mb-12"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          key={activeScenario} // Force re-render when scenario changes
        >
          <div className="relative h-[500px] overflow-hidden">
            {/* Connection Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {(() => {
                // Connect components in a logical flow
                const connections = [
                  [0, 1], // proxy to mgmt
                  [0, 3], // proxy to database
                  [1, 3], // mgmt to database  
                  [1, 4], // mgmt to redis
                  [2, 0]  // openwebui/cdn to proxy
                ]
                
                return connections.map(([from, to], connIndex) => {
                  const fromComp = currentComponents[from]
                  const toComp = currentComponents[to]
                  if (!fromComp || !toComp) return null
                  
                  return (
                    <motion.line
                      key={`${activeScenario}-connection-${from}-${to}`}
                      x1={`${(fromComp.position.x / 600) * 100}%`}
                      y1={`${(fromComp.position.y / 400) * 100}%`}
                      x2={`${(toComp.position.x / 600) * 100}%`}
                      y2={`${(toComp.position.y / 400) * 100}%`}
                      stroke="#d1d5db"
                      strokeWidth="2"
                      strokeDasharray="4,4"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 1.5, delay: connIndex * 0.2 }}
                    />
                  )
                })
              })()}
            </svg>

            {/* Components */}
            {currentComponents.map((component, index) => (
              <motion.div
                key={component.id}
                className="absolute cursor-pointer"
                style={{ 
                  left: `${(component.position.x / 600) * 100}%`, 
                  top: `${(component.position.y / 400) * 100}%`,
                  transform: 'translate(-50%, -50%)'
                }}
                initial={{ opacity: 0, scale: 0, rotate: -180 }}
                animate={{ opacity: 1, scale: 1, rotate: 0 }}
                transition={{ 
                  duration: 0.8, 
                  delay: index * 0.15,
                  type: 'spring',
                  stiffness: 100
                }}
                onHoverStart={() => setActiveComponent(component.id)}
                onHoverEnd={() => setActiveComponent(null)}
                whileHover={{ scale: 1.1, zIndex: 10 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className={`${component.color} w-20 h-20 rounded-xl flex items-center justify-center shadow-lg transition-all duration-300 ${
                  activeComponent === component.id ? 'ring-4 ring-blue-300 shadow-2xl' : ''
                }`}>
                  <component.icon className="w-8 h-8 text-white" />
                </div>
                
                <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 text-center">
                  <h4 className="text-sm font-semibold text-gray-900 mb-1">
                    {component.name}
                  </h4>
                  {activeComponent === component.id && (
                    <motion.div
                      className="absolute top-full mt-2 bg-gray-900 text-white text-xs p-3 rounded-lg shadow-xl z-20 max-w-56"
                      initial={{ opacity: 0, y: 10, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.9 }}
                    >
                      <p className="mb-2">{component.description}</p>
                      <div className="space-y-1 text-blue-200">
                        {Object.entries(component.specs).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="capitalize">{key}:</span>
                            <span className="font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Scenario Details */}
        <motion.div
          className="grid md:grid-cols-3 gap-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          viewport={{ once: true }}
        >
          {(() => {
            const scenarioDetails = {
              docker: [
                { 
                  title: 'Development Setup',
                  description: 'Perfect for local development and testing',
                  items: ['Single-command deployment', 'All services included', 'Easy configuration']
                },
                {
                  title: 'Resource Requirements', 
                  description: 'Minimal hardware requirements',
                  items: ['8GB RAM minimum', '4 CPU cores', '100GB storage']
                },
                {
                  title: 'Use Cases',
                  description: 'Ideal scenarios for Docker deployment',
                  items: ['Local development', 'Small team testing', 'Proof of concept']
                }
              ],
              kubernetes: [
                {
                  title: 'Production Ready',
                  description: 'Scalable and resilient deployment',
                  items: ['Auto-scaling pods', 'High availability', 'Rolling updates']
                },
                {
                  title: 'Infrastructure',
                  description: 'Kubernetes cluster requirements', 
                  items: ['3+ node cluster', '16GB RAM per node', 'Persistent volumes']
                },
                {
                  title: 'Features',
                  description: 'Enterprise-grade capabilities',
                  items: ['Load balancing', 'Health monitoring', 'Zero-downtime updates']
                }
              ],
              cloud: [
                {
                  title: 'Managed Services',
                  description: 'Fully managed cloud deployment',
                  items: ['Serverless functions', 'Managed databases', 'CDN integration']
                },
                {
                  title: 'Auto-Scaling',
                  description: 'Scales with your needs',
                  items: ['Traffic-based scaling', 'Cost optimization', 'Global distribution']
                },
                {
                  title: 'Enterprise',
                  description: 'Large-scale production deployment',
                  items: ['99.99% uptime SLA', 'DDoS protection', 'Compliance ready']
                }
              ]
            }
            
            return (scenarioDetails[activeScenario as keyof typeof scenarioDetails] || []).map((detail, index) => (
              <div key={index} className="bg-white rounded-xl p-6 shadow-lg">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {detail.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {detail.description}
                </p>
                <ul className="space-y-2">
                  {detail.items.map((item, itemIndex) => (
                    <li key={itemIndex} className="flex items-center text-gray-700">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))
          })()}
        </motion.div>
      </div>
    </section>
  )
}