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

if (!fs.existsSync(requirementsPath)) {
  console.warn('⚠️  requirements.txt not found at:', requirementsPath);
  console.warn('   Skipping Python dependency installation');
  process.exit(0);
}

try {
  // Check if pip is available
  try {
    execSync('pip3 --version', { stdio: 'ignore' });
  } catch (err) {
    console.warn('⚠️  pip3 not found, trying pip...');
    execSync('pip --version', { stdio: 'ignore' });
  }

  // Install Python dependencies
  console.log('   Installing from:', requirementsPath);

  try {
    execSync(`pip3 install -r "${requirementsPath}"`, {
      stdio: 'inherit',
      cwd: packageRoot
    });
  } catch (err) {
    // Try with pip if pip3 failed
    execSync(`pip install -r "${requirementsPath}"`, {
      stdio: 'inherit',
      cwd: packageRoot
    });
  }

  console.log('✅ Python dependencies installed successfully');
} catch (error) {
  console.error('❌ Failed to install Python dependencies');
  console.error('   You may need to install them manually:');
  console.error(`   pip install -r ${requirementsPath}`);
  console.error('');
  console.error('   Error:', error.message);

  // Don't fail the npm install, just warn
  process.exit(0);
}
