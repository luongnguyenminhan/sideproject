'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPlus, faEdit, faTrash, faCheck, faTimes, faComments } from '@fortawesome/free-solid-svg-icons'

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

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeConversationId: string
  onSelectConversation: (id: string) => void
  onCreateConversation: () => void
  onUpdateConversationName: (id: string, name: string) => void
  onDeleteConversation: (id: string) => void
  translations: {
    conversations: string
    newConversation: string
    noConversationsYet: string
    createFirstChat: string
    messages: string
  }
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onUpdateConversationName,
  onDeleteConversation,
  translations
}: ConversationSidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')

  const startEditing = (conversation: Conversation) => {
    setEditingId(conversation.id)
    setEditingName(conversation.name)
  }

  const saveEdit = () => {
    if (editingId && editingName.trim()) {
      onUpdateConversationName(editingId, editingName.trim())
    }
    setEditingId(null)
    setEditingName('')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditingName('')
  }

  return (
    <div className="h-full flex flex-col bg-[color:var(--card)]/50 backdrop-blur-sm border-r border-[color:var(--border)]">
      {/* Header */}
      <div className="p-4 border-b border-[color:var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)] rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faComments} className="text-white text-sm" />
            </div>
            <h2 className="text-lg font-semibold text-[color:var(--foreground)]">{translations.conversations}</h2>
          </div>
          <Button
            onClick={onCreateConversation}
            size="sm"
            className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200"
          >
            <FontAwesomeIcon icon={faPlus} className="mr-2" />
            {translations.newConversation}
          </Button>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {conversations.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faComments} className="text-2xl" />
            </div>
            <p>{translations.noConversationsYet}</p>
            <p className="text-sm">{translations.createFirstChat}</p>
          </div>
        ) : (
          conversations.map((conversation) => (
            <Card
              key={conversation.id}
              className={`p-3 cursor-pointer transition-all duration-200 hover:shadow-md backdrop-blur-sm ${
                conversation.id === activeConversationId
                  ? 'bg-gradient-to-r from-[color:var(--primary)]/10 to-[color:var(--primary)]/5 border-[color:var(--primary)]/20'
                  : 'bg-[color:var(--card)] hover:bg-[color:var(--accent)]/50 border-[color:var(--border)]'
              }`}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="flex items-center justify-between">
                {editingId === conversation.id ? (
                  <div className="flex-1 flex items-center gap-2">
                    <input
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      className="flex-1 px-2 py-1 text-sm bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none"
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEdit()
                      }}
                      autoFocus
                    />
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation()
                        saveEdit()
                      }}
                      className="h-6 w-6 p-0"
                    >
                      <FontAwesomeIcon icon={faCheck} className="text-green-600 text-xs" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation()
                        cancelEdit()
                      }}
                      className="h-6 w-6 p-0"
                    >
                      <FontAwesomeIcon icon={faTimes} className="text-red-600 text-xs" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm text-[color:var(--foreground)] truncate">
                        {conversation.name}
                      </h3>
                      <p className="text-xs text-[color:var(--muted-foreground)]">
                        {conversation.messages.length} {translations.messages}
                      </p>
                      <p className="text-xs text-[color:var(--muted-foreground)]">
                        {conversation.lastActivity.toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex flex-col gap-1 ml-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          startEditing(conversation)
                        }}
                        className="h-6 w-6 p-0 hover:bg-[color:var(--accent)]"
                      >
                        <FontAwesomeIcon icon={faEdit} className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteConversation(conversation.id)
                        }}
                        className="h-6 w-6 p-0 hover:bg-[color:var(--destructive)]/10"
                      >
                        <FontAwesomeIcon icon={faTrash} className="text-xs text-[color:var(--destructive)]" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
