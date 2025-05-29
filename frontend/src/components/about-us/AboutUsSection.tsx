import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FacebookPageInfo } from '@/types/facebook.type';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';
import Image from 'next/image';

interface AboutUsSectionProps {
  pageInfo: FacebookPageInfo;
  locale?: string;
}

const AboutUsSection: React.FC<AboutUsSectionProps> = async ({ pageInfo }) => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  return (
    <section className="">
      <div className="max-w-screen mx-auto">

        {/* Facebook Page Info Card */}
        {pageInfo && (
          <div className="mb-12">
            <Card className="bg-[color:var(--card)] border-[color:var(--border)] shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-300">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
                  {t('aboutUs.title')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Page Profile Section */}
                <div className="flex flex-col md:flex-row items-center gap-6">
                  {/* Profile Picture */}
                  {pageInfo.picture?.data?.url && (
                    <div className="flex-shrink-0">
                      <Image
                        src={pageInfo.picture.data.url}
                        alt={pageInfo.name || 'Facebook Page'}
                        className="w-24 h-24 md:w-32 md:h-32 rounded-full border-4 border-[color:var(--feature-blue)] shadow-lg object-cover"
                        width={1920}
                        height={1920}
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
                        <span className='text-lg font-semibold text-[color:var(--feature-blue-text)]'>|</span>
                        {/* email */}
                        <span className="text-lg font-semibold text-[color:var(--feature-blue-text)]">Email: {pageInfo.emails?.[0]}</span>
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
                  
                  {/* Facebook Link */}
                  <div className="text-center p-4 bg-[color:var(--feature-blue)] rounded-xl group relative">
                    <a 
                      href="https://www.facebook.com/cangiuocschoolmedia" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="block hover:opacity-80 transition-opacity"
                    >
                      <svg className="w-8 h-8 text-[color:var(--feature-blue-text)] mx-auto" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                      </svg>
                    </a>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
                      Facebook
                    </div>
                  </div>

                  {/* Address */}
                  {pageInfo.single_line_address && (
                    <div className="text-center p-4 bg-[color:var(--feature-yellow)] rounded-xl group relative">
                      <svg className="w-8 h-8 text-[color:var(--feature-yellow-text)] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
                        {pageInfo.single_line_address}
                      </div>
                    </div>
                  )}

                  {/* Email */}
                  {pageInfo.emails && pageInfo.emails.length > 0 && (
                    <div className="text-center p-4 bg-[color:var(--feature-green)] rounded-xl group relative">
                      <svg className="w-8 h-8 text-[color:var(--feature-green-text)] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
                        {pageInfo.emails[0]}
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

      </div>
    </section>
  );
};

export default AboutUsSection;
