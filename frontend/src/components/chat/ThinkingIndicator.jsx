import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, Flame, Cpu } from 'lucide-react';

const PHRASES = {
  forecast: [
    'Thinking...',
    'Inspecting historical sales patterns...',
    'Cooking demand projections...',
    'Calibrating seasonal patterns & trends...',
    'Calculating 95% planning intervals...',
    'Generating demand forecast...',
  ],
  evaluate: [
    'Thinking...',
    'Evaluating historical accuracy...',
    'Benchmarking prediction methods...',
    'Cooking reliability ratings...',
    'Generating comparison report...',
  ],
  analytics: [
    'Thinking...',
    'Analyzing sales velocity...',
    'Cooking seasonality & product rankings...',
    'Calculating safety stock requirements...',
    'Generating business analytics...',
  ],
  upload: [
    'Reading dataset stream...',
    'Validating file signature & headers...',
    'Detecting date and demand columns...',
    'Cooking dataset summary...',
  ],
  default: [
    'Thinking...',
    'Cooking...',
    'Analyzing demand intent...',
    'Synthesizing insights...',
    'Generating response...',
  ],
};

export default function ThinkingIndicator({
  isUploading,
  isForecasting,
  isEvaluating,
  isAnalyzing,
}) {
  const getPhraseList = () => {
    if (isUploading) return PHRASES.upload;
    if (isForecasting) return PHRASES.forecast;
    if (isEvaluating) return PHRASES.evaluate;
    if (isAnalyzing) return PHRASES.analytics;
    return PHRASES.default;
  };

  const phraseList = getPhraseList();
  const [phraseIndex, setPhraseIndex] = useState(0);

  useEffect(() => {
    setPhraseIndex(0);
    const interval = setInterval(() => {
      setPhraseIndex((prev) => (prev + 1) % phraseList.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [isUploading, isForecasting, isEvaluating, isAnalyzing, phraseList.length]);

  const currentPhrase = phraseList[phraseIndex] || 'Thinking...';
  const isCooking = currentPhrase.toLowerCase().includes('cook');

  return (
    <div className="flex justify-start w-full py-2 animate-fade-in">
      <div className="w-full max-w-3xl flex items-start space-x-3 sm:space-x-3.5">
        {/* Assistant Avatar with gentle pulse */}
        <div className="w-7 h-7 rounded-lg bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm relative">
          <Bot className="w-3.5 h-3.5" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-75" />
        </div>

        {/* Claude-style Thinking / Cooking Status Container */}
        <div className="flex-1 space-y-2.5 min-w-0">
          <div className="flex items-center space-x-2 text-xs">
            <span className="font-semibold text-neutral-200">DemandIQ</span>
            <span className="text-[11px] text-neutral-500">model processing</span>
          </div>

          {/* Cooking / Generating Status Pill */}
          <div className="inline-flex items-center space-x-2.5 px-3 py-1.5 rounded-xl border border-[#262626] bg-[#171717] text-xs shadow-sm">
            {isCooking ? (
              <Flame className="w-3.5 h-3.5 text-amber-400 animate-bounce" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            )}

            <span className="font-medium text-neutral-200 tracking-wide transition-all duration-300">
              {currentPhrase}
            </span>

            {/* Bouncing Dots */}
            <span className="inline-flex space-x-1 pl-1">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" />
            </span>
          </div>

          {/* Shimmer Placeholder Skeleton */}
          <div className="max-w-md p-3 rounded-xl border border-[#222222]/80 bg-[#151515]/60 space-y-2">
            <div className="h-2.5 bg-[#262626] rounded-full w-full animate-pulse" />
            <div className="h-2.5 bg-[#222222] rounded-full w-4/5 animate-pulse [animation-delay:200ms]" />
            <div className="h-2.5 bg-[#1e1e1e] rounded-full w-2/3 animate-pulse [animation-delay:400ms]" />
          </div>
        </div>
      </div>
    </div>
  );
}
