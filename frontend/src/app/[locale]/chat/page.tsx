import Header from '@/components/layout/header'
import { ChatClientWrapper } from '@/components/chat/ChatClientWrapper'
import ClientWrapper from '@/components/layout/client-wrapper'
import { getCurrentLocale } from '@/utils/getCurrentLocale'
import getDictionary, { createTranslator } from '@/utils/translation'

export default async function ChatPage() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  // Prepare translations for chat components
  const chatTranslations = {
    welcomeTitle: t('chat.welcomeTitle'),
    welcomeDescription: t('chat.welcomeDescription'),
    addApiKey: t('chat.addApiKey'),
    enterApiKey: t('chat.enterApiKey'),
    apiKeySet: t('chat.apiKeySet'),
    resetApiKey: t('chat.resetApiKey'),
    noMessages: t('chat.noMessages'),
    startConversation: t('chat.startConversation'),
    typeMessage: t('chat.typeMessage'),
    conversations: t('chat.conversations'),
    newConversation: t('chat.newConversation'),
    noConversationsYet: t('chat.noConversationsYet'),
    createFirstChat: t('chat.createFirstChat'),
    messages: t('chat.messages'),
    uploadedFiles: t('chat.uploadedFiles'),
    noFilesUploaded: t('chat.noFilesUploaded'),
    uploadFilesDescription: t('chat.uploadFilesDescription'),
    chats: t('chat.chats'),
    files: t('chat.files'),
    download: t('common.download'),
    delete: t('common.delete'),
    // Add missing translations
    openMenu: t('chat.openMenu'),
    typing: t('chat.typing'),
    sending: t('chat.sending'),
    loading: t('common.loading'),
    save: t('common.save'),
    cancel: t('common.cancel'),
    edit: t('common.edit'),
    change: t('common.change'),
    fix: t('common.fix'),
    invalidApiKey: t('chat.invalidApiKey'),
    keyNameOptional: t('chat.keyNameOptional'),
    pleaseSetupApiKey: t('chat.pleaseSetupApiKey'),
    thisConversation: t('chat.thisConversation'),
    fileCount: t('chat.fileCount'),
    fileCount_plural: t('chat.fileCount_plural'),
    filesAssociated: t('chat.filesAssociated'),
    uploadFiles: t('common.upload'),
    agentSelection: {
      selectAgent: t('chat.agentSelection.selectAgent'),
      currentAgent: t('chat.agentSelection.currentAgent'),
      changeAgent: t('chat.agentSelection.changeAgent'),
      agentDescription: t('chat.agentSelection.agentDescription')
    }
  }

  return (
    <ClientWrapper>
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <Header />
        
        <div className="h-[calc(100vh-56px)] bg-background overflow-hidden">
          <ChatClientWrapper translations={chatTranslations} />
        </div>
      </div>
    </ClientWrapper>
  )
}
