import React, { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import MessageItem from './MessageItem';
import WelcomeScreen from './WelcomeScreen';
import ClaudeThinkingIndicator from './ClaudeThinkingIndicator';

export default function MessageList() {
  const {
    messages,
    isUploading,
    isForecasting,
    isEvaluating,
    isAnalyzing,
    isResponding,
  } = useChat();
  const bottomRef = useRef(null);

  const isBusy = isUploading || isForecasting || isEvaluating || isAnalyzing || isResponding;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isBusy]);

  if (messages.length === 0) {
    return <WelcomeScreen />;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
      {/* Centered Conversation Container */}
      <div className="max-w-3xl mx-auto w-full space-y-4">
        {messages.map((msg) => (
          <MessageItem key={msg.id} message={msg} />
        ))}

        {/* Claude-style Generating / Cooking / Thinking indicator */}
        {isBusy && (
          <ClaudeThinkingIndicator
            isUploading={isUploading}
            isForecasting={isForecasting}
            isEvaluating={isEvaluating}
            isAnalyzing={isAnalyzing}
          />
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
