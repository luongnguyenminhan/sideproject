import React from 'react';
import { ScrollReveal, FallingText, MagneticCard } from '@/components/animations';

interface Feature {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  colorText: string;
  features: string[];
}

interface FeaturesSectionProps {
  title: string;
  subtitle: string;
  features: Feature[];
}

export default function FeaturesSection({ title, subtitle, features }: FeaturesSectionProps) {
  return (
    <ScrollReveal direction="up" delay={0.2}>
      <section className="py-20 px-6 sm:px-8 lg:px-12">
        <div className="max-w-6xl mx-auto">
          <FallingText variant="bounce" className="text-center mb-20">
            <div 
              className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-6"
            >
              {title}
            </div>
            <p className="text-xl text-[color:var(--muted-foreground)] max-w-2xl mx-auto">
              {subtitle}
            </p>
          </FallingText>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {features.map((feature, index) => (
              <ScrollReveal key={index} direction="up" delay={0.1 * (index + 1)}>
                <MagneticCard strength={20}>
                  <div className={`bg-[color:var(--card)] rounded-2xl p-12 shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 border border-[color:var(--border)] hover:border-[color:var(${feature.colorText})] h-full group relative overflow-hidden`}>
                    <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-${feature.color}-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000`}></div>
                    
                    <div className="relative z-10">
                      <div className={`w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-[color:var(${feature.color})] group-hover:scale-110 group-hover:rotate-6 transition-all duration-300`}>
                        <div className={`text-[color:var(${feature.colorText})]`}>
                          {feature.icon}
                        </div>
                      </div>
                      <h3 className="text-2xl font-semibold text-[color:var(--card-foreground)] mb-6">
                        {feature.title}
                      </h3>
                      <p className="text-[color:var(--muted-foreground)] leading-relaxed text-lg mb-6">
                        {feature.description}
                      </p>
                      <div className="space-y-3">
                        {feature.features.map((item, itemIndex) => (
                          <div key={itemIndex} className="flex items-center space-x-3">
                            <div className={`w-2 h-2 bg-[color:var(${feature.color})] rounded-full`}></div>
                            <span className="text-[color:var(--muted-foreground)]">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </MagneticCard>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>
    </ScrollReveal>
  );
}
