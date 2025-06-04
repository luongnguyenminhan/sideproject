'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSave, faTimes, faEdit } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface SystemPromptEditorProps {
  conversationId: string
  currentPrompt?: string
  onSave: (conversationId: string, prompt: string) => Promise<void>
  onCancel: () => void
  isOpen: boolean
  isLoading?: boolean
}

export function SystemPromptEditor({
  conversationId,
  currentPrompt = '',
  onSave,
  onCancel,
  isOpen,
  isLoading = false
}: SystemPromptEditorProps) {
  const { t } = useTranslation()
  const [prompt, setPrompt] = useState(currentPrompt)
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
    onCancel()
  }

  const getCharacterCountColor = () => {
    const percentage = (prompt.length / maxLength) * 100
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 70) return 'text-yellow-600'
    return 'text-[color:var(--muted-foreground)]'
  }
 
  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-3xl max-h-[85vh] overflow-hidden bg-[color:var(--card)] shadow-xl border-none">
          {/* Header */}
          <div className="p-4 border-b border-[color:var(--border)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] flex items-center justify-center">
                  <FontAwesomeIcon icon={faEdit} className="text-white w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[color:var(--foreground)]">
                    {t('chat.systemPrompt.title')}
                  </h2>
                  <p className="text-xs text-[color:var(--muted-foreground)]">
                    {t('chat.systemPrompt.description')}
                  </p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <FontAwesomeIcon icon={faTimes} className='text-[color:var(--foreground)]' /> 
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-[55vh]">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-[color:var(--foreground)]">
                  {t('chat.systemPrompt.conversationPrompt')}
                </h3>
                <span className={`text-xs ${getCharacterCountColor()}`}>
                  {prompt.length}/{maxLength}
                </span>
              </div>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={t('chat.systemPrompt.placeholder')}
                className="w-full h-[300px] p-3 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none resize-none text-sm"
                maxLength={maxLength}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-[color:var(--border)] bg-[color:var(--muted)]/20">
            <div className="flex items-center justify-end gap-2">
              <Button variant="outline" onClick={handleCancel} disabled={isLoading} size="sm">
                {t('common.cancel')}
              </Button>
              <Button 
                onClick={handleSave} 
                disabled={isLoading || prompt.length > maxLength}
                className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)]"
                size="sm"
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