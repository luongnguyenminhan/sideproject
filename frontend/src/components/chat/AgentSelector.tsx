'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRobot, faChevronDown, faCheck } from '@fortawesome/free-solid-svg-icons'

export interface Agent {
  id: string
  name: string
  description: string
  provider: string
  model?: string
  avatar?: string
}

interface AgentSelectorProps {
  agents: Agent[]
  selectedAgent: Agent | null
  onSelectAgent: (agent: Agent) => void
  translations: {
    selectAgent: string
    currentAgent: string
    changeAgent: string
    agentDescription: string
  }
}

// Mock data for agents
export const mockAgents: Agent[] = [
  {
    id: 'chatgpt-4',
    name: 'ChatGPT-4',
    description: 'General purpose AI assistant for various tasks',
    provider: 'OpenAI',
    model: 'gpt-4-turbo',
    avatar: '🤖'
  },
  {
    id: 'claude-3',
    name: 'Claude 3',
    description: 'Anthropic\'s AI assistant, great for analysis and writing',
    provider: 'Anthropic',
    model: 'claude-3-sonnet',
    avatar: '🧠'
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    description: 'Google\'s AI model with multimodal capabilities',
    provider: 'Google',
    model: 'gemini-pro',
    avatar: '✨'
  },
  {
    id: 'code-llama',
    name: 'Code Llama',
    description: 'Meta\'s code-specialized language model',
    provider: 'Meta',
    model: 'code-llama-70b',
    avatar: '💻'
  },
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    description: 'Latest GPT-4 model with enhanced capabilities',
    provider: 'OpenAI',
    model: 'gpt-4-turbo-preview',
    avatar: '🚀'
  }
]

export function AgentSelector({
  agents = mockAgents,
  selectedAgent,
  onSelectAgent,
  translations
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleSelectAgent = (agent: Agent) => {
    onSelectAgent(agent)
    setIsOpen(false)
  }

  const currentAgent = selectedAgent || agents[0]

  return (
    <div className="relative">
      {/* Current Agent Display */}
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        size="sm"
        className="flex items-center gap-2 bg-[color:var(--card)] border-[color:var(--border)] hover:bg-[color:var(--accent)] text-[color:var(--foreground)]"
      >
        <span className="text-lg">{currentAgent.avatar}</span>
        <div className="flex flex-col items-start text-left">
          <span className="text-xs text-[color:var(--muted-foreground)]">
            {translations.currentAgent}
          </span>
          <span className="text-sm font-medium">{currentAgent.name}</span>
        </div>
        <FontAwesomeIcon 
          icon={faChevronDown} 
          className={`text-xs transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </Button>

      {/* Agent Selection Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown Content */}
          <Card className="absolute top-full right-0 mt-2 w-80 z-50 bg-[color:var(--card)] border-[color:var(--border)] shadow-lg backdrop-blur-sm">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <FontAwesomeIcon icon={faRobot} className="text-[color:var(--primary)]" />
                <h3 className="font-semibold text-[color:var(--foreground)]">
                  {translations.selectAgent}
                </h3>
              </div>
              
              <p className="text-sm text-[color:var(--muted-foreground)] mb-4">
                {translations.agentDescription}
              </p>

              <div className="space-y-2">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => handleSelectAgent(agent)}
                    className={`w-full p-3 rounded-lg border transition-all duration-200 text-left hover:bg-[color:var(--accent)] ${
                      currentAgent.id === agent.id
                        ? 'border-[color:var(--primary)] bg-[color:var(--primary)]/5'
                        : 'border-[color:var(--border)]'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xl">{agent.avatar}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-[color:var(--foreground)]">
                            {agent.name}
                          </h4>
                          {currentAgent.id === agent.id && (
                            <FontAwesomeIcon 
                              icon={faCheck} 
                              className="text-xs text-[color:var(--primary)]" 
                            />
                          )}
                        </div>
                        <p className="text-sm text-[color:var(--muted-foreground)] mt-1">
                          {agent.description}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs px-2 py-1 rounded bg-[color:var(--muted)] text-[color:var(--muted-foreground)]">
                            {agent.provider}
                          </span>
                          {agent.model && (
                            <span className="text-xs px-2 py-1 rounded bg-[color:var(--primary)]/10 text-[color:var(--primary)]">
                              {agent.model}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}