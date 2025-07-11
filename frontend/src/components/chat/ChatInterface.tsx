'use client';

// This file has been refactored into smaller components
// Please use the new ChatInterface component: chat-interface.tsx
// Individual components are now in:
// - chat-header.tsx
// - chat-welcome.tsx  
// - chat-message.tsx
// - message-code-block.tsx
// - message-input.tsx
// - typing-indicator.tsx
// - empty-chat-state.tsx
// - messages-container.tsx

import ChatClientWrapper from './ChatClientWrapper'

export default function ChatInterface() {
  return (
    <div className="h-full">
      <ChatClientWrapper useWebSocketV2={true} />
    </div>
  )
}
