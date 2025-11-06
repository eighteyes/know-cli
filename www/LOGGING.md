# Logging System Documentation

## Overview
The server uses a custom logging system that preserves logs in dated folders for historical reference.

## Features

### Log Storage
- Logs are stored in `.ai/tf/logs/YYYY-MM-DD/` directories
- Each server session creates a unique log file: `session-{timestamp}.log`
- Logs are never deleted on shutdown, only archived

### Log Format
- Timestamps use HH:MM:SS format (no dates in log lines)
- Log levels: INFO, ERROR, WARN, DEBUG
- Request/response logging with duration tracking

### Log Structure
```
HH:MM:SS [LEVEL] Message
```

Example:
```
11:04:13 [INFO] Server running on http://localhost:8880
11:04:35 [INFO] GET /api/graphs
11:04:35 [INFO] GET /api/graphs - 200 (3ms)
```

## API Endpoints

### View Recent Logs
```
GET /api/logs?lines=100
```
Returns the most recent log entries from the current session.

## Log Locations
- Current logs: `.ai/tf/logs/{today's date}/session-{timestamp}.log`
- Historical logs: Preserved in date-based folders
- Never deleted automatically, only on manual cleanup

## Logger Methods
- `logger.log(message)` - Info level logging
- `logger.error(message)` - Error level logging
- `logger.warn(message)` - Warning level logging
- `logger.debug(message)` - Debug level logging

## Graceful Shutdown
On SIGINT or SIGTERM:
1. Server closes connections
2. Logs are flushed to disk
3. Archive process ensures all logs are saved
4. Process exits cleanly

## Benefits
- Historical debugging capability
- No data loss on crashes
- Organized by date for easy navigation
- Lightweight with minimal overhead
- Request tracking for performance analysis