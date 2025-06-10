import React from 'react';
import AboutUsSection from '@/components/about-us/AboutUsSection';
import { ScrollReveal } from '@/components/animations';
import type { FacebookPageInfo } from '@/types/facebook.type';

interface AboutUsSectionWrapperProps {
  postInformation: FacebookPageInfo | null;
}

export default function AboutUsSectionWrapper({ postInformation }: AboutUsSectionWrapperProps) {
  if (!postInformation) {
    return null;
  }

  return (
    <ScrollReveal direction="up" delay={0.2}>
      <section className="py-8 px-6 sm:px-8 lg:px-12">
        <div className="max-w-[85%] mx-auto">
          <AboutUsSection pageInfo={postInformation} />
        </div>
      </section>
    </ScrollReveal>
  );
}
