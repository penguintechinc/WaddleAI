import * as vscode from 'vscode';
import { WaddleAIClient } from './waddleaiClient';

/**
 * WaddleAI Chat Participant for VS Code Chat
 * This integrates WaddleAI as a chat participant in VS Code's chat interface
 */
export class WaddleAIChatParticipant {
    constructor(
        private client: WaddleAIClient,
        private context: vscode.ExtensionContext
    ) {}

    /**
     * Handle chat requests from VS Code
     */
    async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        try {
            // Get configuration
            const config = vscode.workspace.getConfiguration('waddleai');
            const modelId = config.get<string>('defaultModel') || 'gpt-4';

            // Convert request to messages format
            const messages = this.buildMessages(request, context);

            // Check for cancellation
            if (token.isCancellationRequested) {
                return;
            }

            // Send request to WaddleAI
            const chatStream = await this.client.streamChatCompletion(
                messages,
                modelId,
                {
                    temperature: config.get<number>('temperature') || 0.7,
                    max_tokens: config.get<number>('maxTokens') || 2048,
                    enable_memory: config.get<boolean>('enableMemory') || true,
                    enable_security: config.get<boolean>('enableSecurityScanning') || true
                }
            );

            // Stream the response
            for await (const chunk of chatStream) {
                if (token.isCancellationRequested) {
                    return;
                }

                const content = chunk.choices?.[0]?.delta?.content;
                if (content) {
                    stream.markdown(content);
                }
            }

            // Add reference to WaddleAI
            stream.button({
                command: 'waddleai.showUsage',
                title: 'View Usage',
                tooltip: 'View your WaddleAI token usage'
            });

        } catch (error: any) {
            // Handle errors gracefully
            if (error instanceof vscode.CancellationError) {
                return;
            }
            
            let errorMessage = 'WaddleAI request failed';
            
            if (error.response?.status === 401) {
                errorMessage = 'Authentication failed. Please check your API key.';
                stream.button({
                    command: 'waddleai.setApiKey',
                    title: 'Set API Key',
                    tooltip: 'Configure your WaddleAI API key'
                });
            } else if (error.response?.status === 429) {
                errorMessage = 'Rate limit exceeded. Please try again later.';
            } else if (error.response?.status === 503) {
                errorMessage = 'WaddleAI service unavailable. Please try again later.';
            } else if (error.message) {
                errorMessage = `WaddleAI error: ${error.message}`;
            }
            
            stream.markdown(`❌ ${errorMessage}`);
        }
    }

    /**
     * Build messages array from chat request and context
     */
    private buildMessages(request: vscode.ChatRequest, context: vscode.ChatContext): any[] {
        const messages: any[] = [];

        // Add system message with context
        const systemContext = this.buildSystemContext();
        if (systemContext) {
            messages.push({
                role: 'system',
                content: systemContext
            });
        }

        // Add conversation history
        if (context.history.length > 0) {
            const recentHistory = context.history.slice(-5); // Last 5 exchanges
            
            for (const turn of recentHistory) {
                if (turn instanceof vscode.ChatRequestTurn) {
                    messages.push({
                        role: 'user',
                        content: turn.prompt
                    });
                } else if (turn instanceof vscode.ChatResponseTurn) {
                    // Convert response to string
                    const responseText = this.responseToString(turn.response);
                    if (responseText) {
                        messages.push({
                            role: 'assistant',
                            content: responseText
                        });
                    }
                }
            }
        }

        // Add current request
        messages.push({
            role: 'user',
            content: request.prompt
        });

        return messages;
    }

    /**
     * Build system context message
     */
    private buildSystemContext(): string {
        const contextParts: string[] = [];

        // Add workspace information
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            const workspaceNames = vscode.workspace.workspaceFolders.map(f => f.name).join(', ');
            contextParts.push(`Current workspace: ${workspaceNames}`);
        }

        // Add active file context
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            const doc = activeEditor.document;
            contextParts.push(`Active file: ${doc.fileName} (${doc.languageId})`);

            // Add selected code if any
            const selection = activeEditor.selection;
            if (!selection.isEmpty) {
                const selectedText = doc.getText(selection);
                if (selectedText.length < 2000) { // Limit context size
                    contextParts.push(`Selected code:\n\`\`\`${doc.languageId}\n${selectedText}\n\`\`\``);
                }
            }
        }

        // Add configuration context
        const config = vscode.workspace.getConfiguration('waddleai');
        const modelId = config.get<string>('defaultModel');
        if (modelId) {
            contextParts.push(`Using model: ${modelId}`);
        }

        return contextParts.length > 0 ? contextParts.join('\n\n') : '';
    }

    /**
     * Convert chat response to string
     */
    private responseToString(response: ReadonlyArray<vscode.ChatResponseMarkdownPart | vscode.ChatResponseFileTreePart | vscode.ChatResponseAnchorPart | vscode.ChatResponseCommandButtonPart>): string {
        return response
            .filter(part => part instanceof vscode.ChatResponseMarkdownPart)
            .map(part => (part as vscode.ChatResponseMarkdownPart).value.value)
            .join('');
    }

    /**
     * Get available models from WaddleAI
     */
    async getAvailableModels(): Promise<string[]> {
        try {
            const models = await this.client.getAvailableModels();
            return models.map(m => m.id);
        } catch (error) {
            console.error('Failed to fetch models:', error);
            return ['gpt-4', 'gpt-3.5-turbo', 'claude-3-sonnet', 'llama2'];
        }
    }

    /**
     * Handle model selection
     */
    async selectModel(): Promise<void> {
        try {
            const models = await this.getAvailableModels();
            const selected = await vscode.window.showQuickPick(models, {
                placeHolder: 'Select a WaddleAI model',
                title: 'WaddleAI Model Selection'
            });

            if (selected) {
                const config = vscode.workspace.getConfiguration('waddleai');
                await config.update('defaultModel', selected, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage(`WaddleAI model set to: ${selected}`);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to select model: ${error.message}`);
        }
    }
}