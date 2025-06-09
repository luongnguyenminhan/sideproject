import React from 'react';
import { FacebookPostCarousel } from '@/components/facebook';
import { ScrollReveal, FallingText } from '@/components/animations';
import type { FacebookPageInfo } from '@/types/facebook.type';

interface FacebookPostsSectionProps {
  postInformation: FacebookPageInfo | null;
  locale: string;
  postsTitle: string;
  profilePictureUrl?: string;
}

export default function FacebookPostsSection({
  postInformation,
  locale,
  postsTitle,
  profilePictureUrl,
}: FacebookPostsSectionProps) {
  return (
    <ScrollReveal direction="up" delay={0.4}>
      <section className="py-6 sm:py-8 lg:py-12 px-4 sm:px-6 lg:px-8 xl:px-12">
        <div className="w-full max-w-[95%] sm:max-w-[90%] lg:max-w-[85%] mx-auto">
          <FallingText variant="bounce" delay={0.2}>
            <div className="text-center mb-8 sm:mb-10 lg:mb-12">
              <div className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-3 sm:mb-4 leading-tight">
                {postsTitle}
              </div>
            </div>
          </FallingText>          
          <FacebookPostCarousel 
            limit={9} 
            autoPlay={true} 
            truncateMessage={true}
            maxMessageLength={80}
            pageInfo={postInformation}
            locale={locale}
            profilePictureUrl={profilePictureUrl}
          />
        </div>
      </section>
    </ScrollReveal>
  );
}
