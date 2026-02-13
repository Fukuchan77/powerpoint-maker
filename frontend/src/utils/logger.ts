/**
 * Structured logging utility for frontend
 * Provides consistent JSON-formatted logging with context
 */

interface LogContext {
  [key: string]: unknown;
}

interface LogEntry {
  timestamp: string;
  level: string;
  service: string;
  message: string;
  [key: string]: unknown;
}

class Logger {
  private serviceName: string;

  constructor(serviceName: string) {
    this.serviceName = serviceName;
  }

  private log(level: string, message: string, context?: LogContext): void {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      service: this.serviceName,
      message,
      ...context,
    };

    // In development, use console methods for better readability
    // In production, always use JSON format
    const isDevelopment = import.meta.env.DEV;

    if (isDevelopment && level !== 'error') {
      console.log(`[${this.serviceName}] ${message}`, context || '');
    } else {
      const logMethod = level === 'error' ? console.error : console.log;
      logMethod(JSON.stringify(logEntry));
    }
  }

  info(message: string, context?: LogContext): void {
    this.log('info', message, context);
  }

  error(message: string, error?: Error, context?: LogContext): void {
    this.log('error', message, {
      ...context,
      error: error?.message,
      error_type: error?.name,
      stack: error?.stack,
    });
  }

  warn(message: string, context?: LogContext): void {
    this.log('warn', message, context);
  }

  debug(message: string, context?: LogContext): void {
    this.log('debug', message, context);
  }
}

/**
 * Create a logger instance for a specific service/component
 * @param serviceName - Name of the service or component
 * @returns Logger instance
 */
export const createLogger = (serviceName: string): Logger => new Logger(serviceName);
