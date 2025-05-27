import 'server-only'
import type { Locale } from '@/i18n.config'

// Dictionary type definitions
type Dictionary = Record<string, unknown>

// Dictionary cache để tránh load lại
const dictionaries: Record<Locale, () => Promise<Dictionary>> = {
  vi: () => import('@/locales/vi.json').then((module) => module.default),
  en: () => import('@/locales/en.json').then((module) => module.default),
}

// Dictionary cache
const dictionaryCache: Record<Locale, Dictionary> = {} as Record<Locale, Dictionary>

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  // Kiểm tra cache trước
  if (dictionaryCache[locale]) {
    return dictionaryCache[locale]
  }

  try {
    const dictionary = await dictionaries[locale]()
    dictionaryCache[locale] = dictionary
    return dictionary
  } catch (error) {
    console.error(`Failed to load dictionary for locale: ${locale}`, error)
    // Fallback về tiếng Việt nếu có lỗi
    if (locale !== 'vi') {
      return getDictionary('vi')
    }
    throw error
  }
}

// Helper function để lấy nested value
export function getNestedValue(obj: Dictionary, path: string): string {
  const result = path.split('.').reduce((current: Dictionary | unknown, key: string): unknown => {
    if (current && typeof current === 'object' && current !== null) {
      return (current as Record<string, unknown>)[key]
    }
    return undefined
  }, obj)
  
  return typeof result === 'string' ? result : path
}

// Translation function với type safety
export function createTranslator(dictionary: Dictionary) {
  return function t(key: string, params?: Record<string, string | number>): string {
    let translation = getNestedValue(dictionary, key)
    
    // Thay thế parameters nếu có
    if (params && typeof translation === 'string') {
      Object.entries(params).forEach(([param, value]) => {
        translation = translation.replace(new RegExp(`{{${param}}}`, 'g'), String(value))
      })
    }
    
    return translation || key
  }
}

// Default export cho compatibility
export default getDictionary