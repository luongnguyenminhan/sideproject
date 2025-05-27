import { headers } from 'next/headers'
import type { Locale } from '@/i18n.config'
import { i18n } from '@/i18n.config'

export async function getCurrentLocale(): Promise<Locale> {
  const headersList = await headers()
  const locale = headersList.get('x-locale') as Locale
  
  return locale || i18n.defaultLocale
}

export function getLocaleFromUrl(pathname: string): Locale {
  const segments = pathname.split('/').filter(Boolean)
  const firstSegment = segments[0] as Locale
  
  return i18n.locales.includes(firstSegment) ? firstSegment : i18n.defaultLocale
}