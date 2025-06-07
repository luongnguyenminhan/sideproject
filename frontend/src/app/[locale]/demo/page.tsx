import React, { Suspense } from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { getDictionary } from '@/utils/translation';
import { fetchSurveyQuestions } from '@/apis/questionApi';
import SurveyContainer from '@/components/survey/SurveyContainer';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { Locale } from '@/i18n.config';
import Header from '@/components/layout/header';
import ClientWrapper from '@/components/layout/client-wrapper';

async function SurveyContent({ locale }: { locale: Locale }) {
  try {
    // Fetch data server-side với Promise.all để tối ưu performance
    const [dictionary, questions] = await Promise.all([
      getDictionary(locale),
      fetchSurveyQuestions(),
    ]);

    return (
      <ClientWrapper>
        <div className="relative">
          <Header />
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <SurveyContainer questions={questions} />
          </TranslationProvider>
        </div>
      </ClientWrapper>
    );
  } catch (error) {
    console.error('Failed to load survey data:', error);
    return <DemoErrorFallback locale={locale} />;
  }
}

function DemoErrorFallback({ locale }: { locale: Locale }) {
  return (
    <ClientWrapper>
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] flex items-center justify-center">
        <Header />
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-[color:var(--foreground)] mb-4">
            Unable to Load Demo
          </h1>
          <p className="text-[color:var(--muted-foreground)] mb-8 max-w-md">
            We encountered an error while loading the demo. Please try again later.
          </p>
          <a 
            href={`/${locale}`}
            className="inline-flex items-center px-6 py-3 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] rounded-lg hover:bg-[color:var(--primary)]/90 transition-colors"
          >
            Back to Home
          </a>
        </div>
      </div>
    </ClientWrapper>
  );
}

function LoadingSkeleton() {
  return (
    <ClientWrapper>
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <Header />
        <div className="h-[calc(100vh-56px)] bg-background">
          <div className="h-full overflow-y-auto">
            <div className="container mx-auto px-4 py-4 md:py-8 min-h-full flex items-center">
              {/* Demo skeleton */}
              <div className="max-w-4xl mx-auto w-full">
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
        </div>
      </div>
    </ClientWrapper>
  );
}

export default async function DemoPage() {
  const locale = await getCurrentLocale();
  
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <SurveyContent locale={locale} />
    </Suspense>
  );
}