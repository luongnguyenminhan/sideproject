import ServerComponent from "@/components/server-components"
import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"
import React from "react"
import Header from '@/components/layout/header';

export default async function Home() {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  return (
    <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      <Header />
      <main className="flex flex-col items-center justify-center min-h-screen px-6 sm:px-8 lg:px-12 pt-24 pb-20">
        <div className="max-w-6xl mx-auto text-center space-y-12">
          <div className="space-y-6">            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold bg-clip-text text-transparent leading-tight bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
              {t('home.title')}
            </h1>
            <p className="text-xl md:text-2xl lg:text-3xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto leading-relaxed">
              {t('home.description')}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6 mt-16">            
            <div 
              className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-blue-text)]"
            >              
            <div 
                className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-blue)]"
              >
                <svg 
                  className="w-8 h-8 text-[color:var(--feature-blue-text)]"
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('home.features.fastPerformance.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('home.features.fastPerformance.description')}
              </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-green-text)]"
            >
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-green)]"
              >
                <svg 
                  className="w-8 h-8 text-[color:var(--feature-green-text)]"
                  fill="none"
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('home.features.globalReady.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('home.features.globalReady.description')}
              </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-purple-text)]">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-purple)]">
                <svg 
                  className="w-8 h-8 text-[color:var(--feature-purple-text)]"
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('home.features.modernStack.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('home.features.modernStack.description')}
              </p>
            </div>            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-yellow-text)]">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-yellow)]">
                <svg 
                  className="w-8 h-8 text-[color:var(--feature-yellow-text)]"
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('home.features.darkMode.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('home.features.darkMode.description')}
              </p>
            </div>
          </div>

          <div className="mt-20 bg-white dark:bg-gray-800 rounded-3xl !p-10 lg:!p-12 shadow-2xl border border-gray-200 dark:border-gray-700">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-8">
              {t('home.serverComponentDemo')}
            </h2>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-2xl !p-8 border-2 border-dashed border-gray-300 dark:border-gray-600">
              <ServerComponent />
            </div>
          </div>

          
          <div className="mt-16 space-y-8">
            <div className="flex flex-col sm:flex-row gap-6 justify-center">              <button className="px-10 py-4 text-lg text-white font-semibold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 bg-gradient-to-br from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:from-blue-700 hover:to-blue-900">
                {t('home.getStarted')}
              </button>
              <button className="px-10 py-4 text-lg bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-semibold rounded-xl border-2 border-gray-300 dark:border-gray-600 transition-all duration-200 hover:border-gray-400 dark:hover:border-gray-500 transform hover:-translate-y-1">
                {t('home.learnMore')}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>

  )
}