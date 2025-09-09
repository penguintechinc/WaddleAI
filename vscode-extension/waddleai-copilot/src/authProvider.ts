import * as vscode from 'vscode';
import axios from 'axios';

/**
 * Authentication Provider for WaddleAI
 * Handles secure storage and validation of API keys
 */
export class AuthenticationProvider implements vscode.AuthenticationProvider {
    private static readonly PROVIDER_ID = 'waddleai-auth';
    private static readonly LABEL = 'WaddleAI';
    
    private _sessions: vscode.AuthenticationSession[] = [];
    private _onDidChangeSessions = new vscode.EventEmitter<vscode.AuthenticationProviderAuthenticationSessionsChangeEvent>();
    
    public readonly onDidChangeSessions = this._onDidChangeSessions.event;

    constructor(private context: vscode.ExtensionContext) {
        this.loadSessions();
    }

    /**
     * Register authentication provider with VS Code
     */
    static register(context: vscode.ExtensionContext): AuthenticationProvider {
        const provider = new AuthenticationProvider(context);
        context.subscriptions.push(
            vscode.authentication.registerAuthenticationProvider(
                AuthenticationProvider.PROVIDER_ID,
                AuthenticationProvider.LABEL,
                provider,
                { supportsMultipleAccounts: false }
            )
        );
        return provider;
    }

    /**
     * Get existing authentication sessions
     */
    async getSessions(scopes?: readonly string[]): Promise<vscode.AuthenticationSession[]> {
        return this._sessions;
    }

    /**
     * Create a new authentication session
     */
    async createSession(scopes: readonly string[]): Promise<vscode.AuthenticationSession> {
        const apiKey = await this.promptForApiKey();
        if (!apiKey) {
            throw new Error('Authentication cancelled');
        }

        // Validate API key with WaddleAI
        const session = await this.validateAndCreateSession(apiKey);
        
        this._sessions.push(session);
        await this.storeSessions();
        
        this._onDidChangeSessions.fire({
            added: [session],
            removed: [],
            changed: []
        });

        return session;
    }

