import React from 'react';
import { useChat } from '../../context/ChatContext';
import { TrendingUp, Calendar } from 'lucide-react';

export default function WelcomeScreen() {
  const { handleSendPrompt, handleFileUpload } = useChat();

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="flex-1 flex flex-col items-center justify-center px-4 py-8 max-w-2xl mx-auto w-full space-y-6"
    >
      {/* Welcome Heading & Subtitle */}
      <div className="text-center space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-semibold text-white tracking-tight">
          What would you like to forecast?
        </h1>
        <p className="text-sm text-neutral-400">
          Upload your data and explore demand with machine learning.
        </p>
      </div>

      {/* Two Understated Suggestion Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
        {/* Card 1: Forecast demand */}
        <button
          onClick={() => handleSendPrompt('Forecast total demand for the next 14 days')}
          className="p-4 rounded-xl border border-[#262626] bg-[#181818] hover:bg-[#202020] hover:border-[#333333] transition-colors text-left group space-y-3 cursor-pointer"
        >
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="font-semibold text-sm text-white group-hover:text-emerald-300 transition-colors">
              Forecast demand
            </div>
            <div className="text-xs text-neutral-400 mt-1">
              Predict future sales
            </div>
          </div>
        </button>

        {/* Card 2: Analyze trends */}
        <button
          onClick={() => handleSendPrompt('Show sales trends, seasonality and safety stock')}
          className="p-4 rounded-xl border border-[#262626] bg-[#181818] hover:bg-[#202020] hover:border-[#333333] transition-colors text-left group space-y-3 cursor-pointer"
        >
          <Calendar className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="font-semibold text-sm text-white group-hover:text-emerald-300 transition-colors">
              Analyze trends
            </div>
            <div className="text-xs text-neutral-400 mt-1">
              Find seasonal patterns
            </div>
          </div>
        </button>
      </div>
    </div>
  );
}
