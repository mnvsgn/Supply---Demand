import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import {
  Paperclip,
  Loader2,
  FileSpreadsheet,
  ArrowUp,
} from 'lucide-react';

export default function ChatInput() {
  const {
    activeDataset,
    handleFileUpload,
    handleSendPrompt,
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
    if (!text.trim() || isBusy) return;

    const query = text.trim();
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    handleSendPrompt(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
      e.target.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 pb-4">
      {/* Main Input Box */}
      <div className="rounded-2xl border border-[#262626] bg-[#181818] p-3 shadow-sm focus-within:border-[#383838] transition-colors">
        {/* Active Dataset Pill indicator if attached */}
        {activeDataset && (
          <div className="pb-2 mb-2 flex items-center justify-between text-xs border-b border-[#262626]">
            <div className="flex items-center space-x-2 text-neutral-400 min-w-0">
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
              <span className="text-neutral-200 font-medium truncate max-w-[200px]" title={activeDataset.filename}>
                {activeDataset.filename}
              </span>
              <span className="text-[11px] text-neutral-500 flex-shrink-0">
                ({activeDataset.row_count.toLocaleString()} rows)
              </span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c] flex-shrink-0">
              Active
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
            placeholder="Ask about your supply or demand data..."
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
              aria-label="Upload CSV or XLSX file"
              className="flex items-center space-x-2 text-xs text-neutral-400 hover:text-neutral-200 transition-colors disabled:opacity-40 cursor-pointer"
            >
              {isUploading ? (
                <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
              ) : (
                <Paperclip className="w-4 h-4 text-neutral-400" />
              )}
              <span>{isUploading ? 'Uploading...' : 'Upload CSV or XLSX'}</span>
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!text.trim() || isBusy}
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
        Forecasts are estimates based on your uploaded data.
      </div>
    </div>
  );
}
