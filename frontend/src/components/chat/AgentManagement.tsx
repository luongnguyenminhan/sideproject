'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRobot, faKey, faCheck, faSpinner, faCog, faExclamationCircle } from '@fortawesome/free-solid-svg-icons'
import chatApi from '@/apis/chatApi'
import { ApiKeyManager } from './ApiKeyManager'
import { useTranslation } from '@/contexts/TranslationContext'

interface AgentConfig {
  model_name: string
  provider: string
  temperature: number
  max_tokens: number
}

interface ModelInfo {
  name: string
  display_name: string
  description?: string
}

interface AgentManagementProps {
  onAgentUpdate?: (agent: AgentConfig) => void
}

export function AgentManagement({ onAgentUpdate }: AgentManagementProps) {
  const { t } = useTranslation()
  const [currentAgent, setCurrentAgent] = useState<AgentConfig | null>(null)
  const [availableModels, setAvailableModels] = useState<Record<string, ModelInfo[]>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    status: 'valid' | 'invalid' | null
    message: string
  }>({ status: null, message: '' })
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState<AgentConfig>({
    model_name: '',
    provider: '',
    temperature: 0.7,
    max_tokens: 1000
  })
  const [currentApiKey, setCurrentApiKey] = useState<{
    provider: string
    hasKey: boolean
    maskedKey?: string
  } | undefined>(undefined)
  const [activeTab, setActiveTab] = useState<'agent' | 'apikey' | 'validation'>('agent')
  const [isOpen,] = useState(false)

  // Load current agent configuration
  const loadCurrentAgent = async () => {
    try {
      setIsLoading(true)
      const response = await chatApi.getCurrentAgent()
      if (response) {
        const agentConfig: AgentConfig = {
          model_name: response.model_name,
          provider: response.model_provider,
          temperature: response.temperature,
          max_tokens: response.max_tokens
        }
        
        setCurrentAgent(agentConfig)
        setEditForm(agentConfig)
        
        // Set API key info
        setCurrentApiKey({
          provider: response.api_provider,
          hasKey: response.has_api_key,
          maskedKey: response.has_api_key ? `••••••••${response.api_provider.slice(-4)}` : undefined
        })
      }
    } catch (error) {
      console.error('Failed to load current agent:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Load available models
  const loadAvailableModels = async () => {
    try {
      setIsLoading(true)
      const response = await chatApi.getAvailableModels()
      if (response?.providers) {
        const modelsMap: Record<string, ModelInfo[]> = {}
        
        response.providers.forEach(({ provider, models }) => {
          modelsMap[provider] = models.map(modelName => ({
            name: modelName,
            display_name: modelName,
            description: `${provider} model: ${modelName}`
          }))
        })
        
        setAvailableModels(modelsMap)
      }
    } catch (error) {
      console.error('Failed to load available models:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Update agent configuration
  const updateAgentConfig = async () => {
    try {
      setIsLoading(true)
      const result = await chatApi.updateAgentConfig({
        model_provider: editForm.provider,
        model_name: editForm.model_name,
        temperature: editForm.temperature,
        max_tokens: editForm.max_tokens
      })
      if (result) {
        setCurrentAgent(editForm)
        setIsEditing(false)
        onAgentUpdate?.(editForm)
      }
    } catch (error) {
      console.error('Failed to update agent config:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Update API key
  const handleUpdateApiKey = async (provider: string, apiKey: string) => {
    await chatApi.updateAgentApiKey({
      api_key: apiKey,
      api_provider: provider
    })
    
    // Reload agent to get updated API key status
    await loadCurrentAgent()
  }

  // Validate agent
  const validateAgent = async () => {
    try {
      setIsValidating(true)
      const result = await chatApi.validateAgent()
      if (result) {
        setValidationResult({
          status: result.is_valid ? 'valid' : 'invalid',
          message: result.test_response || result.error_message || t('chat.agentManagement.validationCompleted')
        })
      }
    } catch (error) {
      console.error('Failed to validate agent:', error)
      setValidationResult({
        status: 'invalid',
        message: 'Validation failed'
      })
    } finally {
      setIsValidating(false)
    }
  }

  useEffect(() => {
      loadCurrentAgent()
      loadAvailableModels()
      // Prevent scrolling
      document.body.style.overflow = 'hidden'
  }, [isOpen])

  const tabs = [
    { id: 'agent', label: t('chat.agentManagement.agentTab'), icon: faRobot },
    { id: 'apikey', label: t('chat.agentManagement.apiKeyTab'), icon: faKey },
    { id: 'validation', label: t('chat.agentManagement.validationTab'), icon: faCheck }
  ]


  return (
            <div className="overflow-y-auto max-h-[90vh] p-8">
              {/* Header */}
              <div className="text-center space-y-4 mb-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] flex items-center justify-center shadow-lg">
                  <FontAwesomeIcon icon={faRobot} className="w-8 h-8 text-white" />
                </div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
                  {t('chat.agentManagement.title') || 'Agent Management'}
                </h1>
                <p className="text-[color:var(--muted-foreground)] text-lg">
                  {t('chat.agentManagement.subtitle') || 'Configure and manage your AI agent settings'}
                </p>
              </div>

              {/* Tab Navigation */}
              <div className="flex space-x-1 bg-white/60 dark:bg-gray-800/60 backdrop-blur-md p-1 rounded-2xl shadow-lg border border-white/20 dark:border-gray-700/20 mb-6">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as 'agent' | 'apikey' | 'validation')}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium transition-all duration-300 ${
                      activeTab === tab.id
                        ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white shadow-lg transform scale-105'
                        : 'text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)] hover:bg-white/50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <FontAwesomeIcon icon={tab.icon} className="w-4 h-4" />
                    <span className="text-sm">{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Agent Configuration Tab */}
              {activeTab === 'agent' && (
                <div className="space-y-6">
                  {/* Current Agent Display */}
                  <Card 
                    className="border-0 shadow-xl overflow-hidden"
                    style={{
                      borderRadius: '20px',
                      background: 'var(--auth-card-bg)',
                      border: '1px solid var(--auth-card-border)'
                    }}
                  >
                    <div className="p-6">
                      <h3 className="text-xl font-semibold mb-6 flex items-center gap-3 text-[color:var(--foreground)]">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] flex items-center justify-center">
                          <FontAwesomeIcon icon={faRobot} className="text-white" />
                        </div>
                        {t('chat.agentManagement.currentAgent')}
                      </h3>
                      
                      {currentAgent ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-3">
                            <div className="flex items-center gap-3 p-4 rounded-xl bg-[color:var(--feature-blue)]/10 border border-[color:var(--feature-blue)]/20">
                              <div className="w-8 h-8 rounded-lg bg-[color:var(--feature-blue-text)] flex items-center justify-center">
                                <FontAwesomeIcon icon={faRobot} className="text-white w-4 h-4" />
                              </div>
                              <div>
                                <p className="text-sm text-[color:var(--muted-foreground)]">{t('chat.agentManagement.provider')}</p>
                                <p className="font-semibold text-[color:var(--foreground)]">{currentAgent.provider}</p>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-4 rounded-xl bg-[color:var(--feature-green)]/10 border border-[color:var(--feature-green)]/20">
                              <div className="w-8 h-8 rounded-lg bg-[color:var(--feature-green-text)] flex items-center justify-center">
                                <FontAwesomeIcon icon={faCog} className="text-white w-4 h-4" />
                              </div>
                              <div>
                                <p className="text-sm text-[color:var(--muted-foreground)]">{t('chat.agentManagement.modelName')}</p>
                                <p className="font-semibold text-[color:var(--foreground)]">{currentAgent.model_name}</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <div className="flex items-center gap-3 p-4 rounded-xl bg-[color:var(--feature-purple)]/10 border border-[color:var(--feature-purple)]/20">
                              <div className="w-8 h-8 rounded-lg bg-[color:var(--feature-purple-text)] flex items-center justify-center">
                                <span className="text-white text-xs font-bold">T</span>
                              </div>
                              <div>
                                <p className="text-sm text-[color:var(--muted-foreground)]">{t('chat.agentManagement.temperature')}</p>
                                <p className="font-semibold text-[color:var(--foreground)]">{currentAgent.temperature}</p>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-4 rounded-xl bg-[color:var(--feature-yellow)]/10 border border-[color:var(--feature-yellow)]/20">
                              <div className="w-8 h-8 rounded-lg bg-[color:var(--feature-yellow-text)] flex items-center justify-center">
                                <span className="text-white text-xs font-bold">T</span>
                              </div>
                              <div>
                                <p className="text-sm text-[color:var(--muted-foreground)]">{t('chat.agentManagement.maxTokens')}</p>
                                <p className="font-semibold text-[color:var(--foreground)]">{currentAgent.max_tokens}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[color:var(--muted)]/20 flex items-center justify-center">
                            <FontAwesomeIcon icon={faRobot} className="w-8 h-8 text-[color:var(--muted-foreground)]" />
                          </div>
                          <p className="text-[color:var(--muted-foreground)] text-lg">
                            {isLoading ? t('common.loading') : t('chat.agentManagement.noAgentConfigured')}
                          </p>
                        </div>
                      )}
                    </div>
                  </Card>

                  {/* Agent Configuration Form */}
                  {isEditing && (
                    <Card 
                      className="border-0 shadow-xl overflow-hidden"
                      style={{
                        borderRadius: '20px',
                        background: 'var(--auth-card-bg)',
                        border: '1px solid var(--auth-card-border)'
                      }}
                    >
                      <div className="p-6">
                        <h3 className="text-xl font-semibold mb-6 flex items-center gap-3 text-[color:var(--foreground)]">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[color:var(--feature-purple)] to-[color:var(--feature-blue)] flex items-center justify-center">
                            <FontAwesomeIcon icon={faCog} className="text-white" />
                          </div>
                          {t('chat.agentManagement.agentConfig')}
                        </h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">{t('chat.agentManagement.provider')}</label>
                            <select
                              value={editForm.provider}
                              onChange={(e) => setEditForm(prev => ({ ...prev, provider: e.target.value, model_name: '' }))}
                              className="w-full p-3 bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 rounded-xl text-[color:var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[color:var(--primary)] transition-all duration-300"
                            >
                              <option value="">{t('chat.agentManagement.selectProvider')}</option>
                              {Object.keys(availableModels).map((provider) => (
                                <option key={provider} value={provider}>
                                  {provider}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">{t('chat.agentManagement.modelName')}</label>
                            <select
                              value={editForm.model_name}
                              onChange={(e) => setEditForm(prev => ({ ...prev, model_name: e.target.value }))}
                              className="w-full p-3 bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 rounded-xl text-[color:var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[color:var(--primary)] transition-all duration-300 disabled:opacity-50"
                              disabled={!editForm.provider}
                            >
                              <option value="">{t('chat.agentManagement.selectModel')}</option>
                              {editForm.provider && availableModels[editForm.provider]?.map((model) => (
                                <option key={model.name} value={model.name}>
                                  {model.display_name}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">{t('chat.agentManagement.temperature')}</label>
                            <input
                              type="number"
                              min="0"
                              max="2"
                              step="0.1"
                              value={editForm.temperature}
                              onChange={(e) => setEditForm(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                              className="w-full p-3 bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 rounded-xl text-[color:var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[color:var(--primary)] transition-all duration-300"
                            />
                          </div>

                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-[color:var(--foreground)] mb-2">{t('chat.agentManagement.maxTokens')}</label>
                            <input
                              type="number"
                              min="1"
                              max="4000"
                              value={editForm.max_tokens}
                              onChange={(e) => setEditForm(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                              className="w-full p-3 bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 rounded-xl text-[color:var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[color:var(--primary)] transition-all duration-300"
                            />
                          </div>
                        </div>

                        <div className="flex gap-3 mt-8">
                          <Button
                            onClick={updateAgentConfig}
                            disabled={isLoading}
                            className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white border-0 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
                          >
                            <FontAwesomeIcon icon={isLoading ? faSpinner : faCheck} className={isLoading ? 'animate-spin mr-2' : 'mr-2'} />
                            {t('common.save')}
                          </Button>
                          <Button
                            onClick={() => setIsEditing(false)}
                            variant="outline"
                            className="bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border-white/20 hover:bg-white/80 dark:hover:bg-gray-600/80 transition-all duration-300"
                          >
                            {t('common.cancel')}
                          </Button>
                        </div>
                      </div>
                    </Card>
                  )}

                  {/* Edit Button */}
                  {!isEditing && (
                    <Button
                      onClick={() => setIsEditing(true)}
                      className="w-full bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white border-0 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 py-4 text-lg rounded-2xl"
                    >
                      <FontAwesomeIcon icon={faCog} className="mr-3" />
                      {t('chat.agentManagement.updateAgent')}
                    </Button>
                  )}
                </div>
              )}

              {/* API Key Management Tab */}
              {activeTab === 'apikey' && (
                <div 
                  className="border-0 shadow-xl overflow-hidden"
                  style={{
                    borderRadius: '20px',
                    background: 'var(--auth-card-bg)',
                    border: '1px solid var(--auth-card-border)'
                  }}
                >
                  <ApiKeyManager
                    currentApiKey={currentApiKey}
                    onUpdateApiKey={handleUpdateApiKey}
                    isLoading={isLoading}
                  />
                </div>
              )}

              {/* Validation Tab */}
              {activeTab === 'validation' && (
                <Card 
                  className="border-0 shadow-xl overflow-hidden"
                  style={{
                    borderRadius: '20px',
                    background: 'var(--auth-card-bg)',
                    border: '1px solid var(--auth-card-border)'
                  }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-3 text-[color:var(--foreground)]">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[color:var(--feature-green)] to-[color:var(--feature-blue)] flex items-center justify-center">
                        <FontAwesomeIcon icon={faCheck} className="text-white" />
                      </div>
                      {t('chat.agentManagement.validateAgent')}
                    </h3>
                    
                    <div className="space-y-6">
                      <div className="p-4 rounded-xl bg-[color:var(--feature-blue)]/10 border border-[color:var(--feature-blue)]/20">
                        <p className="text-[color:var(--muted-foreground)]">
                          {t('chat.agentManagement.testMessage') || 'Test your agent configuration with a sample message.'}
                        </p>
                      </div>
                      
                      <Button
                        onClick={validateAgent}
                        disabled={isValidating || !currentAgent}
                        className="w-full bg-gradient-to-r from-[color:var(--feature-green-text)] to-[color:var(--feature-blue-text)] text-white border-0 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 py-4 text-lg rounded-2xl disabled:opacity-50 disabled:transform-none"
                      >
                        <FontAwesomeIcon 
                          icon={isValidating ? faSpinner : faCheck} 
                          className={isValidating ? 'animate-spin mr-3' : 'mr-3'} 
                        />
                        {isValidating ? t('common.loading') : t('chat.agentManagement.validateAgent')}
                      </Button>

                      {validationResult.status && (
                        <div className={`flex items-start gap-4 p-6 rounded-2xl backdrop-blur-md ${
                          validationResult.status === 'valid' 
                            ? 'bg-[color:var(--feature-green)]/20 border border-[color:var(--feature-green)]/30' 
                            : 'bg-red-100/20 dark:bg-red-900/20 border border-red-300/30 dark:border-red-700/30'
                        }`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            validationResult.status === 'valid'
                              ? 'bg-[color:var(--feature-green-text)]'
                              : 'bg-red-500'
                          }`}>
                            <FontAwesomeIcon 
                              icon={validationResult.status === 'valid' ? faCheck : faExclamationCircle} 
                              className="text-white w-4 h-4"
                            />
                          </div>
                          <div className="flex-1">
                            <p className={`font-semibold text-lg mb-2 ${
                              validationResult.status === 'valid' 
                                ? 'text-[color:var(--feature-green-text)]' 
                                : 'text-red-600 dark:text-red-400'
                            }`}>
                              {validationResult.status === 'valid' 
                                ? t('chat.agentManagement.validationSuccess') || 'Validation Successful'
                                : t('chat.agentManagement.validationFailed') || 'Validation Failed'
                              }
                            </p>
                            <p className="text-[color:var(--muted-foreground)]">{validationResult.message}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              )}
            </div>
  )
}
