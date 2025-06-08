import React from 'react';

export interface FeatureData {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  colorText: string;
  features: string[];
}

export const createFeaturesData = (t: (key: string) => string): FeatureData[] => [
  {
    title: t('home.features.fastPerformance.title'),
    description: t('home.features.fastPerformance.description'),
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: '--feature-blue',
    colorText: '--feature-blue-text',
    features: [
      t('home.features.fastPerformance.features.optimizedPerformance'),
      t('home.features.fastPerformance.features.lightningFastLoading'),
      t('home.features.fastPerformance.features.seamlessUserExperience')
    ]
  },
  {
    title: t('home.features.globalReady.title'),
    description: t('home.features.globalReady.description'),
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: '--feature-green',
    colorText: '--feature-green-text',
    features: [
      t('home.features.globalReady.features.multiLanguageSupport'),
      t('home.features.globalReady.features.globalAccessibility'),
      t('home.features.globalReady.features.culturalAdaptation')
    ]
  },
  {
    title: t('home.features.modernStack.title'),
    description: t('home.features.modernStack.description'),
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    color: '--feature-purple',
    colorText: '--feature-purple-text',
    features: [
      t('home.features.modernStack.features.nextjsReact'),
      t('home.features.modernStack.features.typescriptSupport'),
      t('home.features.modernStack.features.modernDevelopmentTools')
    ]
  },
  {
    title: t('home.features.darkMode.title'),
    description: t('home.features.darkMode.description'),
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    ),
    color: '--feature-yellow',
    colorText: '--feature-yellow-text',
    features: [
      t('home.features.darkMode.features.darkLightThemes'),
      t('home.features.darkMode.features.eyeFriendlyDesign'),
      t('home.features.darkMode.features.automaticSwitching')
    ]
  }
];
