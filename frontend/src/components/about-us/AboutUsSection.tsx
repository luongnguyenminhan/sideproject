import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FacebookPageInfo } from '@/types/facebook.type';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';

interface AboutUsSectionProps {
  pageInfo: FacebookPageInfo;
  locale?: string;
}

const AboutUsSection: React.FC<AboutUsSectionProps> = async ({ pageInfo }) => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  return (
    <section className="py-16 px-6 sm:px-8 lg:px-12">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
            {t('aboutUs.title')}
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            {t('aboutUs.subtitle')}
          </p>
        </div>

        {/* Facebook Page Info Card */}
        {pageInfo && (
          <div className="mb-12">
            <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-2xl transition-all duration-300">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {t('aboutUs.social.pageInfo')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Page Profile Section */}
                <div className="flex flex-col md:flex-row items-center gap-6">
                  {/* Profile Picture */}
                  {pageInfo.picture?.data?.url && (
                    <div className="flex-shrink-0">
                      <img
                        src={pageInfo.picture.data.url}
                        alt={pageInfo.name || 'Facebook Page'}
                        className="w-24 h-24 md:w-32 md:h-32 rounded-full border-4 border-[color:var(--feature-blue)] shadow-lg object-cover"
                      />
                    </div>
                  )}
                  
                  {/* Page Information */}
                  <div className="flex-1 text-center md:text-left space-y-3">
                    {pageInfo.name && (
                      <h3 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
                        {pageInfo.name}
                      </h3>
                    )}
                    
                    {/* Followers Count */}
                    {pageInfo.followers_count !== undefined && (
                      <div className="flex items-center justify-center md:justify-start gap-2">
                        <svg className="w-5 h-5 text-[color:var(--feature-blue-text)]" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                        <span className="text-lg font-semibold text-[color:var(--feature-blue-text)]">
                          {pageInfo.followers_count?.toLocaleString()} {t('aboutUs.social.followers')}
                        </span>
                      </div>
                    )}
                    
                    {/* About Section */}
                    {pageInfo.about && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                          {t('aboutUs.social.about')}
                        </h4>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                          {pageInfo.about}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Additional Page Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-gray-200 dark:border-gray-600">
                  {pageInfo.posts?.data && (
                    <div className="text-center p-4 bg-[color:var(--feature-blue)] rounded-xl">
                      <div className="text-2xl font-bold text-[color:var(--feature-blue-text)]">
                        {pageInfo.posts.data.length}
                      </div>
                      <div className="text-sm text-[color:var(--feature-blue-text)] opacity-80">
                        {t('home.facebookPostsTitle')}
                      </div>
                    </div>
                  )}
                  
                  {pageInfo.website && (
                    <div className="text-center p-4 bg-[color:var(--feature-green)] rounded-xl">
                      <svg className="w-8 h-8 text-[color:var(--feature-green-text)] mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
                      </svg>
                      <div className="text-sm text-[color:var(--feature-green-text)]">
                        Website
                      </div>
                    </div>
                  )}
                  
                  {pageInfo.phone && (
                    <div className="text-center p-4 bg-[color:var(--feature-purple)] rounded-xl">
                      <svg className="w-8 h-8 text-[color:var(--feature-purple-text)] mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      <div className="text-sm text-[color:var(--feature-purple-text)]">
                        Contact
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Mission & Vision Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-blue-text)]">
            <CardContent className="p-8">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-blue)]">
                <svg className="w-8 h-8 text-[color:var(--feature-blue-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('aboutUs.mission.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('aboutUs.mission.description')}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-green-text)]">
            <CardContent className="p-8">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 bg-[color:var(--feature-green)]">
                <svg className="w-8 h-8 text-[color:var(--feature-green-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('aboutUs.vision.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {t('aboutUs.vision.description')}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Values Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-blue-text)]">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[color:var(--feature-blue)]">
                <svg className="w-6 h-6 text-[color:var(--feature-blue-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('aboutUs.values.innovation')}
              </h4>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                {t('aboutUs.values.innovationDesc')}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-green-text)]">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[color:var(--feature-green)]">
                <svg className="w-6 h-6 text-[color:var(--feature-green-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('aboutUs.values.quality')}
              </h4>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                {t('aboutUs.values.qualityDesc')}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-purple-text)]">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[color:var(--feature-purple)]">
                <svg className="w-6 h-6 text-[color:var(--feature-purple-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('aboutUs.values.collaboration')}
              </h4>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                {t('aboutUs.values.collaborationDesc')}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white dark:bg-gray-800 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-[color:var(--feature-yellow-text)]">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[color:var(--feature-yellow)]">
                <svg className="w-6 h-6 text-[color:var(--feature-yellow-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('aboutUs.values.integrity')}
              </h4>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                {t('aboutUs.values.integrityDesc')}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default AboutUsSection;
