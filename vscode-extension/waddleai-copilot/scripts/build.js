#!/usr/bin/env node

/**
 * Build script for WaddleAI VS Code extension
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectRoot = path.resolve(__dirname, '..');
const outDir = path.join(projectRoot, 'out');

console.log('🔨 Building WaddleAI VS Code Extension...');

// Clean output directory
if (fs.existsSync(outDir)) {
    fs.rmSync(outDir, { recursive: true, force: true });
    console.log('✓ Cleaned output directory');
}

try {
    // Install dependencies
    console.log('📦 Installing dependencies...');
    execSync('npm install', {
        cwd: projectRoot,
        stdio: 'inherit'
    });

    // Lint code
    console.log('🔍 Linting code...');
    execSync('npm run lint', {
        cwd: projectRoot,
        stdio: 'inherit'
    });

    // Compile TypeScript
    console.log('⚙️ Compiling TypeScript...');
    execSync('npm run compile', {
        cwd: projectRoot,
        stdio: 'inherit'
    });

    // Copy assets
    console.log('📋 Copying assets...');
    const mediaDir = path.join(projectRoot, 'media');
    const outMediaDir = path.join(outDir, 'media');

    if (fs.existsSync(mediaDir)) {
        fs.cpSync(mediaDir, outMediaDir, { recursive: true });
        console.log('✓ Copied media assets');
    }

    console.log('✅ Build completed successfully!');

} catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
}
