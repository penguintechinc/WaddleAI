'use client'

import { motion } from 'framer-motion'
import { 
  Shield, 
  Zap, 
  BarChart3, 
  Users, 
  Globe, 
  Brain,
  Code,
  Monitor,
  GitBranch,
  Lock,
  Gauge,
  Layers
} from 'lucide-react'

const features = [
  {
    icon: Code,
    title: "VS Code Extension",
    description: "Native integration with VS Code Chat. Use @waddleai directly in your IDE with full context awareness.",
    color: "bg-blue-500"
  },
  {
    icon: Monitor,
    title: "OpenWebUI Integration", 
    description: "Modern web interface for testing and interacting with WaddleAI models through a sleek chat interface.",
    color: "bg-purple-500"
  },
  {
    icon: Globe,
    title: "OpenAI Compatible API",
    description: "Drop-in replacement for OpenAI API. Use existing OpenAI clients and tools without modification.",
    color: "bg-green-500"
  },
  {
    icon: GitBranch,
    title: "Multi-LLM Routing",
    description: "Route requests to OpenAI, Anthropic, Ollama, and other providers based on your configuration.",
    color: "bg-orange-500"
  },
  {
    icon: Shield,
    title: "Advanced Security",
    description: "Prompt injection detection, jailbreak prevention, and comprehensive security scanning.",
    color: "bg-red-500"
  },
  {
    icon: Users,
    title: "Multi-Tenant Architecture",
    description: "Organization-based isolation with role-based access control for enterprise deployments.",
    color: "bg-indigo-500"
  },
  {
    icon: BarChart3,
    title: "Usage Analytics", 
    description: "Dual token system with detailed analytics, quota management, and Prometheus metrics.",
    color: "bg-pink-500"
  },
  {
    icon: Brain,
    title: "Memory Integration",
    description: "Conversation memory with mem0 and ChromaDB for enhanced context and personalization.",
    color: "bg-teal-500"
  },
  {
    icon: Gauge,
    title: "Performance Monitoring",
    description: "Real-time health checks, metrics collection, and comprehensive observability.",
    color: "bg-yellow-500"
  },
  {
    icon: Lock,
    title: "Enterprise Security",
    description: "JWT authentication, API key management, rate limiting, and comprehensive audit logs.",
    color: "bg-gray-600"
  },
  {
    icon: Layers,
    title: "Scalable Architecture",
    description: "Stateless proxy design with Redis caching and PostgreSQL for production deployments.",
    color: "bg-cyan-500"
  },
  {
    icon: Zap,
    title: "High Performance",
    description: "Optimized routing, connection pooling, and streaming responses for minimal latency.",
    color: "bg-amber-500"
  }
]

export default function FeatureGrid() {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
      {features.map((feature, index) => (
        <motion.div
          key={index}
          className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          viewport={{ once: true }}
          whileHover={{ y: -5 }}
        >
          <div className={`${feature.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
            <feature.icon className="w-6 h-6 text-white" />
          </div>
          
          <h3 className="text-xl font-semibold text-gray-900 mb-3">
            {feature.title}
          </h3>
          
          <p className="text-gray-600 leading-relaxed">
            {feature.description}
          </p>
        </motion.div>
      ))}
    </div>
  )
}