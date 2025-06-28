import React from 'react';
import { ScrollReveal, FallingText } from '@/components/animations';
import { LiquidGlass } from '@/components/ui';

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
                <LiquidGlass 
                  variant="card" 
                  blur="lg" 
                  rounded="2xl" 
                  shadow="xl" 
                  hover={true}
                  className="p-12 h-full group relative"
                >
                  <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-${feature.color}-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000`}></div>
                  
                  <div className="relative z-10">
                    <div className={`w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-gradient-to-br from-${feature.color}-500/20 to-${feature.color}-600/30 backdrop-blur-sm border border-${feature.color}-400/20 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300`}>
                      <div className={`text-${feature.color}-600 dark:text-${feature.color}-400`}>
                        {feature.icon}
                      </div>
                    </div>
                    <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-6">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300 leading-relaxed text-lg mb-6">
                      {feature.description}
                    </p>
                    <div className="space-y-3">
                      {feature.features.map((item, itemIndex) => (
                        <div key={itemIndex} className="flex items-center space-x-3">
                          <div className={`w-2 h-2 bg-${feature.color}-500 rounded-full shadow-lg shadow-${feature.color}-500/30`}></div>
                          <span className="text-gray-600 dark:text-gray-300">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </LiquidGlass>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>
    </ScrollReveal>
  );
}
