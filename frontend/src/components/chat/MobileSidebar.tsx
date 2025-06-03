'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ConversationSidebar } from './ConversationSidebar'
import { FileSidebar } from './FileSidebar'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faComments, faFile } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  name: string
  messages: Message[]
  lastActivity: Date
}

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadDate: Date
}

interface MobileSidebarProps {
  isOpen: boolean
  onClose: () => void
  conversations: Conversation[]
  activeConversationId: string
  onSelectConversation: (id: string) => void
  onCreateConversation: () => void
  onUpdateConversationName: (id: string, name: string) => void
  onDeleteConversation: (id: string) => void
  uploadedFiles: UploadedFile[]
  onDeleteFile: (id: string) => void
  onUploadFiles?: (files: File[]) => void
}

export function MobileSidebar({
  isOpen,
  onClose,
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onUpdateConversationName,
  onDeleteConversation,
  uploadedFiles,
  onDeleteFile,
  onUploadFiles
}: MobileSidebarProps) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'conversations' | 'files'>('conversations')

  if (!isOpen) return null

  const handleSelectConversation = (id: string) => {
    onSelectConversation(id)
    onClose()
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full w-80 bg-[color:var(--card)] border-r border-[color:var(--border)] z-50 md:hidden backdrop-blur-md shadow-xl">
        {/* Tab Navigation */}
        <div className="border-b border-[color:var(--border)] p-4 bg-[color:var(--card)]/80 backdrop-blur-sm">
          <div className="flex gap-2">
            <Button
              variant={activeTab === 'conversations' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('conversations')}
              className={`flex-1 transition-all duration-200 ${
                activeTab === 'conversations'
                  ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)]'
                  : 'border-[color:var(--border)] hover:bg-[color:var(--accent)]'
              }`}
            >
              <FontAwesomeIcon icon={faComments} className="mr-2" />
              {t('chat.chats')}
            </Button>
            <Button
              variant={activeTab === 'files' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('files')}
              className={`flex-1 transition-all duration-200 ${
                activeTab === 'files'
                  ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)]'
                  : 'border-[color:var(--border)] hover:bg-[color:var(--accent)]'
              }`}
            >
              <FontAwesomeIcon icon={faFile} className="mr-2" />
              {t('chat.files')}
            </Button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="h-[calc(100%-80px)]">
          {activeTab === 'conversations' ? (
            <ConversationSidebar
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onCreateConversation={onCreateConversation}
              onUpdateConversationName={onUpdateConversationName}
              onDeleteConversation={onDeleteConversation}
            />
          ) : (
            <FileSidebar
              uploadedFiles={uploadedFiles}
              onDeleteFile={onDeleteFile}
              onUploadFiles={onUploadFiles}
            />
          )}
        </div>
      </div>
    </>
  )
}
