const fs = require('fs').promises;
const path = require('path');

class Logger {
    constructor() {
        this.logStream = null;
        this.logBuffer = [];
        this.logDir = null;
        this.logFile = null;
        this.initialize();
    }

    async initialize() {
        // Create log directory structure
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        this.logDir = path.join(__dirname, '../../.ai/tf/logs', today);

        try {
            await fs.mkdir(this.logDir, { recursive: true });

            // Create unique log file for this session
            const sessionId = Date.now();
            this.logFile = path.join(this.logDir, `session-${sessionId}.log`);

            // Write buffered logs if any
            if (this.logBuffer.length > 0) {
                const initialLogs = this.logBuffer.join('\n') + '\n';
                await fs.writeFile(this.logFile, initialLogs);
                this.logBuffer = [];
            }
        } catch (error) {
            console.error('Failed to initialize logger:', error);
        }
    }

    getTimestamp() {
        const now = new Date();
        return now.toTimeString().split(' ')[0]; // HH:MM:SS
    }

    async write(level, message, ...args) {
        const timestamp = this.getTimestamp();
        const formattedMessage = args.length > 0
            ? `${timestamp} [${level}] ${message} ${args.map(a => typeof a === 'object' ? JSON.stringify(a) : a).join(' ')}`
            : `${timestamp} [${level}] ${message}`;

        // Always log to console
        const consoleMethod = level === 'ERROR' ? 'error' : level === 'WARN' ? 'warn' : 'log';
        console[consoleMethod](formattedMessage);

        // Write to file
        if (this.logFile) {
            try {
                await fs.appendFile(this.logFile, formattedMessage + '\n');
            } catch (error) {
                // If we can't write, buffer it
                this.logBuffer.push(formattedMessage);
            }
        } else {
            // Buffer until we have a file
            this.logBuffer.push(formattedMessage);
        }
    }

    log(message, ...args) {
        return this.write('INFO', message, ...args);
    }

    error(message, ...args) {
        return this.write('ERROR', message, ...args);
    }

    warn(message, ...args) {
        return this.write('WARN', message, ...args);
    }

    debug(message, ...args) {
        return this.write('DEBUG', message, ...args);
    }

    async archiveLogs() {
        // This is called on shutdown - logs are already in dated folders
        // Just ensure everything is flushed
        if (this.logBuffer.length > 0 && this.logFile) {
            try {
                const bufferedLogs = this.logBuffer.join('\n') + '\n';
                await fs.appendFile(this.logFile, bufferedLogs);
                this.logBuffer = [];
                this.log('Logs archived successfully');
            } catch (error) {
                console.error('Failed to archive remaining logs:', error);
            }
        }
    }

    // Get recent logs for debugging
    async getRecentLogs(lines = 100) {
        if (!this.logFile) return [];

        try {
            const content = await fs.readFile(this.logFile, 'utf-8');
            const allLines = content.split('\n').filter(l => l);
            return allLines.slice(-lines);
        } catch (error) {
            return [];
        }
    }
}

// Create singleton instance
const logger = new Logger();

module.exports = logger;