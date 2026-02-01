import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createLogger } from "../logger";

describe("Logger", () => {
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Spy on console methods
    consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore console methods
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  describe("createLogger", () => {
    it("creates a logger with the specified service name", () => {
      const logger = createLogger("TestService");
      expect(logger).toBeDefined();
    });
  });

  describe("info", () => {
    it("logs info message in development mode with readable format", () => {
      const logger = createLogger("TestService");
      logger.info("test message");

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      // In development mode (DEV=true), logs are in readable format
      expect(logCall[0]).toBe("[TestService] test message");
    });

    it("logs info message with context in development mode", () => {
      const logger = createLogger("TestService");
      logger.info("test message", { key: "value" });

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      expect(logCall[0]).toBe("[TestService] test message");
      expect(logCall[1]).toEqual({ key: "value" });
    });

    it("logs info message without context", () => {
      const logger = createLogger("TestService");
      logger.info("test message");

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      expect(logCall[0]).toBe("[TestService] test message");
      expect(logCall[1]).toBe("");
    });
  });

  describe("error", () => {
    it("logs error message", () => {
      const logger = createLogger("TestService");
      logger.error("error message");

      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it("logs error with Error object", () => {
      const logger = createLogger("TestService");
      const error = new Error("test error");
      logger.error("error occurred", error);

      expect(consoleErrorSpy).toHaveBeenCalled();
      const logCall = consoleErrorSpy.mock.calls[0];
      const logEntry = JSON.parse(logCall[0] as string);

      expect(logEntry).toHaveProperty("message", "error occurred");
      expect(logEntry).toHaveProperty("error", "test error");
      expect(logEntry).toHaveProperty("error_type", "Error");
      expect(logEntry).toHaveProperty("stack");
    });

    it("logs error with context", () => {
      const logger = createLogger("TestService");
      const error = new Error("test error");
      logger.error("error occurred", error, { userId: "123" });

      expect(consoleErrorSpy).toHaveBeenCalled();
      const logCall = consoleErrorSpy.mock.calls[0];
      const logEntry = JSON.parse(logCall[0] as string);

      expect(logEntry).toHaveProperty("userId", "123");
      expect(logEntry).toHaveProperty("error", "test error");
    });

    it("logs error without Error object", () => {
      const logger = createLogger("TestService");
      logger.error("error message", undefined, { key: "value" });

      expect(consoleErrorSpy).toHaveBeenCalled();
      const logCall = consoleErrorSpy.mock.calls[0];
      const logEntry = JSON.parse(logCall[0] as string);

      expect(logEntry).toHaveProperty("message", "error message");
      expect(logEntry).toHaveProperty("key", "value");
      expect(logEntry.error).toBeUndefined();
    });
  });

  describe("warn", () => {
    it("logs warning message in development mode with readable format", () => {
      const logger = createLogger("TestService");
      logger.warn("warning message");

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      // In development mode, warn uses readable format
      expect(logCall[0]).toBe("[TestService] warning message");
    });

    it("logs warning with context in development mode", () => {
      const logger = createLogger("TestService");
      logger.warn("warning message", { reason: "test" });

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      expect(logCall[0]).toBe("[TestService] warning message");
      expect(logCall[1]).toEqual({ reason: "test" });
    });
  });

  describe("debug", () => {
    it("logs debug message in development mode with readable format", () => {
      const logger = createLogger("TestService");
      logger.debug("debug message");

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      // In development mode, debug uses readable format
      expect(logCall[0]).toBe("[TestService] debug message");
    });

    it("logs debug with context in development mode", () => {
      const logger = createLogger("TestService");
      logger.debug("debug message", { data: { nested: "value" } });

      expect(consoleLogSpy).toHaveBeenCalled();
      const logCall = consoleLogSpy.mock.calls[0];

      expect(logCall[0]).toBe("[TestService] debug message");
      expect(logCall[1]).toEqual({ data: { nested: "value" } });
    });
  });

  describe("format verification", () => {
    it("verifies development mode uses readable format for non-error logs", () => {
      const logger = createLogger("TestService");

      // Test different log levels
      logger.info("info test");
      logger.warn("warn test");
      logger.debug("debug test");

      expect(consoleLogSpy).toHaveBeenCalledTimes(3);

      // All non-error logs should use readable format in development
      expect(consoleLogSpy.mock.calls[0][0]).toBe("[TestService] info test");
      expect(consoleLogSpy.mock.calls[1][0]).toBe("[TestService] warn test");
      expect(consoleLogSpy.mock.calls[2][0]).toBe("[TestService] debug test");
    });

    it("verifies error logs always use JSON format", () => {
      const logger = createLogger("TestService");
      const error = new Error("test error");

      logger.error("error test", error);

      expect(consoleErrorSpy).toHaveBeenCalledTimes(1);

      // Errors should always use JSON format even in development
      const logCall = consoleErrorSpy.mock.calls[0];
      const logEntry = JSON.parse(logCall[0] as string);

      expect(logEntry).toHaveProperty("level", "error");
      expect(logEntry).toHaveProperty("message", "error test");
    });
  });
});
