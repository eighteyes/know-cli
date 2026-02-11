#!/usr/bin/env node

/**
 * Node.js wrapper for know Python CLI
 * Enables npm distribution of the Python-based know tool
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Find the Python know script (resolve symlinks for npm link)
const packageRoot = path.resolve(path.dirname(fs.realpathSync(__filename)), '..');
const pythonKnow = path.join(packageRoot, 'know', 'know');

if (!fs.existsSync(pythonKnow)) {
  console.error('Error: Python know script not found at:', pythonKnow);
  console.error('Package may be incorrectly installed');
  process.exit(1);
}

// Pass all arguments to Python know
const args = process.argv.slice(2);
const child = spawn(pythonKnow, args, {
  stdio: 'inherit',
  cwd: process.cwd()
});

child.on('exit', (code) => {
  process.exit(code || 0);
});

child.on('error', (err) => {
  console.error('Failed to execute know:', err.message);
  process.exit(1);
});
