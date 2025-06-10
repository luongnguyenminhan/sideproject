'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import { processMessageText } from '@/utils/text-processing';

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  canSendMessage: boolean;
  placeholder: string;
}

export function MessageInput({
  onSendMessage,
  isLoading,
  canSendMessage,
  placeholder,
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !canSendMessage) return;

    // Process the input text before sending
    const processedInput = processMessageText(input);
    onSendMessage(processedInput);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && canSendMessage) {
        // Process the input text before sending
        const processedInput = processMessageText(input);
        onSendMessage(processedInput);
        setInput('');
      }
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  return (
    <div className="border-t border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={!canSendMessage ? "" : placeholder}
            disabled={!canSendMessage}
            rows={1}
            className="flex-1 px-4 py-3 bg-[color:var(--background)] border border-[color:var(--border)] rounded-xl text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[color:var(--muted)]/20 resize-none min-h-[48px] max-h-[150px] overflow-y-auto"
          />
          <Button
            type="submit"
            disabled={!input.trim() || !canSendMessage}
            className="px-6 py-3 bg-gradient-to-r text-white from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            ) : (
              <FontAwesomeIcon icon={faPaperPlane} />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
