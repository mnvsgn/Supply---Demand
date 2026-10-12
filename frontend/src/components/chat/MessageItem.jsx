import React from 'react';
import {
  User,
  Bot,
  AlertOctagon,
  Sparkles,
  CheckCircle2,
  Copy,
  Check,
  FileSpreadsheet,
  RotateCw,
} from 'lucide-react';
import DatasetSummaryCard from '../upload/DatasetSummaryCard';
import ForecastResultCard from '../forecast/ForecastResultCard';
import ModelComparisonCard from '../forecast/ModelComparisonCard';
import QualityWarningCard from './QualityWarningCard';
import ClarificationCard from './ClarificationCard';
import BusinessInsightsCard from '../forecast/BusinessInsightsCard';
import ErrorBoundary from '../common/ErrorBoundary';
import { useChat } from '../../context/ChatContext';
import { formatTime } from '../../utils/formatters';

export default function MessageItem({ message }) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.sender === 'user';
  const {
    handleSelectClarificationOption,
    runAnalytics,
    handleRegenerate,
    isGenerating,
  } = useChat();

  const handleCopy = () => {
    if (message.content) {
      navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Helper to render markdown bold and linebreaks cleanly without huge dependencies
  const renderFormattedText = (content) => {
    if (!content) return null;

    return content.split('\n').map((line, idx) => {
      // Bold rendering **text**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={idx} className="block min-h-[1.25rem]">
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return (
                <strong key={pIdx} className="font-semibold text-slate-100">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            return part;
          })}
        </span>
      );
    });
  };

  if (isUser) {
    return (
      <div className="flex justify-end w-full py-1.5 animate-fade-in">
        <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[65%] flex flex-col items-end">
          <div className="bg-[#262626] text-neutral-100 border border-[#383838] rounded-2xl rounded-tr-sm px-4 py-2.5 sm:px-4 sm:py-3 shadow-sm text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.data?.filename && (
              <div className="mb-2 flex items-center space-x-2.5 px-2.5 py-1.5 rounded-lg bg-[#1a1f28] border border-[#2b394e] text-xs text-neutral-200">
                <div className="w-6 h-6 rounded bg-[#111722] border border-[#233145] flex items-center justify-center flex-shrink-0 text-blue-400">
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate max-w-[180px]">{message.data.filename}</div>
                  {message.data.size && (
                    <div className="text-[10px] text-neutral-400">
                      {(message.data.size / 1024).toFixed(1)} KB
                    </div>
                  )}
                </div>
              </div>
            )}
            <div>{message.content}</div>
          </div>
          <span className="text-[10px] text-neutral-500 mt-1 px-1">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start w-full py-2">
      <div className="w-full max-w-3xl flex items-start space-x-3 sm:space-x-3.5">
        {/* Assistant Avatar */}
        <div className="w-7 h-7 rounded-lg bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
          <Bot className="w-3.5 h-3.5" />
        </div>

        {/* Assistant Content Column */}
        <div className="flex-1 space-y-3 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between text-xs text-neutral-400">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-neutral-200">DemandIQ</span>
              <span className="text-[11px] text-neutral-500">{formatTime(message.timestamp)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => handleRegenerate && handleRegenerate(message.id)}
                disabled={isGenerating}
                title="Regenerate response"
                className="p-1 rounded text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer disabled:opacity-40"
                aria-label="Regenerate message"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin text-emerald-400' : ''}`} />
              </button>
              {message.content && (
                <button
                  onClick={handleCopy}
                  title="Copy text"
                  className="p-1 rounded text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer"
                  aria-label="Copy message"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>
          </div>

          {/* Narrative Text */}
          {message.content && (
            <div className="text-sm text-neutral-200 leading-relaxed space-y-1">
              {renderFormattedText(message.content)}
            </div>
          )}

          {/* Embedded Specialized Cards */}
          <ErrorBoundary>
            {message.type === 'dataset_upload' && message.data && (
              <div className="pt-2">
                <DatasetSummaryCard dataset={message.data} />
              </div>
            )}

            {message.type === 'forecast' && message.data && (
              <div className="pt-2">
                <ForecastResultCard forecastResult={message.data} />
              </div>
            )}

            {message.type === 'evaluation' && message.data && (
              <div className="pt-2">
                <ModelComparisonCard evaluation={message.data} />
              </div>
            )}

            {message.type === 'quality_warning' && message.data && (
              <div className="pt-2">
                <QualityWarningCard dataQuality={message.data} />
              </div>
            )}

            {message.type === 'clarification' && message.data && (
              <div className="pt-2">
                <ClarificationCard
                  clarification={message.data}
                  onSelectOption={handleSelectClarificationOption}
                />
              </div>
            )}

            {message.type === 'analytics' && message.data && (
              <div className="pt-2">
                <BusinessInsightsCard
                  analytics={message.data}
                  onRecalculateInventory={(params) => runAnalytics && runAnalytics(params)}
                />
              </div>
            )}
          </ErrorBoundary>

          {message.type === 'error' && (
            <div className="rounded-xl bg-[#1c1414] border border-[#3b1d1d] p-4 space-y-2.5 text-xs">
              <div className="flex items-center space-x-2 text-rose-400 font-medium">
                <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span className="font-semibold text-neutral-200">
                  {message.data?.code === 'BACKEND_DISCONNECTED' ||
                  message.data?.code === 'INTERNAL_SERVER_ERROR' ||
                  message.content?.includes('connect') ||
                  message.content?.includes('FastAPI')
                    ? 'Internal Server Error'
                    : 'System Notice'}
                </span>
              </div>
              <p className="text-neutral-300 text-xs leading-relaxed">
                {message.content?.includes('Cannot connect to backend server') ||
                message.content?.includes('FastAPI is running') ||
                message.data?.code === 'BACKEND_DISCONNECTED'
                  ? 'Internal Server Error: Unable to connect to the forecasting service. Please verify the service is running and try again in a few moments.'
                  : message.content}
              </p>
              <div className="pt-1">
                <button
                  onClick={() => handleRegenerate && handleRegenerate(message.id)}
                  disabled={isGenerating}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-neutral-300 hover:text-white bg-[#261e1e] hover:bg-[#332525] border border-[#4a2828] transition-colors cursor-pointer text-[11px] disabled:opacity-40"
                >
                  <RotateCw className={`w-3 h-3 ${isGenerating ? 'animate-spin text-rose-400' : 'text-neutral-400'}`} />
                  <span>Retry Request</span>
                </button>
              </div>
            </div>
          )}

          {/* Assistant Action Bar with Regenerate & Sync Icon */}
          {message.type !== 'error' && (
            <div className="flex items-center gap-2 pt-1 text-xs">
              <button
                onClick={() => handleRegenerate && handleRegenerate(message.id)}
                disabled={isGenerating}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-[#222222] border border-[#2b2b2b] transition-colors cursor-pointer text-[11px] disabled:opacity-40"
                title="Regenerate response"
              >
                <RotateCw className={`w-3 h-3 ${isGenerating ? 'animate-spin text-emerald-400' : 'text-neutral-400'}`} />
                <span>Regenerate</span>
              </button>
              {message.content && (
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-[#222222] border border-[#2b2b2b] transition-colors cursor-pointer text-[11px]"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
