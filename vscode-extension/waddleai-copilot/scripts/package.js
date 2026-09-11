#!/usr/bin/env node

/**
 * Package script for WaddleAI VS Code extension
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectRoot = path.resolve(__dirname, '..');

console.log('📦 Packaging WaddleAI VS Code Extension...');

try {
    // Build the extension
    console.log('🔨 Building extension...');
    execSync('node scripts/build.js', {
        cwd: projectRoot,
        stdio: 'inherit'
    });

    // Install vsce if not present
    try {
        execSync('vsce --version', { stdio: 'ignore' });
    } catch (error) {
        console.log('📥 Installing vsce...');
        execSync('npm install -g @vscode/vsce', {
            cwd: projectRoot,
            stdio: 'inherit'
        });
    }

    // Package the extension
    console.log('📦 Creating VSIX package...');
    execSync('vsce package --no-dependencies', {
        cwd: projectRoot,
        stdio: 'inherit'
    });

    // Find the generated VSIX file
    const files = fs.readdirSync(projectRoot).filter(f => f.endsWith('.vsix'));
    if (files.length > 0) {
        const vsixFile = files[files.length - 1]; // Get the latest one
        console.log(`✅ Package created: ${vsixFile}`);
        console.log('\nTo install:');
        console.log(`  code --install-extension ${vsixFile}`);
        console.log('\nOr use VS Code UI:');
        console.log('  Extensions → ... → Install from VSIX...');
    } else {
        console.log('❌ VSIX package not found');
        process.exit(1);
    }

} catch (error) {
    console.error('❌ Package failed:', error.message);
    process.exit(1);
}
