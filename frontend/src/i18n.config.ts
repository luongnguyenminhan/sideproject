export const i18n = {
  defaultLocale: 'vi',
  locales: ['vi', 'en']
} as const

export type Locale = (typeof i18n)['locales'][number]

export const languages = {
  vi: {
    name: 'Tiếng Việt',
    flag: '🇻🇳'
  },
  en: {
    name: 'English', 
    flag: '��🇸'
  }
} as const