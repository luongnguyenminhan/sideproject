import { ChatClientWrapper } from '@/components/chat/ChatClientWrapper'
import ClientWrapper from '@/components/layout/client-wrapper'
import { getCurrentLocale } from '@/utils/getCurrentLocale'
import getDictionary from '@/utils/translation'
import { TranslationProvider } from '@/contexts/TranslationContext'
import Header from '@/components/layout/header'

export default async function ChatPage() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)

  return (
    <ClientWrapper>
        <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
          <Header withChatBubble={true} />

          <div className="h-[calc(100vh-56px)] bg-background overflow-hidden">
            <TranslationProvider dictionary={dictionary} locale={locale}>
              <ChatClientWrapper />
            </TranslationProvider>
          </div>
        </div>
    </ClientWrapper>
  )
}
