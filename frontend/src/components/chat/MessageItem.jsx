import React from 'react';
import {
  User,
  Bot,
  AlertOctagon,
  Sparkles,
  CheckCircle2,
  Copy,
  Check,
} from 'lucide-react';
import DatasetSummaryCard from '../upload/DatasetSummaryCard';
import ForecastResultCard from '../forecast/ForecastResultCard';
import ModelComparisonCard from '../forecast/ModelComparisonCard';
import QualityWarningCard from './QualityWarningCard';
import ClarificationCard from './ClarificationCard';
import BusinessInsightsCard from '../forecast/BusinessInsightsCard';
import { useChat } from '../../context/ChatContext';
import { formatTime } from '../../utils/formatters';

export default function MessageItem({ message }) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.sender === 'user';
  const { handleSelectClarificationOption, runAnalytics } = useChat();

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
      <div className="flex justify-end w-full py-1.5">
        <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[65%] flex flex-col items-end">
          <div className="bg-[#262626] text-neutral-100 border border-[#383838] rounded-2xl rounded-tr-sm px-4 py-2.5 sm:px-4 sm:py-3 shadow-sm text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
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

          {/* Narrative Text */}
          {message.content && (
            <div className="text-sm text-neutral-200 leading-relaxed space-y-1">
              {renderFormattedText(message.content)}
            </div>
          )}

          {/* Embedded Specialized Cards */}
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

          {message.type === 'error' && (
            <div className="rounded-xl bg-rose-950/20 border border-rose-800/40 p-4 space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-rose-400 font-semibold">
                <AlertOctagon className="w-4 h-4" />
                <span>Error {message.data?.code ? `[${message.data.code}]` : ''}</span>
              </div>
              {message.data?.detail && (
                <pre className="p-2 rounded bg-slate-950 text-slate-400 font-mono text-[11px] overflow-x-auto">
                  {typeof message.data.detail === 'object'
                    ? JSON.stringify(message.data.detail, null, 2)
                    : String(message.data.detail)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
