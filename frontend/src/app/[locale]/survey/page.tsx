import React, { Suspense } from 'react';
import { getDictionary } from '@/utils/translation';
import { fetchSurveyQuestions } from '@/apis/questionApi';
import { SurveyClientWrapper } from '@/components/survey/SurveyClientWrapper';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { Locale } from '@/i18n.config';
import Header from '@/components/layout/header';
import { getCurrentLocale } from '@/utils/getCurrentLocale';


async function SurveyContent({ locale }: { locale: Locale }) {
  try {
    // Fetch data server-side với Promise.all để tối ưu performance
    const [dictionary, questions] = await Promise.all([
      getDictionary(locale),
      fetchSurveyQuestions(),
    ]);

    return (
      <>
        <Header />
        <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
          <div className="container mx-auto px-4 py-8">
            <TranslationProvider dictionary={dictionary} locale={locale}>
              <div className="relative">
                {/* Background decorative elements */}
                <div className="absolute -top-10 -left-10 w-32 h-32 bg-[color:var(--feature-purple)] rounded-full blur-3xl opacity-10"></div>
                <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-[color:var(--feature-blue)] rounded-full blur-3xl opacity-10"></div>
                
                <SurveyClientWrapper questions={questions} />
              </div>
            </TranslationProvider>

            {/* Footer Section */}
            <div className="text-center mt-16 pt-8 border-t border-[color:var(--border)]">
              <p className="text-[color:var(--muted-foreground)] text-sm">
                Your responses are secure and confidential
              </p>
              <div className="flex justify-center items-center space-x-4 mt-4">
                <div className="flex items-center space-x-2 text-[color:var(--muted-foreground)] text-xs">
                  <span className="w-2 h-2 bg-[color:var(--feature-green)] rounded-full"></span>
                  <span>Secure</span>
                </div>
                <div className="flex items-center space-x-2 text-[color:var(--muted-foreground)] text-xs">
                  <span className="w-2 h-2 bg-[color:var(--feature-blue)] rounded-full"></span>
                  <span>Encrypted</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  } catch (error) {
    console.error('Failed to load survey data:', error);
    return <SurveyErrorFallback locale={locale} />;
  }
}

function SurveyErrorFallback({ locale }: { locale: Locale }) {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-[color:var(--foreground)] mb-4">
            Unable to Load Survey
          </h1>
          <p className="text-[color:var(--muted-foreground)] mb-8 max-w-md">
            We encountered an error while loading the survey. Please try again later.
          </p>
          <a 
            href={`/${locale}`}
            className="inline-flex items-center px-6 py-3 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] rounded-lg hover:bg-[color:var(--primary)]/90 transition-colors"
          >
            Back to Home
          </a>
        </div>
      </div>
    </>
  );
}

function SurveyLoadingSkeleton() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <div className="container mx-auto px-4 py-8">
          {/* Hero skeleton */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center space-x-2 bg-[color:var(--muted)] px-6 py-3 rounded-full mb-6 animate-pulse">
              <div className="w-4 h-4 bg-[color:var(--muted-foreground)] rounded"></div>
              <div className="w-16 h-4 bg-[color:var(--muted-foreground)] rounded"></div>
            </div>
            
            <div className="w-80 h-16 bg-[color:var(--muted)] rounded-xl mx-auto mb-6 animate-pulse"></div>
            <div className="w-96 h-6 bg-[color:var(--muted)] rounded mx-auto animate-pulse"></div>
          </div>

          {/* Survey skeleton */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-[color:var(--background)] rounded-3xl shadow-2xl border border-[color:var(--border)] p-8">
              {/* Progress bar skeleton */}
              <div className="w-full h-3 bg-[color:var(--muted)] rounded-full mb-8 animate-pulse"></div>
              
              {/* Content skeleton */}
              <div className="space-y-6">
                <div className="w-3/4 h-8 bg-[color:var(--muted)] rounded animate-pulse"></div>
                <div className="w-1/2 h-6 bg-[color:var(--muted)] rounded animate-pulse"></div>
                
                {/* Options skeleton */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-24 bg-[color:var(--muted)] rounded-xl animate-pulse"></div>
                  ))}
                </div>
                
                {/* Button skeleton */}
                <div className="flex justify-between items-center mt-8">
                  <div className="w-20 h-10 bg-[color:var(--muted)] rounded animate-pulse"></div>
                  <div className="w-24 h-10 bg-[color:var(--muted)] rounded animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default async function SurveyPage() {
  const locale = await getCurrentLocale()
  
  return (
    <Suspense fallback={<SurveyLoadingSkeleton />}>
      <SurveyContent locale={locale} />
    </Suspense>
  );
} 