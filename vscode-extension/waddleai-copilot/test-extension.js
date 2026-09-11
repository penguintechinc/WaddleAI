#!/usr/bin/env node

/**
 * Simple test script to verify extension functionality
 */

const path = require('path');
const fs = require('fs');

console.log('🚀 Testing WaddleAI VS Code Extension...\n');

// Test 1: Check if all required files exist
const requiredFiles = [
    'out/extension.js',
    'out/chatParticipant.js',
    'out/waddleaiClient.js',
    'out/authProvider.js',
    'package.json'
];

console.log('📁 Checking required files...');
let allFilesExist = true;
requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`✅ ${file} exists`);
    } else {
        console.log(`❌ ${file} missing`);
        allFilesExist = false;
    }
});

if (!allFilesExist) {
    console.log('\n❌ Missing required files. Please run "npm run compile" first.');
    process.exit(1);
}

// Test 2: Check package.json structure
console.log('\n📦 Checking package.json...');
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

const requiredProperties = ['name', 'main', 'engines', 'activationEvents', 'contributes'];
requiredProperties.forEach(prop => {
    if (packageJson[prop]) {
        console.log(`✅ package.json has ${prop}`);
    } else {
        console.log(`❌ package.json missing ${prop}`);
    }
});

// Test 3: Try to load the extension module
console.log('\n🔧 Testing extension module...');
try {
    const extensionPath = path.resolve('out/extension.js');
    const extension = require(extensionPath);

    if (typeof extension.activate === 'function') {
        console.log('✅ Extension has activate function');
    } else {
        console.log('❌ Extension missing activate function');
    }

    if (typeof extension.deactivate === 'function') {
        console.log('✅ Extension has deactivate function');
    } else {
        console.log('❌ Extension missing deactivate function');
    }

} catch (error) {
    console.log(`❌ Failed to load extension: ${error.message}`);
}

// Test 4: Check WaddleAI Client
console.log('\n🌐 Testing WaddleAI Client...');
try {
    const WaddleAIClient = require('./out/waddleaiClient').WaddleAIClient;
    console.log('✅ WaddleAIClient can be imported');

    // Mock context for testing
    const mockContext = {
        secrets: {
            get: async () => null,
            store: async () => {}
        },
        extension: {
            packageJSON: { version: '0.1.0' }
        }
    };

    const client = new WaddleAIClient(mockContext);
    console.log('✅ WaddleAIClient can be instantiated');

} catch (error) {
    console.log(`❌ WaddleAI Client error: ${error.message}`);
}

console.log('\n🎉 Extension basic tests completed!');
console.log('\n📋 Next steps:');
console.log('1. Open this folder in VS Code');
console.log('2. Press F5 to launch Extension Development Host');
console.log('3. In the new VS Code window, open Chat panel');
console.log('4. Type "@waddleai" to interact with the participant');
console.log('5. Configure API key using Command Palette: "WaddleAI: Set API Key"');
