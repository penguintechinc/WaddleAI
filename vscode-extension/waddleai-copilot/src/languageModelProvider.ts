import * as vscode from 'vscode';
import { WaddleAIClient } from './waddleaiClient';

/**
 * WaddleAI Language Model Provider for VS Code Copilot Chat
 * This provider integrates WaddleAI's proxy service with VS Code's language model API
 */
export class WaddleAILanguageModelProvider implements vscode.LanguageModelChatProvider {
    public readonly id = 'waddleai';
    public readonly name = 'WaddleAI';
    public readonly vendor = 'WaddleAI';
    
    private models: vscode.LanguageModelChatSelector[] = [];
    
    constructor(
        private client: WaddleAIClient,
        private context: vscode.ExtensionContext
    ) {
        this.initializeModels();
    }

    private async initializeModels() {
        try {
            const availableModels = await this.client.getAvailableModels();
            this.models = availableModels.map(model => ({
                id: `waddleai/${model.id}`,
                vendor: 'WaddleAI',
                family: this.getModelFamily(model.id),
                version: model.version || '1.0',
                maxInputTokens: model.maxInputTokens || 8192,
                maxOutputTokens: model.maxOutputTokens || 4096
            }));
        } catch (error) {
            console.error('Failed to initialize WaddleAI models:', error);
            // Fallback to default models
            this.models = this.getDefaultModels();
        }
    }

    private getModelFamily(modelId: string): string {
        if (modelId.includes('gpt')) return 'gpt';
        if (modelId.includes('claude')) return 'claude';
        if (modelId.includes('llama')) return 'llama';
        if (modelId.includes('codellama')) return 'codellama';
        return 'general';
    }

    private getDefaultModels(): vscode.LanguageModelChatSelector[] {
        return [
            {
                id: 'waddleai/gpt-4',
                vendor: 'WaddleAI',
                family: 'gpt',
                version: '4.0',
                maxInputTokens: 8192,
                maxOutputTokens: 4096
            },
            {
                id: 'waddleai/gpt-3.5-turbo',
                vendor: 'WaddleAI',
                family: 'gpt',
                version: '3.5',
                maxInputTokens: 4096,
                maxOutputTokens: 2048
            },
            {
                id: 'waddleai/claude-3-opus',
                vendor: 'WaddleAI',
                family: 'claude',
                version: '3.0',
                maxInputTokens: 100000,
                maxOutputTokens: 4096
            },
            {
                id: 'waddleai/llama2',
                vendor: 'WaddleAI',
                family: 'llama',
                version: '2.0',
                maxInputTokens: 4096,
                maxOutputTokens: 2048
            }
        ];
    }

    /**
     * Provide available models to VS Code
     */
    async provideLanguageModelChatResponse(
        messages: vscode.LanguageModelChatMessage[],
        options: vscode.LanguageModelChatRequestOptions,
        extensionToken: vscode.ExtensionContext,
        progress: vscode.Progress<vscode.LanguageModelChatResponseStream>,
        token: vscode.CancellationToken
    ): Promise<vscode.LanguageModelChatResponse> {
        
        // Extract model from options or use default
        const config = vscode.workspace.getConfiguration('waddleai');
        const modelId = options.modelId?.replace('waddleai/', '') || config.get<string>('defaultModel') || 'gpt-4';
        
        // Convert VS Code messages to OpenAI format
        const openAIMessages = this.convertMessages(messages);
        
        // Add system message for code context if available
        if (options.justification) {
            openAIMessages.unshift({
                role: 'system',
                content: `Context: ${options.justification}`
            });
        }

        try {
            // Check for cancellation
            if (token.isCancellationRequested) {
                throw new vscode.CancellationError();
            }

            // Stream the response from WaddleAI
            const stream = await this.client.streamChatCompletion(
                openAIMessages,
                modelId,
                {
                    temperature: config.get<number>('temperature') || 0.7,
                    max_tokens: config.get<number>('maxTokens') || 2048,
                    stream: true
                }
            );

            let fullResponse = '';
            let tokenCount = 0;

            // Process the stream
            for await (const chunk of stream) {
                if (token.isCancellationRequested) {
                    throw new vscode.CancellationError();
                }

                const delta = chunk.choices?.[0]?.delta?.content;
                if (delta) {
                    fullResponse += delta;
                    tokenCount += this.estimateTokens(delta);
                    
                    // Report progress
                    progress.report({
                        index: 0,
                        part: delta
                    });
                }
            }

            // Return the complete response
            return {
                text: fullResponse,
                messages: [{
                    role: vscode.LanguageModelChatMessageRole.Assistant,
                    content: fullResponse
                }]
            };

        } catch (error: any) {
            if (error instanceof vscode.CancellationError) {
                throw error;
            }
            
            // Handle API errors
            if (error.response?.status === 401) {
                vscode.window.showErrorMessage(
                    'WaddleAI authentication failed. Please check your API key.',
                    'Set API Key'
                ).then(selection => {
                    if (selection === 'Set API Key') {
                        vscode.commands.executeCommand('waddleai.setApiKey');
                    }
                });
            } else if (error.response?.status === 429) {
                vscode.window.showErrorMessage(
                    'WaddleAI rate limit exceeded. Please try again later.'
                );
            } else {
                vscode.window.showErrorMessage(
                    `WaddleAI error: ${error.message}`
                );
            }
            
            throw error;
        }
    }

