#!/usr/bin/env node

/**
 * Post-install script for @lb-project/know
 * Installs Python dependencies required for the know tool
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('📦 Installing Python dependencies for @lb-project/know...');

// Find requirements.txt
const packageRoot = path.resolve(__dirname, '..');
const requirementsPath = path.join(packageRoot, 'know', 'requirements.txt');
const venvPath = path.join(packageRoot, 'know', 'venv');
const venvPython = path.join(venvPath, 'bin', 'python3');
const venvPip = path.join(venvPath, 'bin', 'pip');

if (!fs.existsSync(requirementsPath)) {
  console.warn('⚠️  requirements.txt not found at:', requirementsPath);
  console.warn('   Skipping Python dependency installation');
  process.exit(0);
}

try {
  // Create venv if it doesn't exist
  if (!fs.existsSync(venvPath)) {
    console.log('🔨 Creating Python virtual environment...');
    execSync('python3 -m venv know/venv', {
      stdio: 'inherit',
      cwd: packageRoot
    });
    console.log('✅ Virtual environment created at know/venv');
  } else {
    console.log('✓ Using existing virtual environment at know/venv');
  }

  // Install Python dependencies into venv
  console.log('   Installing from:', requirementsPath);

  execSync(`"${venvPip}" install -r "${requirementsPath}"`, {
    stdio: 'inherit',
    cwd: packageRoot
  });

  console.log('✅ Python dependencies installed successfully');
} catch (error) {
  console.error('❌ Failed to install Python dependencies');
  console.error('   You may need to install them manually:');
  console.error(`   python3 -m venv know/venv`);
  console.error(`   know/venv/bin/pip install -r ${requirementsPath}`);
  console.error('');
  console.error('   Error:', error.message);

  // Don't fail the npm install, just warn
  process.exit(0);
}