    /**
     * Remove an authentication session
     */
    async removeSession(sessionId: string): Promise<void> {
        const sessionIndex = this._sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex > -1) {
            const session = this._sessions[sessionIndex];
            this._sessions.splice(sessionIndex, 1);
            
            await this.storeSessions();
            
            this._onDidChangeSessions.fire({
                added: [],
                removed: [session],
                changed: []
            });
        }
    }

    /**
     * Prompt user for API key
     */
    private async promptForApiKey(): Promise<string | undefined> {
        const result = await vscode.window.showInputBox({
            title: 'WaddleAI Authentication',
            prompt: 'Enter your WaddleAI API key',
            password: true,
            placeHolder: 'wa-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            ignoreFocusOut: true,
            validateInput: this.validateApiKeyFormat
        });

        return result;
    }

    /**
     * Validate API key format
     */
    private validateApiKeyFormat(apiKey: string): string | undefined {
        if (!apiKey) {
            return 'API key is required';
        }
        
        if (!apiKey.startsWith('wa-')) {
            return 'Invalid API key format. WaddleAI API keys start with "wa-"';
        }
        
        if (apiKey.length < 40) {
            return 'API key appears to be too short';
        }
        
        return undefined;
    }

    /**
     * Validate API key with WaddleAI server and create session
     */
    private async validateAndCreateSession(apiKey: string): Promise<vscode.AuthenticationSession> {
        const config = vscode.workspace.getConfiguration('waddleai');
        const endpoint = config.get<string>('apiEndpoint') || 'http://localhost:8000';
        
        try {
            // Test the API key by making a request to the user info endpoint
            const response = await axios.get(`${endpoint}/v1/user/me`, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            const userData = response.data;
            const sessionId = `waddleai-${Date.now()}`;
            
            const session: vscode.AuthenticationSession = {
                id: sessionId,
                accessToken: apiKey,
                account: {
                    id: userData.user_id?.toString() || 'unknown',
                    label: userData.username || userData.email || 'WaddleAI User'
                },
                scopes: []
            };

            // Store in secure storage
            await this.context.secrets.store(`waddleai.session.${sessionId}`, JSON.stringify({
                apiKey,
                userData,
                createdAt: new Date().toISOString()
            }));

            return session;
            
        } catch (error: any) {
            let errorMessage = 'Failed to authenticate with WaddleAI';
            
            if (error.response) {
                switch (error.response.status) {
                    case 401:
                        errorMessage = 'Invalid API key. Please check your credentials.';
                        break;
                    case 403:
                        errorMessage = 'API key does not have sufficient permissions.';
                        break;
                    case 404:
                        errorMessage = 'WaddleAI endpoint not found. Please check your configuration.';
                        break;
                    case 500:
                        errorMessage = 'WaddleAI server error. Please try again later.';
                        break;
                    default:
                        errorMessage = `Authentication failed: ${error.response.status}`;
                }
            } else if (error.code === 'ECONNREFUSED') {
                errorMessage = 'Cannot connect to WaddleAI server. Please check the endpoint configuration.';
            }
            
            throw new Error(errorMessage);
        }
    }

    /**
     * Load sessions from secure storage
     */
    private async loadSessions(): Promise<void> {
        try {
            const storedSessions = await this.context.globalState.get<string[]>('waddleai.sessionIds', []);
            
            for (const sessionId of storedSessions) {
                try {
                    const sessionDataStr = await this.context.secrets.get(`waddleai.session.${sessionId}`);
                    if (sessionDataStr) {
                        const sessionData = JSON.parse(sessionDataStr);
                        
                        // Reconstruct session
                        const session: vscode.AuthenticationSession = {
                            id: sessionId,
                            accessToken: sessionData.apiKey,
                            account: {
                                id: sessionData.userData.user_id?.toString() || 'unknown',
                                label: sessionData.userData.username || sessionData.userData.email || 'WaddleAI User'
                            },
                            scopes: []
                        };
                        
                        this._sessions.push(session);
                    }
                } catch (error) {
                    console.error(`Failed to load session ${sessionId}:`, error);
                    // Remove invalid session
                    await this.context.secrets.delete(`waddleai.session.${sessionId}`);
                }
            }
            
            // Update stored session IDs to only include valid ones
            await this.storeSessions();
            
        } catch (error) {
            console.error('Failed to load authentication sessions:', error);
        }
    }

    /**
     * Store sessions to secure storage
     */
    private async storeSessions(): Promise<void> {
        const sessionIds = this._sessions.map(s => s.id);
        await this.context.globalState.update('waddleai.sessionIds', sessionIds);
    }

    /**
     * Get the current active session
     */
    async getActiveSession(): Promise<vscode.AuthenticationSession | undefined> {
        return this._sessions[0]; // For now, just return the first session
    }

    /**
     * Refresh a session (validate the API key is still valid)
     */
    async refreshSession(session: vscode.AuthenticationSession): Promise<vscode.AuthenticationSession> {
        try {
            // Validate the existing API key
            const newSession = await this.validateAndCreateSession(session.accessToken);
            
            // Update the session
            const index = this._sessions.findIndex(s => s.id === session.id);
            if (index >= 0) {
                this._sessions[index] = newSession;
                await this.storeSessions();
                
                this._onDidChangeSessions.fire({
                    added: [],
                    removed: [],
                    changed: [newSession]
                });
            }
            
            return newSession;
            
        } catch (error) {
            // If refresh fails, remove the session
            await this.removeSession(session.id);
            throw error;
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return this._sessions.length > 0;
    }

    /**
     * Get API key from active session
     */
    getApiKey(): string | undefined {
        const session = this._sessions[0];
        return session?.accessToken;
    }
}