import React, { Suspense } from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { getDictionary } from '@/utils/translation';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { Locale } from '@/i18n.config';
import Header from '@/components/layout/header';
import ClientWrapper from '@/components/layout/client-wrapper';
import CVTestComponent from '@/components/cv/CVTestComponent';

async function CVTestContent({ locale }: { locale: Locale }) {
  try {
    const dictionary = await getDictionary(locale);

    return (
      <ClientWrapper>
        <div className="relative">
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <CVTestComponent />
          </TranslationProvider>
        </div>
      </ClientWrapper>
    );
  } catch (error) {
    console.error('Failed to load CV test data:', error);
    return <CVTestErrorFallback locale={locale} />;
  }
}

function CVTestErrorFallback({ locale }: { locale: Locale }) {
  return (
    <ClientWrapper>
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] flex items-center justify-center">
        <Header />
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-[color:var(--foreground)] mb-4">
            Unable to Load CV Test
          </h1>
          <p className="text-[color:var(--muted-foreground)] mb-8 max-w-md">
            We encountered an error while loading the CV test page. Please try again later.
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
              <div className="max-w-4xl mx-auto w-full">
                <div className="bg-[color:var(--background)] rounded-3xl shadow-2xl border border-[color:var(--border)] p-8">
                  {/* Upload area skeleton */}
                  <div className="w-full h-48 bg-[color:var(--muted)] rounded-xl mb-8 animate-pulse"></div>
                  
                  {/* Options skeleton */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-16 bg-[color:var(--muted)] rounded-lg animate-pulse"></div>
                    ))}
                  </div>
                  
                  {/* Button skeleton */}
                  <div className="w-full h-12 bg-[color:var(--muted)] rounded-lg animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ClientWrapper>
  );
}

export default async function CVTestPage() {
  const locale = await getCurrentLocale();
  
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <CVTestContent locale={locale} />
    </Suspense>
  );
} 