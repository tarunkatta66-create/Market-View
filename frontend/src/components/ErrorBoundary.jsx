import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm max-w-md w-full text-center">
            <h2 className="text-lg font-bold text-slate-800 mb-2">Display Error Encountered</h2>
            <p className="text-sm text-slate-500 mb-4">
              The application encountered a rendering issue while processing market feeds.
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.reload();
              }}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
            >
              Refresh Terminal
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
