'use client'

import { motion } from 'framer-motion'
import { Check, ArrowRight, Shield, Cloud, Server, Briefcase, Mail, MessageCircle } from 'lucide-react'

const pricingTiers = [
  {
    id: 'self-hosted',
    name: 'Self-Hosted',
    subtitle: 'Fair Use AGPL3',
    price: 'Free',
    description: 'Open source deployment for individual developers and small teams',
    icon: Server,
    color: 'bg-green-600',
    borderColor: 'border-green-200',
    buttonColor: 'bg-green-600 hover:bg-green-700',
    popular: false,
    features: [
      'Complete WaddleAI platform',
      'OpenAI-compatible API',
      'VS Code extension included',
      'OpenWebUI integration',
      'Community documentation',
      'GitHub Issues support',
      'Fair Use AGPL3 license',
      'Self-managed deployment'
    ],
    support: [
      { type: 'Community Support', icon: MessageCircle, description: 'GitHub Issues and community forums' }
    ],
    cta: 'Get Started',
    ctaLink: 'https://github.com/penguintechinc/waddleai'
  },
  {
    id: 'enterprise-self-hosted',
    name: 'Enterprise Self-Hosted',
    subtitle: 'Priority Support',
    price: 'Contact Sales',
    description: 'Enterprise deployment with commercial license and priority support',
    icon: Shield,
    color: 'bg-blue-600',
    borderColor: 'border-blue-200',
    buttonColor: 'bg-blue-600 hover:bg-blue-700',
    popular: true,
    features: [
      'Everything in Self-Hosted',
      'Commercial license',
      'Priority support portal',
      'Email support',
      'SLA guarantees',
      'Custom integrations',
      'Advanced security features',
      'Deployment assistance'
    ],
    support: [
      { type: 'Priority Portal', icon: Shield, description: 'Dedicated support portal with priority queue' },
      { type: 'Email Support', icon: Mail, description: 'Direct email support with guaranteed response times' }
    ],
    cta: 'Contact Sales',
    ctaLink: 'mailto:sales@penguintech.io'
  },
  {
    id: 'enterprise-cloud',
    name: 'Enterprise Cloud',
    subtitle: 'Fully Managed',
    price: 'Contact Sales',
    description: 'Penguin Technologies hosts and manages WaddleAI for you',
    icon: Cloud,
    color: 'bg-purple-600',
    borderColor: 'border-purple-200',
    buttonColor: 'bg-purple-600 hover:bg-purple-700',
    popular: false,
    features: [
      'Everything in Enterprise Self-Hosted',
      'Fully managed hosting',
      '99.9% uptime SLA',
      'Automatic updates',
      'Global CDN',
      'Advanced monitoring',
      'Backup and disaster recovery',
      'Compliance certifications'
    ],
    support: [
      { type: 'Priority Portal', icon: Shield, description: 'Dedicated support portal with priority queue' },
      { type: 'Email Support', icon: Mail, description: 'Direct email support with guaranteed response times' },
      { type: '24/7 Monitoring', icon: Cloud, description: 'Continuous monitoring and automated incident response' }
    ],
    cta: 'Contact Sales',
    ctaLink: 'mailto:sales@penguintech.io'
  },
  {
    id: 'embedded',
    name: 'Embedded',
    subtitle: 'White Label',
    price: 'Contact Sales',
    description: 'White-label WaddleAI integration for your products and services',
    icon: Briefcase,
    color: 'bg-orange-600',
    borderColor: 'border-orange-200',
    buttonColor: 'bg-orange-600 hover:bg-orange-700',
    popular: false,
    features: [
      'White-label branding',
      'Custom API endpoints',
      'SDK and libraries',
      'Integration support',
      'Revenue sharing options',
      'Co-marketing opportunities',
      'Technical documentation',
      'Developer portal access'
    ],
    support: [
      { type: 'Dedicated Account Manager', icon: Briefcase, description: 'Personal account manager for partnership success' },
      { type: 'Integration Support', icon: Shield, description: 'Technical support for integration and customization' },
      { type: 'Partner Portal', icon: Cloud, description: 'Dedicated partner portal with resources and tools' }
    ],
    cta: 'Contact Sales',
    ctaLink: 'mailto:sales@penguintech.io'
  }
]