    /**
     * Convert VS Code chat messages to OpenAI format
     */
    private convertMessages(messages: vscode.LanguageModelChatMessage[]): any[] {
        return messages.map(msg => {
            let role: string;
            switch (msg.role) {
                case vscode.LanguageModelChatMessageRole.User:
                    role = 'user';
                    break;
                case vscode.LanguageModelChatMessageRole.Assistant:
                    role = 'assistant';
                    break;
                default:
                    role = 'system';
            }

            // Handle different content types
            if (typeof msg.content === 'string') {
                return {
                    role,
                    content: msg.content
                };
            } else if (Array.isArray(msg.content)) {
                // Handle multimodal content
                const parts = msg.content.map((part: any) => {
                    if (part.type === 'text') {
                        return { type: 'text', text: part.value };
                    } else if (part.type === 'image') {
                        return { 
                            type: 'image_url', 
                            image_url: { 
                                url: part.value,
                                detail: 'auto'
                            }
                        };
                    }
                    return part;
                });
                
                return {
                    role,
                    content: parts
                };
            }

            return {
                role,
                content: String(msg.content)
            };
        });
    }

    /**
     * Simple token estimation
     */
    private estimateTokens(text: string): number {
        // Rough estimation: 1 token per 4 characters
        return Math.ceil(text.length / 4);
    }

    /**
     * Get available models
     */
    async getModels(): Promise<vscode.LanguageModelChatSelector[]> {
        if (this.models.length === 0) {
            await this.initializeModels();
        }
        return this.models;
    }

    /**
     * Prepare a chat request with context
     */
    async prepareRequest(
        messages: vscode.LanguageModelChatMessage[],
        context?: vscode.ChatContext
    ): Promise<any> {
        const config = vscode.workspace.getConfiguration('waddleai');
        
        // Add workspace context if available
        const contextMessages: any[] = [];
        
        if (context?.history) {
            // Include relevant history
            const recentHistory = context.history.slice(-5); // Last 5 messages
            for (const turn of recentHistory) {
                if (turn.prompt) {
                    contextMessages.push({
                        role: 'user',
                        content: turn.prompt
                    });
                }
                if (turn.response) {
                    contextMessages.push({
                        role: 'assistant',
                        content: turn.response.toString()
                    });
                }
            }
        }

        // Add current workspace information
        if (vscode.workspace.workspaceFolders) {
            const workspaceInfo = vscode.workspace.workspaceFolders
                .map(f => f.name)
                .join(', ');
            
            contextMessages.unshift({
                role: 'system',
                content: `Current workspace: ${workspaceInfo}`
            });
        }

        // Add active file context
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            const doc = activeEditor.document;
            const selection = activeEditor.selection;
            
            if (!selection.isEmpty) {
                const selectedText = doc.getText(selection);
                contextMessages.push({
                    role: 'system',
                    content: `Selected code in ${doc.languageId}:\n\`\`\`${doc.languageId}\n${selectedText}\n\`\`\``
                });
            }
        }

        return {
            messages: [...contextMessages, ...this.convertMessages(messages)],
            model: config.get<string>('defaultModel') || 'gpt-4',
            temperature: config.get<number>('temperature') || 0.7,
            max_tokens: config.get<number>('maxTokens') || 2048,
            enable_memory: config.get<boolean>('enableMemory') || true,
            enable_security: config.get<boolean>('enableSecurityScanning') || true
        };
    }
}