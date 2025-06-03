'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSave, faTimes, faEye, faEdit, faInfo } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface SystemPromptEditorProps {
  conversationId: string
  currentPrompt?: string
  agentSystemPrompt?: string
  onSave: (conversationId: string, prompt: string) => Promise<void>
  onCancel: () => void
  isOpen: boolean
  isLoading?: boolean
}

export function SystemPromptEditor({
  conversationId,
  currentPrompt = '',
  agentSystemPrompt,
  onSave,
  onCancel,
  isOpen,
  isLoading = false
}: SystemPromptEditorProps) {
  const { t } = useTranslation()
  const [prompt, setPrompt] = useState(currentPrompt)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const maxLength = 4000

  useEffect(() => {
    setPrompt(currentPrompt)
  }, [currentPrompt])

  const handleSave = async () => {
    if (prompt.length <= maxLength) {
      try {
        await onSave(conversationId, prompt.trim())
      } catch (error) {
        console.error('Failed to save system prompt:', error)
      }
    }
  }

  const handleCancel = () => {
    setPrompt(currentPrompt)
    setIsPreviewMode(false)
    onCancel()
  }

  const getCharacterCountColor = () => {
    const percentage = (prompt.length / maxLength) * 100
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 70) return 'text-yellow-600'
    return 'text-[color:var(--muted-foreground)]'
  }

  const activePrompt = prompt.trim() || agentSystemPrompt || ''
  const promptSource = prompt.trim() 
    ? t('chat.systemPrompt.conversationPrompt')
    : agentSystemPrompt 
      ? t('chat.systemPrompt.agentPrompt')
      : t('chat.systemPrompt.noAgentPrompt')

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden bg-[color:var(--card)] shadow-xl">
          {/* Header */}
          <div className="p-6 border-b border-[color:var(--border)]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-[color:var(--foreground)]">
                  {t('chat.systemPrompt.title')}
                </h2>
                <p className="text-sm text-[color:var(--muted-foreground)] mt-1">
                  {t('chat.systemPrompt.description')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPreviewMode(!isPreviewMode)}
                >
                  <FontAwesomeIcon icon={isPreviewMode ? faEdit : faEye} className="mr-2" />
                  {isPreviewMode ? t('chat.systemPrompt.edit') : t('chat.systemPrompt.preview')}
                </Button>
                <Button variant="outline" size="sm" onClick={handleCancel}>
                  <FontAwesomeIcon icon={faTimes} />
                </Button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* Prompt Source Info */}
            <div className="mb-4 p-3 bg-[color:var(--muted)]/50 rounded-lg border border-[color:var(--border)]">
              <div className="flex items-center gap-2 mb-2">
                <FontAwesomeIcon icon={faInfo} className="text-[color:var(--primary)]" />
                <span className="text-sm font-medium text-[color:var(--foreground)]">
                  {t('chat.systemPrompt.promptSource')}
                </span>
              </div>
              <p className="text-sm text-[color:var(--muted-foreground)]">
                {promptSource}
              </p>
            </div>

            {/* Agent System Prompt Display */}
            {agentSystemPrompt && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[color:var(--foreground)] mb-2">
                  {t('chat.systemPrompt.agentPrompt')}
                </h3>
                <div className="p-3 bg-[color:var(--muted)]/30 border border-[color:var(--border)] rounded-lg">
                  <p className="text-sm text-[color:var(--muted-foreground)] whitespace-pre-wrap">
                    {agentSystemPrompt.length > 200 
                      ? `${agentSystemPrompt.substring(0, 200)}...`
                      : agentSystemPrompt
                    }
                  </p>
                </div>
              </div>
            )}

            {/* Editor/Preview */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-[color:var(--foreground)]">
                  {t('chat.systemPrompt.conversationPrompt')}
                </h3>
                <span className={`text-xs ${getCharacterCountColor()}`}>
                  {t('chat.systemPrompt.characterCount', { current: prompt.length, max: maxLength })}
                </span>
              </div>

              {isPreviewMode ? (
                <div className="min-h-[200px] p-4 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {activePrompt ? (
                      <p className="whitespace-pre-wrap text-[color:var(--foreground)]">
                        {activePrompt}
                      </p>
                    ) : (
                      <p className="text-[color:var(--muted-foreground)] italic">
                        {t('chat.systemPrompt.placeholder')}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={t('chat.systemPrompt.placeholder')}
                  className="w-full h-[200px] p-4 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none resize-none"
                  maxLength={maxLength}
                />
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-[color:var(--border)] bg-[color:var(--muted)]/20">
            <div className="flex items-center justify-end gap-3">
              <Button variant="outline" onClick={handleCancel} disabled={isLoading}>
                {t('common.cancel')}
              </Button>
              <Button 
                onClick={handleSave} 
                disabled={isLoading || prompt.length > maxLength}
                className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)]"
              >
                <FontAwesomeIcon icon={faSave} className="mr-2" />
                {isLoading ? '...' : t('common.save')}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}