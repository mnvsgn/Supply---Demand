import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import {
  Plus,
  Paperclip,
  Loader2,
  FileSpreadsheet,
  ArrowUp,
  X,
  Sparkles,
} from 'lucide-react';

export default function ChatInput() {
  const {
    activeDataset,
    stagedFile,
    handleStageFile,
    handleClearStagedFile,
    handleSendPromptWithFile,
    isUploading,
    isForecasting,
    isEvaluating,
    isAnalyzing,
    isResponding,
  } = useChat();

  const [text, setText] = useState('');
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const isBusy = isUploading || isForecasting || isEvaluating || isAnalyzing || isResponding;

  // Auto-expand textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if ((!text.trim() && !stagedFile) || isBusy) return;

    const query = text.trim();
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    handleSendPromptWithFile(query, stagedFile);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleStageFile(e.target.files[0]);
      e.target.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 pb-4">
      {/* Main Input Box */}
      <div className="rounded-2xl border border-[#262626] bg-[#181818] p-3 shadow-sm focus-within:border-[#383838] transition-colors">
        
        {/* Staged File Thumbnail Chip (Matching the screenshot attachment card) */}
        {stagedFile && (
          <div className="mb-2.5 inline-flex items-center space-x-3 p-2 pr-2.5 rounded-xl bg-[#141a24] border border-[#223048] shadow-sm relative group animate-fade-in">
            {/* Dark chart / data visualization thumbnail icon matching screenshot */}
            <div className="w-12 h-12 rounded-lg bg-[#0e141e] border border-[#1d2b40] flex flex-col items-center justify-center flex-shrink-0 relative overflow-hidden">
              {/* Mini SVG sparkline with dashed forecast line */}
              <svg className="w-9 h-7" viewBox="0 0 36 24" fill="none">
                <line x1="2" y1="20" x2="34" y2="20" stroke="#1e293b" strokeWidth="1" />
                <line x1="2" y1="12" x2="34" y2="12" stroke="#1e293b" strokeWidth="1" />
                {/* Historical line */}
                <path d="M 4 18 L 11 15 L 18 10 L 22 13" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
                {/* Forecast dashed line */}
                <path d="M 22 13 L 28 8 L 33 6" stroke="#60a5fa" strokeWidth="2" strokeDasharray="2 2" strokeLinecap="round" />
                {/* Dots */}
                <circle cx="22" cy="13" r="1.5" fill="#3b82f6" />
                <circle cx="28" cy="8" r="1.5" fill="#60a5fa" />
                <circle cx="33" cy="6" r="1.5" fill="#60a5fa" />
              </svg>
            </div>

            {/* File info */}
            <div className="flex-1 min-w-0 pr-1">
              <div className="text-xs font-semibold text-neutral-100 truncate max-w-[200px]" title={stagedFile.name}>
                {stagedFile.name}
              </div>
              <div className="text-[11px] text-neutral-400 mt-0.5 flex items-center space-x-1.5">
                <span>{(stagedFile.size / 1024).toFixed(1)} KB</span>
              </div>
            </div>

            {/* Remove button */}
            <button
              type="button"
              onClick={handleClearStagedFile}
              className="p-1 rounded-md text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors cursor-pointer"
              title="Remove attached file"
              aria-label="Remove attached file"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* If an active dataset is already loaded in the session and no new file is staged */}
        {!stagedFile && activeDataset && (
          <div className="pb-2 mb-2 flex items-center justify-between text-xs border-b border-[#262626]">
            <div className="flex items-center space-x-2 text-neutral-400 min-w-0">
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
              <span className="text-neutral-200 font-medium truncate max-w-[200px]" title={activeDataset.filename}>
                {activeDataset.filename}
              </span>
              <span className="text-[11px] text-neutral-500 flex-shrink-0">
                ({activeDataset.row_count.toLocaleString()} records active)
              </span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c] flex-shrink-0">
              Session Active
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-2">
          {/* Text Area */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              stagedFile
                ? "What would you like to forecast with this dataset? (e.g. 'Forecast demand for 14 days')"
                : "Ask DemandIQ to forecast, analyze sales trends, or evaluate demand..."
            }
            rows={1}
            disabled={isBusy}
            className="w-full bg-transparent border-0 text-neutral-100 placeholder-neutral-500 text-sm focus:outline-none focus:ring-0 resize-none py-1 px-1 max-h-40 leading-relaxed block"
          />

          {/* Bottom Toolbar: Upload Action & Send Button */}
          <div className="flex items-center justify-between pt-1">
            {/* File Upload Trigger */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              className="hidden"
              aria-label="Upload CSV or XLSX dataset"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isBusy}
              aria-label="Attach CSV or XLSX file"
              className="flex items-center space-x-1.5 text-xs text-neutral-400 hover:text-neutral-200 transition-colors disabled:opacity-40 cursor-pointer p-1 rounded-lg hover:bg-[#222222]"
            >
              {isUploading ? (
                <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
              ) : (
                <Plus className="w-4 h-4 text-neutral-300 stroke-[2.5]" />
              )}
              <span className="text-[11px] font-medium text-neutral-300">
                {stagedFile ? 'Change spreadsheet' : 'Attach data'}
              </span>
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={(!text.trim() && !stagedFile) || isBusy}
              aria-label="Send message"
              className="w-8 h-8 rounded-lg bg-white hover:bg-neutral-200 disabled:bg-[#262626] text-black disabled:text-neutral-600 transition-colors flex items-center justify-center flex-shrink-0 shadow-sm cursor-pointer disabled:cursor-not-allowed"
            >
              {isBusy ? (
                <Loader2 className="w-4 h-4 animate-spin text-neutral-400" />
              ) : (
                <ArrowUp className="w-4 h-4 text-black stroke-[2.5]" />
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Footer Disclaimer */}
      <div className="text-center text-xs text-neutral-500 pt-2.5">
        Demand projections and safety stock sizing are grounded in historical observations.
      </div>
    </div>
  );
}
