import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled component error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="rounded-xl border border-rose-900/40 bg-[#1a1212] p-4 text-xs text-neutral-300 space-y-2">
          <div className="flex items-center space-x-2 text-rose-400 font-semibold">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Display Notice</span>
          </div>
          <p className="text-neutral-400">
            A temporary display issue occurred while rendering this card.
          </p>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#2a1a1a] hover:bg-[#382020] text-rose-300 border border-rose-800/40 text-[11px] transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Retry Display</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