const comparisonFeatures = [
  { category: 'Core Features', features: [
    'OpenAI-Compatible API',
    'Multi-LLM Support', 
    'VS Code Extension',
    'OpenWebUI Integration',
    'Security Scanning',
    'Token Management',
    'Usage Analytics'
  ]},
  { category: 'Support & Services', features: [
    'Community Support',
    'Priority Support Portal',
    'Email Support',
    'Phone Support',
    'Custom Integrations',
    'Deployment Assistance',
    'Training & Onboarding'
  ]},
  { category: 'Enterprise Features', features: [
    'Commercial License',
    'SLA Guarantees',
    'Advanced Security',
    'Compliance Certifications',
    'Backup & Recovery',
    'Global CDN',
    'White-label Options'
  ]}
]

export default function Pricing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header Section */}
      <section className="pt-32 pb-20 bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Choose Your WaddleAI Plan
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From open source self-hosting to fully managed enterprise solutions, 
              we have the right plan for your AI infrastructure needs.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-8">
            {pricingTiers.map((tier, index) => (
              <motion.div
                key={tier.id}
                className={`relative bg-white rounded-2xl shadow-xl border-2 ${tier.borderColor} ${
                  tier.popular ? 'ring-4 ring-blue-200 scale-105' : ''
                }`}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-blue-600 text-white px-6 py-2 rounded-full text-sm font-semibold">
                      Most Popular
                    </div>
                  </div>
                )}

                <div className="p-8">
                  <div className="flex items-center mb-6">
                    <div className={`${tier.color} w-12 h-12 rounded-lg flex items-center justify-center mr-4`}>
                      <tier.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                      <p className="text-sm text-gray-500">{tier.subtitle}</p>
                    </div>
                  </div>

                  <div className="mb-6">
                    <div className="text-4xl font-bold text-gray-900 mb-2">
                      {tier.price}
                    </div>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      {tier.description}
                    </p>
                  </div>

                  <div className="mb-8">
                    <h4 className="font-semibold text-gray-900 mb-4">Features included:</h4>
                    <ul className="space-y-3">
                      {tier.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center">
                          <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                          <span className="text-gray-700 text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="mb-8">
                    <h4 className="font-semibold text-gray-900 mb-4">Support included:</h4>
                    <div className="space-y-3">
                      {tier.support.map((support, supportIndex) => (
                        <div key={supportIndex} className="flex items-start">
                          <support.icon className="w-4 h-4 text-gray-500 mr-3 mt-1 flex-shrink-0" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">{support.type}</div>
                            <div className="text-xs text-gray-600">{support.description}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <a
                    href={tier.ctaLink}
                    className={`w-full ${tier.buttonColor} text-white py-3 px-6 rounded-lg font-semibold transition-colors duration-200 flex items-center justify-center group`}
                    target={tier.ctaLink.startsWith('mailto:') ? undefined : '_blank'}
                    rel={tier.ctaLink.startsWith('mailto:') ? undefined : 'noopener noreferrer'}
                  >
                    {tier.cta}
                    <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </a>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Comparison Table */}
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
              Features Comparison
            </h2>
            <p className="text-xl text-gray-600">
              Compare features across all WaddleAI plans to find the right fit
            </p>
          </motion.div>

          <motion.div
            className="overflow-x-auto shadow-2xl rounded-2xl"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
          >
            <table className="w-full bg-white">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 w-1/4">
                    Features
                  </th>
                  {pricingTiers.map((tier) => (
                    <th key={tier.id} className="px-6 py-4 text-center text-sm font-semibold text-gray-900 w-1/6">
                      <div className="flex flex-col items-center">
                        <div className={`${tier.color} w-8 h-8 rounded-lg flex items-center justify-center mb-2`}>
                          <tier.icon className="w-4 h-4 text-white" />
                        </div>
                        <div>{tier.name}</div>
                        <div className="text-xs text-gray-500 font-normal">{tier.subtitle}</div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* Core Features */}
                <tr className="bg-blue-50">
                  <td className="px-6 py-3 text-sm font-semibold text-blue-900" colSpan={5}>
                    Core Platform Features
                  </td>
                </tr>
                {[
                  'OpenAI-Compatible API',
                  'Multi-LLM Support (GPT, Claude, LLaMA)',
                  'VS Code Extension',
                  'OpenWebUI Integration', 
                  'Security Scanning & Prompt Injection Detection',
                  'Token Management & Usage Analytics',
                  'Conversation Memory Integration',
                  'Role-Based Access Control'
                ].map((feature, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 text-sm text-gray-900">{feature}</td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                    </td>
                  </tr>
                ))}

                {/* Licensing & Commercial Use */}
                <tr className="bg-purple-50">
                  <td className="px-6 py-3 text-sm font-semibold text-purple-900" colSpan={5}>
                    Licensing & Commercial Use
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Open Source (AGPL3)</td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Commercial License</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">White-Label/Rebranding Rights</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>

                {/* Support & Services */}
                <tr className="bg-green-50">
                  <td className="px-6 py-3 text-sm font-semibold text-green-900" colSpan={5}>
                    Support & Services
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Community Support (GitHub Issues)</td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Priority Support Portal</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Email Support with SLA</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Deployment Assistance</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Dedicated Account Manager</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>

                {/* Infrastructure & Hosting */}
                <tr className="bg-orange-50">
                  <td className="px-6 py-3 text-sm font-semibold text-orange-900" colSpan={5}>
                    Infrastructure & Hosting
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Self-Managed Deployment</td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm text-gray-600">Optional</span>
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Fully Managed Hosting</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm text-gray-600">Optional</span>
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">99.9% Uptime SLA</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Global CDN & Edge Caching</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Automatic Backups & Disaster Recovery</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>

                {/* Advanced Features */}
                <tr className="bg-indigo-50">
                  <td className="px-6 py-3 text-sm font-semibold text-indigo-900" colSpan={5}>
                    Advanced Features
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Custom Integrations & SDKs</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">Advanced Security & Compliance</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm text-gray-600">Basic</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
                <tr className="bg-white">
                  <td className="px-6 py-4 text-sm text-gray-900">Revenue Sharing Opportunities</td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Check className="w-5 h-5 text-green-500 mx-auto" />
                  </td>
                </tr>
              </tbody>
            </table>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
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
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Common questions about WaddleAI pricing and deployment options
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
            {[
              {
                question: "What's included in the AGPL3 Fair Use license?",
                answer: "The AGPL3 Fair Use license allows free use of WaddleAI for personal, educational, and small commercial projects. You must open source any modifications and provide the same license to users. Fair use means reasonable usage without commercial redistribution."
              },
              {
                question: "How does Enterprise Self-Hosted differ from the free version?",
                answer: "Enterprise Self-Hosted includes a commercial license (no need to open source your modifications), priority support portal, email support with SLA guarantees, custom integrations, and deployment assistance."
              },
              {
                question: "What does 'Fully Managed' mean for Enterprise Cloud?",
                answer: "Penguin Technologies hosts, monitors, updates, and maintains your WaddleAI instance. You get 99.9% uptime SLA, automatic updates, global CDN, backup and disaster recovery, all without managing infrastructure."
              },
              {
                question: "How does the Embedded/White-label option work?",
                answer: "The Embedded option allows you to integrate WaddleAI into your products with your branding. Includes custom API endpoints, SDKs, revenue sharing options, and dedicated partnership support."
              },
              {
                question: "Can I upgrade between plans?",
                answer: "Yes, you can upgrade from Self-Hosted to any Enterprise plan, or from Enterprise Self-Hosted to Enterprise Cloud. Contact sales@penguintech.io for migration assistance."
              },
              {
                question: "What kind of support response times can I expect?",
                answer: "Self-Hosted gets community support via GitHub. Enterprise plans get priority portal support with 4-hour response times, and email support with 24-hour response times during business hours."
              }
            ].map((faq, index) => (
              <motion.div
                key={index}
                className="bg-white rounded-xl p-6 shadow-lg"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {faq.question}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-20 bg-primary-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold mb-6">
              Ready to Get Started?
            </h2>
            <p className="text-xl mb-8 text-primary-200 max-w-3xl mx-auto">
              Questions about which plan is right for you? Our team is here to help you choose 
              the best WaddleAI deployment option for your needs.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:sales@penguintech.io"
                className="bg-white text-primary-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center justify-center"
              >
                <Mail className="mr-2 w-5 h-5" />
                Contact Sales
              </a>
              <a
                href="https://github.com/penguintechinc/waddleai"
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-900 transition-colors inline-flex items-center justify-center"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Server className="mr-2 w-5 h-5" />
                Try Self-Hosted
              </a>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}