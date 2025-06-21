# EnterViu - Professional Career Platform Frontend

Hệ thống đa ngôn ngữ và theme hiện đại cho Next.js với TypeScript.

## ✨ Tính năng

- 🌍 **Đa ngôn ngữ**: Hỗ trợ tiếng Việt và tiếng Anh
- 🎨 **Dark/Light Mode**: Chuyển đổi theme mượt mà với hỗ trợ system preference
- 🚀 **Performance**: Server-side rendering với caching thông minh
- 📱 **Responsive**: UI đẹp trên mọi thiết bị
- 🔧 **Type-safe**: TypeScript đầy đủ với type safety
- 🎯 **Modern Stack**: Next.js 15, React 19, Tailwind CSS 4

## 📁 Cấu trúc dự án

```
src/
├── app/
│   └── [locale]/
│       ├── layout.tsx         # Root layout với ThemeProvider
│       ├── page.tsx          # Homepage
│       └── globals.css       # Global styles
├── components/
│   ├── global/
│   │   └── languageSwapper.tsx  # Language switcher component
│   ├── theme-provider.tsx    # Theme context provider
│   ├── theme-toggle.tsx      # Theme toggle component
│   └── server-components.tsx # Demo server component
├── utils/
│   ├── translation.ts        # Translation utilities
│   └── getCurrentLocale.ts   # Locale helper functions
├── locales/
│   ├── vi.json              # Vietnamese translations
│   └── en.json              # English translations
├── redux/
│   ├── store.ts             # Redux store configuration
│   ├── hooks.ts             # Typed Redux hooks
│   └── slices/
│       ├── themeSlice.ts    # Theme state management
│       └── localeSlice.ts   # Locale state management
├── i18n.config.ts           # i18n configuration
└── middleware.ts            # Next.js middleware for locale routing
```

## 🚀 Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## 🛠️ Cách sử dụng

### 1. Cấu hình i18n

```typescript
// i18n.config.ts
export const i18n = {
  defaultLocale: 'vi',
  locales: ['vi', 'en']
} as const

export const languages = {
  vi: { name: 'Tiếng Việt', flag: '🇻🇳' },
  en: { name: 'English', flag: '🇺🇸' }
} as const
```

### 2. Sử dụng Translation trong Server Components

```typescript
import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"

export default async function MyComponent() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  return (
    <div>
      <h1>{t('home.title')}</h1>
      <p>{t('home.description')}</p>
    </div>
  )
}
```

### 3. Sử dụng Theme Toggle

```typescript
import { ThemeToggle } from "@/components/theme-toggle"

export default function Header() {
  return (
    <header>
      <ThemeToggle align="end" side="bottom" />
    </header>
  )
}
```

### 4. Sử dụng Language Switcher

```typescript
import LanguageSwitcher from "@/components/global/languageSwapper"

export default function Navigation() {
  return (
    <nav>
      <LanguageSwitcher align="end" side="bottom" />
    </nav>
  )
}
```

## 🎨 Customization

### Thêm ngôn ngữ mới

1. Cập nhật `i18n.config.ts`:
```typescript
export const i18n = {
  defaultLocale: 'vi',
  locales: ['vi', 'en', 'ja'] // Thêm 'ja'
} as const

export const languages = {
  vi: { name: 'Tiếng Việt', flag: '🇻🇳' },
  en: { name: 'English', flag: '🇺🇸' },
  ja: { name: '日本語', flag: '🇯🇵' } // Thêm Japanese
} as const
```

2. Tạo file `locales/ja.json`
3. Cập nhật `translation.ts` để include dictionary mới

## 📝 Best Practices

1. **Server Components**: Sử dụng server components cho translation khi có thể
2. **Caching**: Dictionary được cache tự động
3. **Type Safety**: Luôn sử dụng type-safe translation
4. **Performance**: Lazy load translations
5. **SEO**: Proper locale trong HTML lang attribute

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.
