import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"

export default async function ServerComponent() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)
  
  const currentTime = new Date().toLocaleString(locale === 'vi' ? 'vi-VN' : 'en-US')
  
  return (
    <div className="space-y-4 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
      <div className="text-center space-y-2">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('server.serverRendered')}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {t('server.currentTime')}: <span className="font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{currentTime}</span>
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-100 dark:border-gray-600">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            {t('server.locale')}
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-300 font-mono">
            {locale.toUpperCase()}
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-100 dark:border-gray-600">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Server Timestamp
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-300 font-mono">
            {Date.now()}
          </p>
        </div>
      </div>
      
      <div className="text-xs text-center text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-4">
        This component is rendered on the server at build time or request time
      </div>
    </div>
  )
}