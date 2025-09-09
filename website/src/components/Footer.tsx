'use client'

import { motion } from 'framer-motion'
import { Github, Twitter, Linkedin, Mail, ExternalLink } from 'lucide-react'

export default function Footer() {
  const footerSections = [
    {
      title: 'Product',
      links: [
        { name: 'Features', href: '#features' },
        { name: 'Solutions', href: '/solutions' },
        { name: 'Pricing', href: '/pricing' },
        { name: 'VS Code Extension', href: 'https://docs.waddlebot.ai/integrations/vscode-extension' },
        { name: 'OpenWebUI Integration', href: 'https://docs.waddlebot.ai/testing-setup' },
      ]
    },
    {
      title: 'Integrations',
      links: [
        { name: 'OpenAI API', href: 'https://docs.waddlebot.ai/api/openai-compatible' },
        { name: 'VS Code', href: 'https://docs.waddlebot.ai/integrations/vscode-extension' },
        { name: 'OpenWebUI', href: 'https://docs.waddlebot.ai/testing-setup' },
        { name: 'Docker', href: 'https://docs.waddlebot.ai/deployment/docker' },
        { name: 'Kubernetes', href: 'https://docs.waddlebot.ai/deployment/kubernetes' },
      ]
    },
    {
      title: 'Resources',
      links: [
        { name: 'Documentation', href: 'https://docs.waddlebot.ai' },
        { name: 'Getting Started', href: 'https://docs.waddlebot.ai/getting-started' },
        { name: 'Testing Setup', href: 'https://docs.waddlebot.ai/testing-setup' },
        { name: 'Troubleshooting', href: 'https://docs.waddlebot.ai/troubleshooting' },
        { name: 'Community', href: '/community' },
      ]
    },
    {
      title: 'Company',
      links: [
        { name: 'About', href: '/about' },
        { name: 'Blog', href: '/blog' },
        { name: 'Careers', href: '/careers' },
        { name: 'Contact', href: '/contact' },
        { name: 'Privacy Policy', href: '/privacy' },
      ]
    }
  ]

  const socialLinks = [
    { name: 'GitHub', href: 'https://github.com/penguintechinc/waddleai', icon: Github },
    { name: 'Twitter', href: 'https://ptg.best/twitter', icon: Twitter },
    { name: 'LinkedIn', href: 'https://ptg.best/linkedin', icon: Linkedin },
    { name: 'Email', href: 'mailto:sales@penguintech.io', icon: Mail },
  ]

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Company Info */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h3 className="text-2xl font-bold text-white mb-4">WaddleAI</h3>
              <p className="text-gray-400 mb-6 leading-relaxed">
                Enterprise-grade AI proxy with OpenAI-compatible APIs, VS Code integration, 
                and comprehensive management capabilities.
              </p>
              
              <div className="flex space-x-4">
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    className="text-gray-400 hover:text-white transition-colors"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <social.icon className="w-5 h-5" />
                  </a>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Footer Sections */}
          {footerSections.map((section, index) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              <h4 className="text-lg font-semibold text-white mb-4">
                {section.title}
              </h4>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      className="text-gray-400 hover:text-white transition-colors duration-200 flex items-center"
                    >
                      {link.name}
                      {link.href.startsWith('http') && (
                        <ExternalLink className="ml-1 w-3 h-3" />
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Newsletter Signup */}
        <motion.div
          className="mt-12 pt-8 border-t border-gray-800"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <div className="md:flex md:items-center md:justify-between">
            <div className="md:flex-1">
              <h4 className="text-lg font-semibold text-white mb-2">
                Stay Updated
              </h4>
              <p className="text-gray-400 mb-4 md:mb-0">
                Get the latest updates on WaddleAI features, integrations, and best practices.
              </p>
            </div>
            
            <div className="md:ml-8 md:flex-shrink-0">
              <form className="flex gap-3">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors duration-200"
                >
                  Subscribe
                </button>
              </form>
            </div>
          </div>
        </motion.div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-gray-800">
          <div className="md:flex md:items-center md:justify-between">
            <p className="text-gray-400 text-sm">
              © 2024 WaddleAI. All rights reserved.
            </p>
            
            <div className="mt-4 md:mt-0">
              <div className="flex items-center space-x-6 text-sm text-gray-400">
                <a href="/terms" className="hover:text-white transition-colors">
                  Terms of Service
                </a>
                <a href="/privacy" className="hover:text-white transition-colors">
                  Privacy Policy
                </a>
                <a href="/cookies" className="hover:text-white transition-colors">
                  Cookie Policy
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}