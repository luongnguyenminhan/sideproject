'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faKey, faEye, faEyeSlash, faCheck, faSpinner, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface ApiKeyManagerProps {
  currentApiKey?: {
    provider: string
    hasKey: boolean
    maskedKey?: string
  }
  onUpdateApiKey: (provider: string, apiKey: string) => Promise<void>
  isLoading?: boolean
}

const PROVIDERS = [
  { value: 'google', label: 'Google (Gemini)' },
  { value: 'openai', label: 'OpenAI (GPT)' },
  { value: 'anthropic', label: 'Anthropic (Claude)' }
]

export function ApiKeyManager({
  currentApiKey,
  onUpdateApiKey,
  isLoading = false
}: ApiKeyManagerProps) {
  const { t } = useTranslation()
  const [selectedProvider, setSelectedProvider] = useState(currentApiKey?.provider || 'google')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [updateStatus, setUpdateStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [isEditing, setIsEditing] = useState(false)

  const handleSave = async () => {
    if (!apiKey.trim()) return

    try {
      setUpdateStatus('idle')
      await onUpdateApiKey(selectedProvider, apiKey.trim())
      setUpdateStatus('success')
      setApiKey('')
      setIsEditing(false)
      setShowKey(false)
      
      // Clear success message after 3 seconds
      setTimeout(() => setUpdateStatus('idle'), 3000)
    } catch (error) {
      console.error('Failed to update API key:', error)
      setUpdateStatus('error')
      setTimeout(() => setUpdateStatus('idle'), 5000)
    }
  }

  const handleCancel = () => {
    setApiKey('')
    setIsEditing(false)
    setShowKey(false)
    setUpdateStatus('idle')
  }

  const getProviderLabel = (provider: string) => {
    return PROVIDERS.find(p => p.value === provider)?.label || provider
  }

  return (
    <Card className="p-4 bg-[color:var(--card)] border border-[color:var(--border)]">
      <div className="flex items-center gap-2 mb-4">
        <FontAwesomeIcon icon={faKey} className="text-[color:var(--primary)]" />
        <h3 className="text-lg font-semibold text-[color:var(--foreground)]">
          {t('chat.agentManagement.apiKeyManagement.title')}
        </h3>
      </div>

      <p className="text-sm text-[color:var(--muted-foreground)] mb-4">
        {t('chat.agentManagement.apiKeyManagement.description')}
      </p>

      {/* Current API Key Status */}
      <div className="mb-4 p-3 bg-[color:var(--muted)]/30 border border-[color:var(--border)] rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[color:var(--foreground)]">
              {t('chat.agentManagement.apiKeyManagement.currentKey')}
            </p>
            {currentApiKey?.hasKey ? (
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded">
                  ✓ {getProviderLabel(currentApiKey.provider)}
                </span>
                {currentApiKey.maskedKey && (
                  <span className="text-xs text-[color:var(--muted-foreground)] font-mono">
                    {currentApiKey.maskedKey}
                  </span>
                )}
              </div>
            ) : (
              <p className="text-xs text-[color:var(--muted-foreground)] mt-1">
                {t('chat.agentManagement.apiKeyManagement.noKeySet')}
              </p>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
            disabled={isLoading}
          >
            {t('chat.agentManagement.apiKeyManagement.update')}
          </Button>
        </div>
      </div>

      {/* Update Form */}
      {isEditing && (
        <div className="space-y-4 p-4 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">
              {t('chat.agentManagement.apiKeyManagement.selectProvider')}
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full p-2 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none"
              disabled={isLoading}
            >
              {PROVIDERS.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          {/* API Key Input */}
          <div>
            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">
              {t('chat.agentManagement.apiKeyManagement.enterApiKey')}
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={t('chat.agentManagement.apiKeyManagement.apiKeyPlaceholder')}
                className="w-full p-2 pr-10 bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]"
                title={showKey ? t('chat.agentManagement.apiKeyManagement.hideKey') : t('chat.agentManagement.apiKeyManagement.showKey')}
              >
                <FontAwesomeIcon icon={showKey ? faEyeSlash : faEye} className="text-sm" />
              </button>
            </div>
          </div>

          {/* Status Messages */}
          {updateStatus === 'success' && (
            <div className="flex items-center gap-2 p-2 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-lg">
              <FontAwesomeIcon icon={faCheck} />
              <span className="text-sm">{t('chat.agentManagement.apiKeyManagement.keyUpdated')}</span>
            </div>
          )}

          {updateStatus === 'error' && (
            <div className="flex items-center gap-2 p-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg">
              <FontAwesomeIcon icon={faExclamationTriangle} />
              <span className="text-sm">{t('chat.agentManagement.apiKeyManagement.updateFailed')}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={!apiKey.trim() || isLoading}
              className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)]"
            >
              <FontAwesomeIcon icon={isLoading ? faSpinner : faCheck} className={isLoading ? 'animate-spin mr-2' : 'mr-2'} />
              {isLoading ? '...' : t('common.save')}
            </Button>
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={isLoading}
            >
              {t('common.cancel')}
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
} 