'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useTranslation } from '@/contexts/TranslationContext'
import { faCheck, faCog, faComments, faEdit, faFileText, faPlus, faRobot, faSpinner, faTimes, faTrash } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { useState } from 'react'

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
  messageCount?: number
  systemPrompt?: string
}

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeConversationId: string
  onSelectConversation: (id: string) => void
  onCreateConversation: () => void
  onUpdateConversationName: (id: string, name: string) => void
  onDeleteConversation: (id: string) => void
  onOpenSystemPromptEditor?: (conversationId: string) => void
  currentAgent?: {
    model_name: string
    provider: string
    temperature: number
    max_tokens: number
    system_prompt?: string
  } | null
  agentStatus?: 'loading' | 'error' | 'success' | 'none'
  onOpenAgentManagement?: () => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onUpdateConversationName,
  onDeleteConversation,
  onOpenSystemPromptEditor,
  currentAgent,
  agentStatus,
  onOpenAgentManagement,
  // isCollapsed = false,
  // onToggleCollapse
}: ConversationSidebarProps) {
  const { t } = useTranslation()
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
    <div className="h-full flex flex-col bg-[color:var(--card)]/50 backdrop-blur-sm relative transition-all duration-300 ease-in-out">
      {/* Header */}
      <div className="p-4 border-b border-[color:var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <Button
            onClick={onCreateConversation}
            size="sm"
            className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 flex-1 mr-2 group"
          >
            <FontAwesomeIcon icon={faPlus} className="mr-2 text-white group-hover:scale-110 transition-transform duration-200" />
            <span className="text-white">{t('chat.newConversation')}</span>
          </Button>
        </div>

        {/* Agent Status Section */}
        <Card className="bg-[color:var(--card)]/30 border border-[color:var(--border)] transition-all duration-200 hover:shadow-sm">
          <div className="p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <FontAwesomeIcon icon={faRobot} className="text-[color:var(--primary)] text-sm animate-pulse" />
                <span className="text-sm font-medium text-[color:var(--foreground)]">
                  {t('chat.agentManagement.currentAgent')}
                </span>
              </div>
              {onOpenAgentManagement && (
                <Button
                  onClick={onOpenAgentManagement}
                  size="sm"
                  variant="default"
                  className="h-7 px-2 text-xs text-[color:var(--foreground)] bg-[color:var(--accent)] hover:bg-[color:var(--accent)]/80 transition-all duration-200 cursor-pointer group"
                >
                  <FontAwesomeIcon icon={faCog} className="mr-1 text-[color:var(--foreground)] group-hover:rotate-90 transition-transform duration-300" />
                  {t('chat.agentManagement.manage')}
                </Button>
              )}
            </div>
            
            <div className="text-xs text-[color:var(--muted-foreground)]">
              {agentStatus === 'loading' && (
                <div className="flex items-center gap-2">
                  <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                  <span>{t('chat.agentManagement.agentLoading')}</span>
                </div>
              )}
              
              {agentStatus === 'error' && (
                <div className="text-red-500 animate-pulse">
                  {t('chat.agentManagement.agentError')}
                </div>
              )}
              
              {agentStatus === 'success' && currentAgent && (
                <div className="animate-fadeIn">
                  <div className="font-medium text-[color:var(--foreground)]">
                    {currentAgent.model_name}
                  </div>
                  <div className="text-[color:var(--muted-foreground)]">
                    {currentAgent.provider} • T:{currentAgent.temperature} • Max:{currentAgent.max_tokens}
                  </div>
                </div>
              )}
              
              {(!agentStatus || agentStatus === 'none') && !currentAgent && (
                <div className="text-[color:var(--muted-foreground)]">
                  {t('chat.agentManagement.noAgentConfigured')}
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-[color:var(--muted)] scrollbar-track-transparent">
        {conversations.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8 animate-fadeIn">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105">
              <FontAwesomeIcon icon={faComments} className="text-2xl" />
            </div>
            <p>{t('chat.noConversationsYet')}</p>
            <p className="text-sm">{t('chat.createFirstChat')}</p>
          </div>
        ) : (
          conversations.map((conversation, index) => (
            <Card
              key={conversation.id}
              className={`p-3 cursor-pointer transition-all duration-200 hover:shadow-md backdrop-blur-sm hover:scale-[1.02] transform ${
                conversation.id === activeConversationId
                  ? 'bg-gradient-to-r from-[color:var(--primary)]/10 to-[color:var(--primary)]/5 border-[color:var(--primary)]/20 shadow-md'
                  : 'bg-[color:var(--card)] hover:bg-[color:var(--accent)]/50 border-[color:var(--border)]'
              }`}
              style={{
                animationDelay: `${index * 50}ms`
              }}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="flex items-center justify-between">
                {editingId === conversation.id ? (
                  <div className="flex-1 flex items-center gap-2 animate-slideIn">
                    <input
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      className="flex-1 px-2 py-1 text-sm bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none transition-all duration-200"
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
                      className="h-6 w-6 p-0 hover:scale-110 transition-transform duration-200"
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
                      className="h-6 w-6 p-0 hover:scale-110 transition-transform duration-200"
                    >
                      <FontAwesomeIcon icon={faTimes} className="text-red-600 text-xs" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-sm text-[color:var(--foreground)] truncate">
                          {conversation.name}
                        </h3>
                        {conversation.systemPrompt && (
                          <div 
                            className="w-2 h-2 bg-[color:var(--primary)] rounded-full flex-shrink-0 animate-pulse"
                            title={t('chat.tooltips.hasCustomSystemPrompt')}
                          />
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-[color:var(--muted-foreground)]">
                          {conversation.lastActivity.toLocaleDateString()}
                        </p>
                        {conversation.messageCount !== undefined && (
                          <span className="text-xs text-[color:var(--muted-foreground)]">
                            • {conversation.messageCount} {t('chat.messages')}
                          </span>
                        )}
                      </div>
                      {conversation.systemPrompt && (
                        <p className="text-xs text-[color:var(--muted-foreground)] italic truncate mt-1">
                          &ldquo;{conversation.systemPrompt.substring(0, 50)}...&rdquo;
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col gap-1 ml-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          startEditing(conversation)
                        }}
                        className="h-6 w-6 p-0 hover:bg-[color:var(--accent)] hover:scale-110 transition-all duration-200"
                        title={t('chat.tooltips.editName')}
                      >
                        <FontAwesomeIcon icon={faEdit} className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]" />
                      </Button>
                      {onOpenSystemPromptEditor && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation()
                            onOpenSystemPromptEditor(conversation.id)
                          }}
                          className="h-6 w-6 p-0 hover:bg-[color:var(--accent)] hover:scale-110 transition-all duration-200"
                          title={t('chat.tooltips.editSystemPrompt')}
                        >
                          <FontAwesomeIcon icon={faFileText} className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]" />
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteConversation(conversation.id)
                        }}
                        className="h-6 w-6 p-0 hover:bg-[color:var(--destructive)]/10 hover:scale-110 transition-all duration-200"
                        title={t('chat.tooltips.deleteConversation')}
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
