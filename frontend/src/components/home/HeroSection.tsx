import React from 'react';
import { FallingText, MagnetButton } from '@/components/animations';
import type { UserResponse } from '@/types/auth.type';

interface HeroSectionProps {
  user: UserResponse | null;
  isAuthenticated: boolean;
  welcomeTitle: string;
  description: string;
  getStartedText: string;
  learnMoreText: string;
}

export default function HeroSection({
  user,
  isAuthenticated,
  welcomeTitle,
  description,
  getStartedText,
  learnMoreText
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
        </FallingText>

        {/* Call to Action Buttons */}
        <FallingText variant="scale" delay={1} duration={1}>
          <div className="flex flex-col sm:flex-row gap-8 justify-center mt-16">
            <MagnetButton magnetStrength={0.8}>
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] rounded-xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity duration-300"></div>
                <button className="relative px-12 py-4 text-lg text-[color:var(--primary-foreground)] font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-[var(--button-hover-shadow)] transform hover:-translate-y-2 bg-gradient-to-br from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:from-blue-700 hover:to-blue-900 border border-white/20">
                  {getStartedText}
                </button>
              </div>
            </MagnetButton>
            
            <MagnetButton magnetStrength={0.5}>
              <div className="group relative">
                <div className="absolute inset-0 bg-[color:var(--card)] rounded-xl blur-sm opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
                <button className="relative px-12 py-4 text-lg bg-[color:var(--card)] hover:bg-[color:var(--muted)] text-[color:var(--card-foreground)] font-semibold rounded-xl border-2 border-[color:var(--border)] transition-all duration-300 hover:border-[color:var(--ring)] transform hover:-translate-y-2 backdrop-blur-sm">
                  {learnMoreText}
                </button>
              </div>
            </MagnetButton>
          </div>
        </FallingText>
      </div>
    </section>
  );
}
