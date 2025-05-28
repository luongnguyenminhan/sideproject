'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface CarouselProps {
  children: React.ReactNode[];
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showDots?: boolean;
  showArrows?: boolean;
  itemsPerView?: number;
  className?: string;
  endlessScroll?: boolean;
  scrollSpeed?: number;
}

const Carousel: React.FC<CarouselProps> = ({
  children,
  autoPlay = false,
  autoPlayInterval = 10000,
  showDots = false,
  showArrows = false,
  itemsPerView = 1,
  className = '',
  endlessScroll = false,
  scrollSpeed = 1,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [translateX, setTranslateX] = useState(0);
  const totalItems = children.length;
  const maxIndex = Math.max(0, Math.floor(totalItems / itemsPerView) - 1);
  // Endless scroll effect
  useEffect(() => {
    if (!endlessScroll) return;

    const interval = setInterval(() => {
      setTranslateX((prev) => prev - scrollSpeed);
    }, 50);

    return () => clearInterval(interval);
  }, [endlessScroll, scrollSpeed]);

  // Reset position when items have scrolled out of view
  useEffect(() => {
    if (!endlessScroll) return;

    const itemWidth = 100 / totalItems;
    const resetPoint = -(itemWidth * totalItems);
    
    if (translateX <= resetPoint) {
      setTranslateX(0);
    }
  }, [translateX, endlessScroll, totalItems]);

  // Regular autoplay (when not endless scroll)
  useEffect(() => {
    if (endlessScroll || !autoPlay || totalItems <= itemsPerView) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex >= maxIndex ? 0 : prevIndex + 1));
    }, autoPlayInterval);

    return () => clearInterval(interval);
  }, [autoPlay, autoPlayInterval, maxIndex, totalItems, itemsPerView, endlessScroll]);

  const goToSlide = (index: number) => {
    setCurrentIndex(Math.max(0, Math.min(index, maxIndex)));
  };

  const goToPrevious = () => {
    setCurrentIndex((prevIndex) => (prevIndex <= 0 ? maxIndex : prevIndex - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prevIndex) => (prevIndex >= maxIndex ? 0 : prevIndex + 1));
  };

  if (totalItems === 0) {
    return null;
  }

  return (
    <div className={`relative w-full ${className}`}>
      {/* Carousel Container */}
      <div className="relative overflow-hidden">
        <div
          className="flex transition-transform duration-300 ease-in-out"
          style={{
            transform: endlessScroll 
              ? `translateX(${translateX}%)`
              : `translateX(-${(currentIndex * 100) / itemsPerView}%)`,
            width: `${(totalItems * 100) / itemsPerView}%`,
          }}
        >
          {children.map((child, index) => (
            <div
              key={index}
              className="flex-shrink-0"
              style={{ width: `${100 / totalItems}%` }}
            >
              <div className="px-2">{child}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Arrows */}
      {showArrows && totalItems > itemsPerView && !endlessScroll && (
        <>
          <button
            onClick={goToPrevious}
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white rounded-full p-2 shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-600"
            aria-label="Previous slide"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={goToNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white rounded-full p-2 shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-600"
            aria-label="Next slide"
          >
            <ChevronRight size={20} />
          </button>
        </>
      )}

      {/* Dots Indicator */}
      {showDots && totalItems > itemsPerView && !endlessScroll && (
        <div className="flex justify-center space-x-2 mt-4">
          {Array.from({ length: Math.ceil(totalItems / itemsPerView) }).map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`w-3 h-3 rounded-full transition-all duration-200 ${
                index === currentIndex
                  ? 'bg-blue-500 dark:bg-blue-400'
                  : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Carousel;
