/* eslint-disable @typescript-eslint/no-unused-vars */
// FloatingChatBubble.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import chatApi from '@/apis/chatApi';
import { Card } from '@/components/ui/card';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faComments, faPaperPlane, faSync, faTrash, faPlus, faEdit, faTimes } from '@fortawesome/free-solid-svg-icons';
import type { Conversation, Message, UploadedFile } from '@/types/chat.type';
import { convertToUIConversation, convertToUIMessage, convertToUIFile } from '@/types/chat.type';

export default function FloatingChatBubble() {
  const [isOpen, setIsOpen] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [promptDraft, setPromptDraft] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  // Load conversations on open
  useEffect(() => {
    if (isOpen) {
      loadConversations();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
      loadFiles(activeConversationId);
    } else {
      setMessages([]);
      setUploadedFiles([]);
    }
  }, [activeConversationId]);

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const res = await chatApi.getConversations();
      const apiConvs = res ? (Array.isArray(res.items) ? res.items : []) : [];
      const uiConvs = apiConvs.map(convertToUIConversation);
      setConversations(uiConvs);
      if (!activeConversationId && uiConvs.length) {
        setActiveConversationId(uiConvs[0].id);
      }
    } catch {
      setError('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      setIsLoading(true);
      const res = await chatApi.getConversationMessages(conversationId);
      const apiMsgs = res ? (Array.isArray(res.items) ? res.items : []) : [];
      setMessages(apiMsgs.map(convertToUIMessage));
    } catch {
      setError('Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  };

  const loadFiles = async (conversationId: string) => {
    try {
      const res = await chatApi.getFiles({ conversation_id: conversationId });
      const apiFiles = res ? (Array.isArray(res.items) ? res.items : []) : [];
      setUploadedFiles(apiFiles.map(convertToUIFile));
    } catch {
      setError('Failed to load files');
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !activeConversationId) return;
    try {
      setIsLoading(true);
      // Only include file_ids if there are uploaded files
      const fileIds = uploadedFiles.length > 0 ? uploadedFiles.map(f => f.id) : undefined;
      await chatApi.sendMessage({ conversation_id: activeConversationId, content: input, ...(fileIds ? { file_ids: fileIds } : {}) });
      setInput('');
      loadMessages(activeConversationId);
    } catch (err) {
      setError('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    try {
      setIsLoading(true);
      const res = await chatApi.createConversation({ name: 'New Chat' });
      loadConversations();
      if (res && res.id) setActiveConversationId(res.id);
    } catch {
      setError('Failed to create conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      setIsLoading(true);
      await chatApi.deleteConversation(id);
      loadConversations();
      if (activeConversationId === id) setActiveConversationId(null);
    } catch (err) {
      setError('Failed to delete conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshConversation = () => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
      loadFiles(activeConversationId);
    }
  };

  const handleFileUpload = async (files: FileList | File[]) => {
    if (!activeConversationId) return;
    try {
      setIsLoading(true);
      await chatApi.uploadFiles(Array.from(files), activeConversationId);
      loadFiles(activeConversationId);
    } catch (err) {
      setError('Failed to upload file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const handlePromptSave = async () => {
    if (!activeConversationId) return;
    try {
      setIsLoading(true);
      await chatApi.updateConversation(activeConversationId, { system_prompt: promptDraft });
      setSystemPrompt(promptDraft);
      setShowPromptEditor(false);
    } catch (err) {
      setError('Failed to update prompt');
    } finally {
      setIsLoading(false);
    }
  };

  // UI
  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          className="fixed bottom-6 right-6 z-50 bg-[color:var(--primary)] text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg hover:scale-105 transition-all"
          onClick={() => setIsOpen(true)}
          aria-label="Open Chat"
        >
          <FontAwesomeIcon icon={faComments} size="2x" />
        </button>
      )}

      {/* Floating Chat Panel */}
      {isOpen && (
        <div
          className="fixed bottom-6 right-6 z-[9999] w-full max-w-md md:w-96 bg-[color:var(--card)] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-[color:var(--border)]"
          style={{ maxHeight: '80vh' }}
          ref={chatWindowRef}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-[color:var(--border)] bg-[color:var(--card)]/80">
            <div className="flex items-center gap-2">
              <FontAwesomeIcon icon={faComments} className="text-[color:var(--primary)]" />
              <span className="font-semibold">Chat</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[color:var(--muted-foreground)] hover:text-red-500">
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>

            {/* Conversation Selector */}
            <div className="flex items-center gap-2 p-2 border-b border-[color:var(--border)] bg-[color:var(--muted)]/10">
              <select
                className="flex-1 rounded border p-1"
                value={activeConversationId || ''}
                onChange={e => setActiveConversationId(e.target.value)}
              >
                {conversations.map(conv => (
                  <option key={conv.id} value={conv.id}>{conv.name}</option>
                ))}
              </select>
              <button onClick={handleCreateConversation} className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded">
                <FontAwesomeIcon icon={faPlus} />
              </button>
              {activeConversationId && (
                <button onClick={() => handleDeleteConversation(activeConversationId)} className="p-1 text-red-500 hover:bg-red-100 rounded">
                  <FontAwesomeIcon icon={faTrash} />
                </button>
              )}
              <button onClick={handleRefreshConversation} className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded">
                <FontAwesomeIcon icon={faSync} />
              </button>
              <button onClick={() => { setPromptDraft(systemPrompt); setShowPromptEditor(true); }} className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded">
                <FontAwesomeIcon icon={faEdit} />
              </button>
            </div>

            {/* Prompt Editor */}
            {showPromptEditor && (
              <div className="p-4 border-b border-[color:var(--border)] bg-[color:var(--muted)]/10 flex flex-col gap-2">
                <textarea
                  className="w-full rounded border p-2"
                  rows={3}
                  value={promptDraft}
                  onChange={e => setPromptDraft(e.target.value)}
                  placeholder="Custom system prompt..."
                />
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setShowPromptEditor(false)} className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">Cancel</button>
                  <button onClick={handlePromptSave} className="px-3 py-1 rounded bg-[color:var(--primary)] text-white hover:bg-[color:var(--primary-dark)]">Save</button>
                </div>
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-[color:var(--card)]" style={{ minHeight: 200 }}>
              {messages.length === 0 ? (
                <div className="text-center text-[color:var(--muted-foreground)]">No messages yet.</div>
              ) : (
                messages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`rounded-xl px-3 py-2 max-w-[80%] ${msg.role === 'user' ? 'bg-[color:var(--primary)] text-white' : 'bg-gray-100 dark:bg-gray-800 text-[color:var(--foreground)]'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* File Uploads */}
            <div className="p-2 border-t border-[color:var(--border)] bg-[color:var(--muted)]/10">
              <div className="flex flex-wrap gap-2 items-center">
                {uploadedFiles.map(file => (
                  <div key={file.id} className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 text-xs">
                    <span>{file.originalName || file.name}</span>
                  </div>
                ))}
                <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  className="hidden"
                  onChange={e => {
                    if (e.target.files) handleFileUpload(e.target.files);
                  }}
                />
                <button onClick={() => fileInputRef.current?.click()} className="text-[color:var(--primary)] px-2 py-1 rounded hover:bg-[color:var(--accent)] text-xs">Upload</button>
                <span className="text-xs text-[color:var(--muted-foreground)]">or drag & drop files here</span>
              </div>
            </div>

          {/* Input */}
          <form
            className="flex items-center gap-2 p-2 border-t border-[color:var(--border)] bg-[color:var(--card)]"
            onSubmit={async e => {
              e.preventDefault();
              await handleSendMessage();
            }}
          >
            <input
              className="flex-1 rounded border p-2"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
              autoFocus
            />
            <button type="submit" className="p-2 rounded bg-[color:var(--primary)] text-white hover:bg-[color:var(--primary-dark)]" disabled={isLoading || !input.trim()}>
              <FontAwesomeIcon icon={faPaperPlane} />
            </button>
          </form>
          {error && <div className="text-xs text-red-500 text-center p-1">{error}</div>}
        </div>
      )}
    </>
  );
}
