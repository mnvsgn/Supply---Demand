import React from 'react';
import MessageList from './chat/MessageList';

/**
 * ChatWindow is the primary scrollable chat container displaying
 * message history, welcome cards, and backend status shimmers.
 */
export default function ChatWindow() {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      <MessageList />
    </div>
  );
}

export { MessageList };
