import type { ErrorInfo, ReactNode } from "react";
import { Component } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component to catch and handle React errors
 *
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error("ErrorBoundary caught an error:", error, errorInfo);
    }

    // You can also log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div
          style={{
            padding: "2rem",
            maxWidth: "600px",
            margin: "2rem auto",
            border: "1px solid #f5c6cb",
            borderRadius: "8px",
            backgroundColor: "#f8d7da",
            color: "#721c24",
          }}
        >
          <h2 style={{ marginTop: 0 }}>⚠️ Something went wrong</h2>
          <p>
            An unexpected error occurred in the application. Please try
            refreshing the page.
          </p>

          {import.meta.env.DEV && this.state.error && (
            <details style={{ marginTop: "1rem", whiteSpace: "pre-wrap" }}>
              <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
                Error Details (Development Only)
              </summary>
              <div
                style={{
                  marginTop: "1rem",
                  padding: "1rem",
                  backgroundColor: "#fff",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  fontSize: "0.9em",
                  fontFamily: "monospace",
                }}
              >
                <strong>Error:</strong> {this.state.error.toString()}
                {this.state.errorInfo && (
                  <>
                    <br />
                    <br />
                    <strong>Component Stack:</strong>
                    <pre>{this.state.errorInfo.componentStack}</pre>
                  </>
                )}
              </div>
            </details>
          )}

          <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem" }}>
            <button
              onClick={this.handleReset}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#721c24",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#fff",
                color: "#721c24",
                border: "1px solid #721c24",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
