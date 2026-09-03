import { Component, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/** Catches render crashes (e.g. failed lazy chunks, malformed API data)
 * and shows a recoverable fallback instead of a blank screen. */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    console.error('UI crash caught by ErrorBoundary:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background p-8 text-center">
          <span className="material-symbols-outlined text-5xl text-error">error</span>
          <h1 className="font-headline-md text-headline-md text-on-surface">Something went wrong</h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Please refresh the page. If the problem persists, contact your administrator.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="px-4 py-1.5 rounded bg-primary text-on-primary font-label-md text-label-md"
          >
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
