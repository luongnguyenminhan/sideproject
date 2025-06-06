import React, { Suspense } from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary from '@/utils/translation';
import { fetchSurveyQuestions } from '@/apis/questionApi';
import SurveyContainer from '@/components/survey/SurveyContainer';
import { TranslationProvider } from '@/contexts/TranslationContext';
import Header from '@/components/layout/header';
import ClientWrapper from '@/components/layout/client-wrapper';

async function SurveyContent() {
  const locale = await getCurrentLocale();
  const [dictionary, questions] = await Promise.all([
    getDictionary(locale),
    fetchSurveyQuestions(),
  ]);

  return (
    <ClientWrapper>
      <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <Header />
        
        <div className="h-[calc(100vh-56px)] bg-background">
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <div className="h-full overflow-y-auto">
              <div className="container mx-auto px-4 py-4 md:py-8 min-h-full flex items-center">
                <SurveyContainer questions={questions} />
              </div>
            </div>
          </TranslationProvider>
        </div>
      </div>
    </ClientWrapper>
  );
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center space-x-2 bg-[color:var(--muted)] px-4 py-2 rounded-full text-sm font-medium mb-4 animate-pulse">
            <div className="w-4 h-4 bg-[color:var(--muted-foreground)] rounded"></div>
            <div className="w-20 h-4 bg-[color:var(--muted-foreground)] rounded"></div>
          </div>
          <div className="w-64 h-12 bg-[color:var(--muted)] rounded mx-auto mb-4 animate-pulse"></div>
          <div className="w-96 h-6 bg-[color:var(--muted)] rounded mx-auto animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}

export default async function DemoPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <SurveyContent />
    </Suspense>
  );
}
