import * as vscode from 'vscode';
import { WaddleAILanguageModelProvider } from './languageModelProvider';
import { WaddleAIClient } from './waddleaiClient';
import { AuthenticationProvider } from './authProvider';

let waddleAIClient: WaddleAIClient;
let authProvider: AuthenticationProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('WaddleAI Copilot extension is now active!');

    // Initialize authentication provider
    authProvider = new AuthenticationProvider(context);
    
    // Initialize WaddleAI client
    waddleAIClient = new WaddleAIClient(context);

    // Register the language model provider for Copilot Chat
    const provider = new WaddleAILanguageModelProvider(waddleAIClient, context);
    
    // Register with VS Code's language model API
    const registration = vscode.lm.registerLanguageModelProvider(
        'waddleai',
        provider
    );
    context.subscriptions.push(registration);

    // Register commands
    registerCommands(context);

    // Show welcome message on first activation
    const hasShownWelcome = context.globalState.get('waddleai.welcomeShown');
    if (!hasShownWelcome) {
        showWelcomeMessage(context);
    }

    // Auto-configure if API key is not set
    const config = vscode.workspace.getConfiguration('waddleai');
    const apiKey = config.get<string>('apiKey');
    if (!apiKey) {
        vscode.window.showInformationMessage(
            'WaddleAI: Please set your API key to start using WaddleAI in Copilot Chat',
            'Set API Key'
        ).then(selection => {
            if (selection === 'Set API Key') {
                vscode.commands.executeCommand('waddleai.setApiKey');
            }
        });
    }
}

