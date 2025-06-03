import React from 'react'
import { withAuth } from '@/hoc/withAuth'
import type { UserResponse } from '@/types/auth.type'
import { getCurrentLocale } from '@/utils/getCurrentLocale'
import { getDictionary, createTranslator } from '@/utils/translation'

interface HomePageProps {
  user: UserResponse;
}

async function HomePage({ user }: HomePageProps) {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
          {t('home.welcomeBack')}, {user.name || user.username}!
        </h1>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-200 dark:border-gray-700 transition-colors duration-200">
          <h2 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
            {t('home.userInformation')}
          </h2>
          <p className="text-gray-700 dark:text-gray-300">
            <strong>{t('home.email')}:</strong> {user.email}
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            <strong>{t('home.username')}:</strong> {user.username}
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            <strong>{t('home.confirmed')}:</strong> {user.confirmed ? t('common.yes') : t('common.no')}
          </p>
        </div>
      </div>
    </div>
  )
}

export default withAuth(HomePage);