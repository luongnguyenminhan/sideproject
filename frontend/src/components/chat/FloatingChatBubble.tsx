/* eslint-disable @typescript-eslint/no-unused-vars */
// FloatingChatBubble.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MessageCodeBlock } from './message-code-block';
import { TypingIndicator } from './typing-indicator';
import chatApi from '@/apis/chatApi';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import AnimatedRibbon from '@/components/animations/AnimatedRibbon';
import { faComments, faPaperPlane, faSync, faTrash, faPlus, faEdit, faTimes } from '@fortawesome/free-solid-svg-icons';
import type { Conversation, Message, UploadedFile } from '@/types/chat.type';
import { convertToUIConversation, convertToUIMessage, convertToUIFile } from '@/types/chat.type';

import { useTranslation } from '@/contexts/TranslationContext';
import { ScrambledText } from '@/components/animations/ScrambledText';
import { FadeIn } from '@/components/animations/FadeIn';
import { SlideIn } from '@/components/animations/SlideIn';
import { AnimatedButton } from '@/components/animations/AnimatedButton';
import { AnimatedList } from '@/components/animations/AnimatedList';
import { motion, AnimatePresence } from 'framer-motion';
import { processMessageText } from '@/utils/text-processing';

export default function FloatingChatBubble() {
  const { t } = useTranslation();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [promptDraft, setPromptDraft] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatWindowRef = useRef<HTMLDivElement>(null);
  // Auto-scroll to bottom when messages or loading state changes
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isLoading]);
  // Load conversations on mount
  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
      loadFiles(activeConversationId);
    } else {
      setMessages([]);
      setUploadedFiles([]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('chat.errorLoadConversations') || 'Failed to load conversations');
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
      setError(t('chat.errorLoadMessages') || 'Failed to load messages');
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
      setError(t('chat.errorLoadFiles') || 'Failed to load files');
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !activeConversationId) return;
    setPendingMessage(input);
    setInput('');
    try {
      setIsLoading(true);
      // Only include file_ids if there are uploaded files
      const fileIds = uploadedFiles.length > 0 ? uploadedFiles.map(f => f.id) : undefined;
      await chatApi.sendMessage({ conversation_id: activeConversationId, content: input, ...(fileIds ? { file_ids: fileIds } : {}) });
      setPendingMessage(null);
      loadMessages(activeConversationId);
    } catch (err) {
      setError(t('chat.errorSendMessage') || 'Failed to send message');
      setPendingMessage(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    try {
      setIsLoading(true);
      const res = await chatApi.createConversation({ name: t('chat.newConversation') || 'New Conversation' });
      loadConversations();
      if (res && res.id) setActiveConversationId(res.id);
    } catch {
      setError(t('chat.errorCreateConversation') || 'Failed to create conversation');
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
      setError(t('chat.errorDeleteConversation') || 'Failed to delete conversation');
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
      setError(t('chat.errorUploadFile') || 'Failed to upload file');
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
      setError(t('chat.errorUpdatePrompt') || 'Failed to update prompt');
    } finally {
      setIsLoading(false);
    }
  };

  // UI
  if (!isOpen) {
    // Render a floating button to reopen chat
    return (
      <div className="z-50">
        <SlideIn isVisible={!isOpen} direction="up">
          <AnimatedButton
            onClick={() => setIsOpen(true)}
            className="bg-[color:var(--primary)] text-white rounded-full shadow-lg p-4 flex items-center justify-center hover:bg-[color:var(--primary-dark)] transition-all duration-200"
            title={t('chat.tooltips.openChat') || 'Open chat'}
            style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.18)' }}
            animation="scale"
          >
            <FontAwesomeIcon icon={faComments} className="text-2xl" />
          </AnimatedButton>
        </SlideIn>
      </div>
    );
  }
  return (
    <div className="z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="floating-chat"
            initial={{ scale: 0, opacity: 1, originX: 1, originY: 1 }}
            animate={{ scale: 1, opacity: 1, originX: 1, originY: 1 }}
            exit={{ scale: 0, opacity: 1, originX: 1, originY: 1 }}
            transition={{
              type: 'spring',
              stiffness: 400,
              damping: 30,
              // Thêm delay cho hiệu ứng exit để thu nhỏ mượt hơn
              exit: { delay: 0.08, duration: 0.28 }
            }}
            style={{ originX: 1, originY: 1 }}
          >
            {/* SlideIn giữ lại để nút mở chat vẫn có hiệu ứng, nhưng khung chat chính dùng motion.div */}
            {/* ...bắt đầu khung chat... */}
            <div
              className="relative w-lg max-h-[80vh] flex flex-col max-w-[90vw] overflow-hidden bg-[color:var(--card)] border border-[color:var(--border)] rounded-2xl shadow-2xl transform transition-all duration-300 scale-100"
              ref={chatWindowRef}
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              style={{ minHeight: 0 }}
            >
              {/* Animated background ribbons */}
              <AnimatedRibbon count={2} thickness={40} speed={0.3} enableFade enableWaves className="z-0" />
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-[color:var(--border)] bg-[color:var(--card)]/80 z-10">
                <div className="flex items-center gap-2">
                  <FontAwesomeIcon icon={faComments} className="text-[color:var(--primary)]" />
                  <ScrambledText as="span" className="font-semibold text-[color:var(--foreground)]" speed={0.5} scramble="always">
                    {t('chat.chats')}
                  </ScrambledText>
                </div>
                <AnimatedButton
                  onClick={() => setIsOpen(false)}
                  className="p-1 text-[color:var(--muted-foreground)] hover:bg-[color:var(--accent)] rounded"
                  title={t('chat.tooltips.closeChat') || 'Close'}
                  style={{ marginLeft: 'auto' }}
                  animation="scale"
                >
                  <FontAwesomeIcon icon={faTimes} />
                </AnimatedButton>
              </div>

              {/* Conversation Selector */}
              <div className="flex items-center justify-around gap-2 p-2 border-b border-[color:var(--border)] bg-[color:var(--muted)]/10">
                <FadeIn as="div" className='w-[80%]' delay={0.1}>
                  <select
                    className="flex-1 rounded border border-[color:var(--border)] w-full p-1 text-[color:var(--foreground)]"
                    value={activeConversationId || ''}
                    onChange={e => setActiveConversationId(e.target.value)}
                    aria-label={t('chat.conversations')}
                  >
                    {conversations.map(conv => (
                      <option className="text-[color:var(--foreground)]" key={conv.id} value={conv.id}>{conv.name}</option>
                    ))}
                  </select>
                </FadeIn>
                <AnimatedButton
                  onClick={handleCreateConversation}
                  className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded"
                  title={t('chat.tooltips.addConversation') || t('chat.newConversation')}
                  animation="scale"
                >
                  <FontAwesomeIcon icon={faPlus} />
                </AnimatedButton>
                {activeConversationId && (
                  <AnimatedButton
                    onClick={() => handleDeleteConversation(activeConversationId)}
                    className="p-1 text-red-500 hover:bg-red-100 rounded"
                    title={t('chat.tooltips.deleteConversation')}
                    animation="shake"
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </AnimatedButton>
                )}
                <AnimatedButton
                  onClick={handleRefreshConversation}
                  className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded"
                  title={t('chat.tooltips.refreshConversation') || t('chat.refresh') || t('common.refresh') || 'Refresh'}
                  animation="rotate"
                >
                  <FontAwesomeIcon icon={faSync} />
                </AnimatedButton>
                <AnimatedButton
                  onClick={() => { setPromptDraft(systemPrompt); setShowPromptEditor(true); }}
                  className="p-1 text-[color:var(--primary)] hover:bg-[color:var(--accent)] rounded"
                  title={t('chat.tooltips.editSystemPrompt')}
                  animation="pulse"
                >
                  <FontAwesomeIcon icon={faEdit} />
                </AnimatedButton>
              </div>

              {/* Prompt Editor */}
              {showPromptEditor && (
                <div className="p-4 border-b border-[color:var(--border)] bg-[color:var(--muted)]/10 flex flex-col gap-2">
                  <textarea
                    className="w-full rounded border p-2 text-[color:var(--foreground)] bg-[color:var(--card)] border-[color:var(--border)]"
                    rows={3}
                    value={promptDraft}
                    onChange={e => setPromptDraft(e.target.value)}
                    placeholder={t('chat.systemPrompt.placeholder')}
                  />
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setShowPromptEditor(false)} className="px-3 py-1 rounded bg-[color:var(--muted)] text-[color:var(--foreground)] hover:bg-[color:var(--muted-hover)]">{t('common.cancel')}</button>
                    <button onClick={handlePromptSave} className="px-3 py-1 rounded bg-[color:var(--primary)] text-white hover:bg-[color:var(--primary-dark)]">{t('common.save')}</button>
                  </div>
                </div>
              )}

              {/* Messages */}
              <div
                className="flex-1 overflow-y-auto p-4 space-y-2 bg-[color:var(--card)]"
                style={{ minHeight: 200 }}
                ref={chatWindowRef}
              >
                {messages.length === 0 && !pendingMessage ? (
                  <FadeIn as="div" delay={0.2} className="text-center text-[color:var(--muted-foregroundcolor)]">{t('chat.noMessages')}</FadeIn>
                ) : (
                  <AnimatedList
                    items={messages}
                    getKey={msg => msg.id}
                    animation="slide-up"
                    delayStep={0.05}
                    renderItem={(msg, idx) => (
                      <SlideIn key={msg.id} direction={msg.role === 'user' ? 'right' : 'left'} delay={idx * 0.05} className="mb-4">
                        <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          {msg.role === 'user' ? (
                            <div className="rounded-xl px-3 py-2 max-w-[80%] bg-[color:var(--primary)] whitespace-pre-wrap break-words text-white">
                              {msg.content}
                            </div>
                          ) : (
                            <div className="rounded-xl px-3 py-2 w-full bg-[color:var(--muted)] whitespace-pre-wrap break-words shadow-md transition-colors duration-300 text-[color:var(--foreground)]">
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                  code: (props: any) => {
                                    const { inline, className, children, ...rest } = props;
                                    const match = /language-(\w+)/.exec(className || '');
                                    const codeContent = String(children).replace(/\n$/, '');
                                    const language = match ? match[1] : 'text';
                                    if (inline) {
                                      return (
                                        <code className="bg-[color:var(--muted)] text-[color:var(--foreground)] px-1.5 py-0.5 rounded text-sm font-mono border border-[color:var(--border)]/50 shadow-sm" {...rest}>
                                          {children}
                                        </code>
                                      );
                                    }
                                    return (
                                      <MessageCodeBlock code={codeContent} language={language} variant={match ? 'header' : 'floating'} />
                                    );
                                  },
                                }}
                              >
                                {processMessageText(msg.content)}
                              </ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </SlideIn>
                    )}
                  />
                )}
                {/* Typing indicator */}
                {isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'user' && (
                  <FadeIn as="div" delay={0.1} className="flex justify-start">
                    <div className="max-w-[80%]">
                      <TypingIndicator typingText={t('chat.typing')} />
                    </div>
                  </FadeIn>
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
                  <button onClick={() => fileInputRef.current?.click()} className="text-[color:var(--primary)] px-2 py-1 rounded hover:bg-[color:var(--accent)] text-xs" title={t('chat.tooltips.uploadFile')}>{t('common.upload')}</button>
                  <span className="text-xs text-[color:var(--muted-foreground)]">{t('chat.uploadFilesDescription') || t('chat.uploadDragDrop') || 'or drag & drop files here'}</span>
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
                  className="flex-1 rounded border border-[color:var(--border)] p-2 text-[color:var(--foreground)]"
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={t('chat.typeMessage')}
                  disabled={isLoading}
                  autoFocus
                />
                <AnimatedButton type="submit" className="p-2 rounded bg-[color:var(--primary)] text-white hover:bg-[color:var(--primary-dark)]" disabled={isLoading || !input.trim()} title={t('chat.tooltips.sendMessage')} animation="scale">
                  {isLoading ? (
                    <span className="flex items-center space-x-1">
                      <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </span>
                  ) : (
                    <FontAwesomeIcon icon={faPaperPlane} />
                  )}
                </AnimatedButton>
              </form>

              {error && <div className="text-xs text-red-500 text-center p-1">{error}</div>}
            </div>
            {/* ...kết thúc khung chat... */}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
