import React from 'react';
import { FallingText } from '@/components/animations';
import type { UserResponse } from '@/types/auth.type';
import HeroButtons from '@/components/home/heroButtons';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { LiquidGlass } from '@/components/ui';

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
        {/* Main Title with Glass Effect */}
        <FallingText variant="bounce" delay={0.2} duration={1.5}>
          <LiquidGlass 
            variant="subtle" 
            blur="md" 
            rounded="3xl" 
            className="p-8 inline-block"
            opacity={0.05}
          >
            <div 
              className="text-5xl md:text-7xl lg:text-8xl font-bold bg-clip-text text-transparent leading-tight bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 dark:from-blue-400 dark:via-purple-400 dark:to-pink-400 mb-8"
            >
              {isAuthenticated 
                ? welcomeTitle.replace('{name}', user?.name || user?.username || '')
                : welcomeTitle
              }
            </div>
          </LiquidGlass>
        </FallingText>

        {/* Subtitle with Glass Card */}
        <FallingText variant="fade" delay={0.6} duration={1.2}>
          <LiquidGlass 
            variant="card" 
            blur="lg" 
            rounded="2xl" 
            className="p-6 max-w-4xl mx-auto"
            opacity={0.08}
          >
            <div className="text-xl md:text-2xl lg:text-3xl text-[color:var(--text-primary)] leading-relaxed">
              {description}
            </div>
          </LiquidGlass>
        </FallingText>

        {/* Call to Action Buttons */}
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
