import * as vscode from 'vscode';
import axios, { AxiosInstance } from 'axios';
import { EventEmitter } from 'events';

/**
 * WaddleAI API Client
 * Handles all communication with the WaddleAI proxy server
 */
export class WaddleAIClient extends EventEmitter {
    private axiosInstance: AxiosInstance;
    private apiKey: string | undefined;
    private endpoint: string;
    private sessionId: string;

    constructor(private context: vscode.ExtensionContext) {
        super();
        
        const config = vscode.workspace.getConfiguration('waddleai');
        this.endpoint = config.get<string>('apiEndpoint') || 'http://localhost:8000';
        this.sessionId = this.generateSessionId();
        
        // Initialize axios instance
        this.axiosInstance = axios.create({
            baseURL: this.endpoint,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'X-Session-Id': this.sessionId,
                'X-Client': 'vscode-extension',
                'X-Client-Version': this.getExtensionVersion()
            }
        });

        // Load API key from secure storage or config
        this.loadApiKey();

        // Set up request interceptor for authentication
        this.axiosInstance.interceptors.request.use(
            (config) => {
                if (this.apiKey) {
                    config.headers['Authorization'] = `Bearer ${this.apiKey}`;
                }
                return config;
            },
            (error) => {
                return Promise.reject(error);
            }
        );

        // Set up response interceptor for error handling
        this.axiosInstance.interceptors.response.use(
            (response) => response,
            async (error) => {
                if (error.response?.status === 401) {
                    // Token might be expired, try to refresh
                    await this.handleAuthError();
                }
                return Promise.reject(error);
            }
        );
    }

    private async loadApiKey() {
        // Try to load from secure storage first
        this.apiKey = await this.context.secrets.get('waddleai.apiKey');
        
        // Fallback to configuration
        if (!this.apiKey) {
            const config = vscode.workspace.getConfiguration('waddleai');
            this.apiKey = config.get<string>('apiKey');
        }
    }

    private generateSessionId(): string {
        return `vscode-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    private getExtensionVersion(): string {
        const packageJson = this.context.extension.packageJSON;
        return packageJson.version || '0.0.0';
    }

    private async handleAuthError() {
        const action = await vscode.window.showErrorMessage(
            'WaddleAI authentication failed. Please update your API key.',
            'Update API Key',
            'Cancel'
        );
        
        if (action === 'Update API Key') {
            await vscode.commands.executeCommand('waddleai.setApiKey');
            await this.loadApiKey();
        }
    }

    /**
     * Test connection to WaddleAI proxy
     */
    async testConnection(): Promise<any> {
        try {
            const response = await this.axiosInstance.get('/health');
            return response.data;
        } catch (error: any) {
            throw new Error(`Connection failed: ${error.message}`);
        }
    }

    /**
     * Get available models from WaddleAI
     */
    async getAvailableModels(): Promise<any[]> {
        try {
            const response = await this.axiosInstance.get('/v1/models');
            return response.data.data || [];
        } catch (error: any) {
            console.error('Failed to fetch models:', error);
            return [];
        }
    }

    /**
     * Stream chat completion from WaddleAI
     */
    async streamChatCompletion(
        messages: any[],
        model: string,
        options: any = {}
    ): Promise<AsyncIterable<any>> {
        const requestBody = {
            model,
            messages,
            stream: true,
            ...options
        };

        try {
            const response = await this.axiosInstance.post('/v1/chat/completions', requestBody, {
                responseType: 'stream'
            });

            return this.parseSSEStream(response.data);
        } catch (error: any) {
            throw new Error(`Chat completion failed: ${error.message}`);
        }
    }

    /**
     * Parse SSE stream from OpenAI-compatible API
     */
    private async* parseSSEStream(stream: any): AsyncIterable<any> {
        let buffer = '';
        
        for await (const chunk of stream) {
            buffer += chunk.toString();
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        return;
                    }
                    
                    try {
                        const parsed = JSON.parse(data);
                        yield parsed;
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e);
                    }
                }
            }
        }
    }

    /**
     * Regular chat completion (non-streaming)
     */
    async chatCompletion(
        messages: any[],
        model: string,
        options: any = {}
    ): Promise<any> {
        const requestBody = {
            model,
            messages,
            stream: false,
            ...options
        };

        try {
            const response = await this.axiosInstance.post('/v1/chat/completions', requestBody);
            return response.data;
        } catch (error: any) {
            throw new Error(`Chat completion failed: ${error.message}`);
        }
    }

    /**
     * Get token usage statistics
     */
    async getUsage(days: number = 30): Promise<any> {
        try {
            const response = await this.axiosInstance.get('/v1/usage', {
                params: { days }
            });
            
            // Transform the response for display
            const usage = response.data;
            return {
                total_tokens: usage.total_tokens || 0,
                total_requests: usage.total_requests || 0,
                used_today: usage.daily_usage?.today || 0,
                used_month: usage.monthly_usage?.current || 0,
                daily_limit: usage.quotas?.daily || 10000,
                monthly_limit: usage.quotas?.monthly || 300000,
                period_days: days
            };
        } catch (error: any) {
            throw new Error(`Failed to fetch usage: ${error.message}`);
        }
    }

    /**
     * Clear conversation memory
     */
    async clearMemory(): Promise<void> {
        try {
            await this.axiosInstance.post('/v1/memory/clear', {
                session_id: this.sessionId
            });
        } catch (error: any) {
            throw new Error(`Failed to clear memory: ${error.message}`);
        }
    }

    /**
     * Get conversation history
     */
    async getHistory(limit: number = 10): Promise<any[]> {
        try {
            const response = await this.axiosInstance.get('/v1/memory/history', {
                params: {
                    session_id: this.sessionId,
                    limit
                }
            });
            return response.data.history || [];
        } catch (error: any) {
            console.error('Failed to fetch history:', error);
            return [];
        }
    }

    /**
     * Send telemetry data
     */
    async sendTelemetry(event: string, properties: any = {}): Promise<void> {
        try {
            await this.axiosInstance.post('/v1/telemetry', {
                event,
                properties: {
                    ...properties,
                    session_id: this.sessionId,
                    client: 'vscode-extension',
                    timestamp: new Date().toISOString()
                }
            });
        } catch (error) {
            // Silently fail telemetry
            console.debug('Telemetry failed:', error);
        }
    }

    /**
     * Update configuration
     */
    async updateConfiguration(newEndpoint?: string, newApiKey?: string) {
        if (newEndpoint && newEndpoint !== this.endpoint) {
            this.endpoint = newEndpoint;
            this.axiosInstance.defaults.baseURL = newEndpoint;
        }
        
        if (newApiKey && newApiKey !== this.apiKey) {
            this.apiKey = newApiKey;
            await this.context.secrets.store('waddleai.apiKey', newApiKey);
        }
    }

    /**
     * Dispose of resources
     */
    dispose() {
        this.removeAllListeners();
    }
}