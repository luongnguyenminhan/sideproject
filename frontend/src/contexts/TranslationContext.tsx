'use client'

import { createContext, useContext, useMemo } from 'react'
import { getNestedValue } from '@/utils/translationHelpers'

// Type definitions
export type Dictionary = Record<string, unknown>

interface TranslationContextType {
  t: (key: string, params?: Record<string, string | number>) => string
  locale: string
}

const TranslationContext = createContext<TranslationContextType | null>(null)

interface TranslationProviderProps {
  children: React.ReactNode
  dictionary: Dictionary
  locale: string
}

export function TranslationProvider({ 
  children, 
  dictionary, 
  locale 
}: TranslationProviderProps) {
  const t = useMemo(() => {
    return function(key: string, params?: Record<string, string | number>): string {
      let translation = getNestedValue(dictionary, key)
      
      // Thay thế parameters nếu có
      if (params && typeof translation === 'string') {
        Object.entries(params).forEach(([param, value]) => {
          translation = translation.replace(new RegExp(`{{${param}}}`, 'g'), String(value))
        })
      }
      
      return translation || key
    }
  }, [dictionary])

  const value = useMemo(() => ({
    t,
    locale
  }), [t, locale])

  return (
    <TranslationContext.Provider value={value}>
      {children}
    </TranslationContext.Provider>
  )
}

export function useTranslation() {
  const context = useContext(TranslationContext)
  if (!context) {
    throw new Error('useTranslation must be used within TranslationProvider')
  }
  return context
} 