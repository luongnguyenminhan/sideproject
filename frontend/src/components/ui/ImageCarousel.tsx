'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { 
  FallingText, 
  MagneticCard, 
  ScrollReveal,
} from '@/components/animations';

interface ImageCarouselProps {
  images: string[];
  title: string;
  subtitle: string;
  description: string;
  nextText: string;
  prevText: string;
  currentText: string;
  autoPlay?: boolean;
  interval?: number;
}

const ImageCarousel: React.FC<ImageCarouselProps> = ({
  images,
  title,
  subtitle,
  description,
  nextText,
  prevText,
  currentText,
  autoPlay = true,
  interval = 4000
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setCurrentIndex((prevIndex) => 
        prevIndex === images.length - 1 ? 0 : prevIndex + 1
      );
    }, interval);

    return () => clearInterval(timer);
  }, [isPlaying, images.length, interval]);

  const goToNext = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === images.length - 1 ? 0 : prevIndex + 1
    );
  };

  const goToPrev = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? images.length - 1 : prevIndex - 1
    );
  };

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  if (!images || images.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-[color:var(--muted-foreground)]">No images available</p>
      </div>
    );
  }

  return (
    <section className="py-20 px-6 sm:px-8 lg:px-12">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal direction="up" delay={0.1}>
          {/* Header */}
          <div className="text-center mb-16">
            <FallingText variant="bounce" delay={0.2}>
              <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-6">
                {title}
              </h2>
            </FallingText>
            
            <FallingText variant="fade" delay={0.4}>
              <p className="text-xl text-[color:var(--feature-blue-text)] font-semibold mb-4">
                {subtitle}
              </p>
            </FallingText>
            
            <FallingText variant="slide" delay={0.6}>
              <p className="text-lg text-[color:var(--muted-foreground)] max-w-2xl mx-auto">
                {description}
              </p>
            </FallingText>
          </div>

          {/* Carousel Container */}
          <MagneticCard strength={8}>
            <div className="bg-[color:var(--card)] rounded-3xl p-8 lg:p-12 shadow-[var(--card-hover-shadow)] border border-[color:var(--border)] relative overflow-hidden group">
              
              {/* Animated Background */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
              
              <div className="relative z-10">
                {/* Image Display */}
                <div className="relative h-80 md:h-96 lg:h-[500px] mb-8 rounded-2xl overflow-hidden bg-[color:var(--muted)] group/image">
                  <div className="absolute inset-0 bg-gradient-to-br from-[color:var(--feature-blue)]/10 to-[color:var(--feature-purple)]/10 opacity-0 group-hover/image:opacity-100 transition-opacity duration-500"></div>
                  
                  {images.map((image, index) => (
                    <div
                      key={index}
                      className={`absolute inset-0 transition-all duration-700 ease-in-out ${
                        index === currentIndex 
                          ? 'opacity-100 scale-100 translate-x-0' 
                          : index < currentIndex 
                            ? 'opacity-0 scale-95 -translate-x-full' 
                            : 'opacity-0 scale-95 translate-x-full'
                      }`}
                    >
                      <Image
                        src={image}
                        alt={`Gallery image ${index + 1}`}
                        fill
                        className="object-contain transition-transform duration-700 group-hover/image:scale-105"
                        priority={index === 0}
                      />
                    </div>
                  ))}
                  
                  {/* Image Overlay Info */}
                  <div className="absolute bottom-4 left-4 bg-[color:var(--card)]/90 backdrop-blur-sm rounded-lg px-4 py-2 border border-[color:var(--border)]">
                    <p className="text-sm text-[color:var(--card-foreground)] font-medium">
                      {currentText} {currentIndex + 1} / {images.length}
                    </p>
                  </div>
                </div>

                {/* Navigation Controls */}
                <div className="flex items-center justify-between mb-8">
                  {/* Previous Button */}
                  <MagneticCard strength={15}>
                    <button
                      onClick={goToPrev}
                      className="group relative px-6 py-3 bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] text-white rounded-xl hover:scale-110 transition-all duration-300 shadow-lg hover:shadow-[var(--card-hover-shadow)]"
                    >
                      <div className="relative z-10 flex items-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        <span className="font-semibold">{prevText}</span>
                      </div>
                    </button>
                  </MagneticCard>

                  {/* Play/Pause Button */}
                  <MagneticCard strength={10}>
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="group relative p-3 bg-[color:var(--muted)] hover:bg-[color:var(--accent)] rounded-full transition-all duration-300 border border-[color:var(--border)] hover:border-[color:var(--ring)]"
                    >
                      {isPlaying ? (
                        <svg className="w-6 h-6 text-[color:var(--card-foreground)]" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                        </svg>
                      ) : (
                        <svg className="w-6 h-6 text-[color:var(--card-foreground)]" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                      )}
                    </button>
                  </MagneticCard>

                  {/* Next Button */}
                  <MagneticCard strength={15}>
                    <button
                      onClick={goToNext}
                      className="group relative px-6 py-3 bg-gradient-to-r from-[color:var(--feature-purple)] to-[color:var(--feature-blue)] text-white rounded-xl hover:scale-110 transition-all duration-300 shadow-lg hover:shadow-[var(--card-hover-shadow)]"
                    >
                      <div className="relative z-10 flex items-center space-x-2">
                        <span className="font-semibold">{nextText}</span>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </button>
                  </MagneticCard>
                </div>

                {/* Dot Indicators */}
                <div className="flex justify-center space-x-3">
                  {images.map((_, index) => (
                    <MagneticCard key={index} strength={5}>
                      <button
                        onClick={() => goToSlide(index)}
                        className={`w-3 h-3 rounded-full transition-all duration-300 ${
                          index === currentIndex
                            ? 'bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] scale-125'
                            : 'bg-[color:var(--muted-foreground)]/50 hover:bg-[color:var(--muted-foreground)]'
                        }`}
                      />
                    </MagneticCard>
                  ))}
                </div>
              </div>
            </div>
          </MagneticCard>
        </ScrollReveal>
      </div>
    </section>
  );
};

export default ImageCarousel; 