function registerCommands(context: vscode.ExtensionContext) {
    // Set API Key command
    const setApiKeyCommand = vscode.commands.registerCommand('waddleai.setApiKey', async () => {
        const apiKey = await vscode.window.showInputBox({
            prompt: 'Enter your WaddleAI API key',
            password: true,
            placeHolder: 'wa-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            validateInput: (value) => {
                if (!value) {
                    return 'API key is required';
                }
                if (!value.startsWith('wa-')) {
                    return 'Invalid API key format. Should start with "wa-"';
                }
                return null;
            }
        });

        if (apiKey) {
            const config = vscode.workspace.getConfiguration('waddleai');
            await config.update('apiKey', apiKey, vscode.ConfigurationTarget.Global);
            
            // Store securely in secret storage
            await context.secrets.store('waddleai.apiKey', apiKey);
            
            vscode.window.showInformationMessage('WaddleAI API key saved successfully!');
            
            // Test connection
            vscode.commands.executeCommand('waddleai.testConnection');
        }
    });

    // Select Model command
    const selectModelCommand = vscode.commands.registerCommand('waddleai.selectModel', async () => {
        // Fetch available models from WaddleAI
        try {
            const models = await waddleAIClient.getAvailableModels();
            const modelNames = models.map(m => m.id);
            
            const selected = await vscode.window.showQuickPick(modelNames, {
                placeHolder: 'Select a model to use with WaddleAI',
                title: 'WaddleAI Model Selection'
            });

            if (selected) {
                const config = vscode.workspace.getConfiguration('waddleai');
                await config.update('defaultModel', selected, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage(`WaddleAI: Model set to ${selected}`);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to fetch models: ${error.message}`);
        }
    });

    // Test Connection command
    const testConnectionCommand = vscode.commands.registerCommand('waddleai.testConnection', async () => {
        const progress = vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Testing WaddleAI connection...',
            cancellable: false
        }, async () => {
            try {
                const health = await waddleAIClient.testConnection();
                if (health.status === 'healthy') {
                    vscode.window.showInformationMessage('✅ WaddleAI connection successful!');
                    return true;
                } else {
                    vscode.window.showWarningMessage(`⚠️ WaddleAI is ${health.status}`);
                    return false;
                }
            } catch (error: any) {
                vscode.window.showErrorMessage(`❌ WaddleAI connection failed: ${error.message}`);
                return false;
            }
        });
        
        return progress;
    });

    // Show Usage command
    const showUsageCommand = vscode.commands.registerCommand('waddleai.showUsage', async () => {
        try {
            const usage = await waddleAIClient.getUsage();
            
            const panel = vscode.window.createWebviewPanel(
                'waddleaiUsage',
                'WaddleAI Token Usage',
                vscode.ViewColumn.One,
                {
                    enableScripts: true
                }
            );

            panel.webview.html = getUsageWebviewContent(usage);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to fetch usage: ${error.message}`);
        }
    });

    // Clear Memory command
    const clearMemoryCommand = vscode.commands.registerCommand('waddleai.clearMemory', async () => {
        const confirm = await vscode.window.showWarningMessage(
            'Are you sure you want to clear conversation memory?',
            'Yes', 'No'
        );
        
        if (confirm === 'Yes') {
            try {
                await waddleAIClient.clearMemory();
                vscode.window.showInformationMessage('Conversation memory cleared successfully');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to clear memory: ${error.message}`);
            }
        }
    });

    context.subscriptions.push(
        setApiKeyCommand,
        selectModelCommand,
        testConnectionCommand,
        showUsageCommand,
        clearMemoryCommand
    );
}

function showWelcomeMessage(context: vscode.ExtensionContext) {
    const message = `Welcome to WaddleAI for Copilot Chat! 🎉
    
    WaddleAI is now available as a language model provider in VS Code.
    You can use it in Copilot Chat by selecting "WaddleAI" from the model dropdown.
    
    To get started:
    1. Set your API key: Command Palette > "WaddleAI: Set API Key"
    2. Select a model: Command Palette > "WaddleAI: Select Model"
    3. Open Copilot Chat and select WaddleAI as your model provider
    `;
    
    vscode.window.showInformationMessage(message, 'Get Started', 'Later').then(selection => {
        if (selection === 'Get Started') {
            vscode.commands.executeCommand('waddleai.setApiKey');
        }
    });
    
    context.globalState.update('waddleai.welcomeShown', true);
}

function getUsageWebviewContent(usage: any): string {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WaddleAI Usage</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
                padding: 20px;
            }
            .stat-card {
                background: var(--vscode-editor-inactiveSelectionBackground);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .stat-title {
                font-size: 14px;
                color: var(--vscode-descriptionForeground);
                margin-bottom: 5px;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: var(--vscode-editor-foreground);
            }
            .progress-bar {
                width: 100%;
                height: 20px;
                background: var(--vscode-input-background);
                border-radius: 10px;
                overflow: hidden;
                margin-top: 10px;
            }
            .progress-fill {
                height: 100%;
                background: var(--vscode-progressBar-background);
                transition: width 0.3s ease;
            }
            h1 {
                color: var(--vscode-editor-foreground);
                border-bottom: 1px solid var(--vscode-panel-border);
                padding-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>🚀 WaddleAI Token Usage</h1>
        
        <div class="stat-card">
            <div class="stat-title">Total WaddleAI Tokens Used</div>
            <div class="stat-value">${usage.total_tokens.toLocaleString()}</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-title">Total Requests</div>
            <div class="stat-value">${usage.total_requests.toLocaleString()}</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-title">Daily Quota</div>
            <div class="stat-value">${usage.used_today.toLocaleString()} / ${usage.daily_limit.toLocaleString()}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${(usage.used_today / usage.daily_limit * 100)}%"></div>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-title">Monthly Quota</div>
            <div class="stat-value">${usage.used_month.toLocaleString()} / ${usage.monthly_limit.toLocaleString()}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${(usage.used_month / usage.monthly_limit * 100)}%"></div>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-title">Period</div>
            <div class="stat-value">${usage.period_days} days</div>
        </div>
    </body>
    </html>
    `;
}

export function deactivate() {
    // Clean up resources
    if (waddleAIClient) {
        waddleAIClient.dispose();
    }
}