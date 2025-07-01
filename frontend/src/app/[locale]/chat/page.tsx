import { ChatClientWrapper } from '@/components/chat/ChatClientWrapper'
import ClientWrapper from '@/components/layout/client-wrapper'
import { TranslationProvider } from '@/contexts/TranslationContext'
import { getCurrentLocale } from '@/utils/getCurrentLocale'
import getDictionary from '@/utils/translation'

export default async function ChatPage() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)

  return (
    <ClientWrapper>
        <div className="h-[calc(100vh-56px)] bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
          <div className="h-full bg-background overflow-hidden">
            <TranslationProvider dictionary={dictionary} locale={locale}>
              <ChatClientWrapper />
            </TranslationProvider>
          </div>
        </div>
    </ClientWrapper>
  )
}
