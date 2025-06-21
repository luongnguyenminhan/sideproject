import React from 'react';
import { FallingText } from '@/components/animations';
import type { UserResponse } from '@/types/auth.type';
import HeroButtons from '@/components/home/heroButtons';
import { TranslationProvider } from '@/contexts/TranslationContext';

interface HeroSectionProps {
  user: UserResponse | null;
  isAuthenticated: boolean;
  welcomeTitle: string;
  description: string;
  getStartedText: string;
  learnMoreText: string;
  locale: string;
  dictionary: Record<string, unknown>;
}

export default function HeroSection({
  user,
  isAuthenticated,
  welcomeTitle,
  description,
  getStartedText,
  learnMoreText,
  locale,
  dictionary
}: HeroSectionProps) {
  return (
    <section className="relative py-32 px-6 sm:px-8 lg:px-12">
      <div className="max-w-6xl mx-auto text-center space-y-12">
        {/* Main Title with Shiny Effect */}
        <FallingText variant="bounce" delay={0.2} duration={1.5}>
          <div 
            className="text-5xl md:text-7xl lg:text-8xl font-bold bg-clip-text text-transparent leading-tight bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-8"
          >
            {isAuthenticated 
              ? welcomeTitle.replace('{name}', user?.name || user?.username || '')
              : welcomeTitle
            }
          </div>
        </FallingText>

        {/* Subtitle */}
        <FallingText variant="fade" delay={0.6} duration={1.2}>
          <div className="text-xl md:text-2xl lg:text-3xl text-[color:var(--muted-foreground)] max-w-4xl mx-auto leading-relaxed">
            {description}
          </div>
        </FallingText>        {/* Call to Action Buttons */}
        <FallingText variant="scale" delay={1} duration={1}>
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <HeroButtons
              isAuthenticated={isAuthenticated}
              getStartedText={getStartedText}
              learnMoreText={learnMoreText}
              locale={locale}
            />
          </TranslationProvider>
        </FallingText>
      </div>
    </section>
  );
}
