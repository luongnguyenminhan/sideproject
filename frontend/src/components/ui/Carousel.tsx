"use client";

import React, { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface CarouselProps {
  children: React.ReactNode[];
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showDots?: boolean;
  showArrows?: boolean;
  itemsPerView?:
    | {
        desktop?: number;
        mobile?: number;
      }
    | number;
  className?: string;
  endlessScroll?: boolean;
  scrollSpeed?: number;
  enableDrag?: boolean;
}

const useResponsive = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  return { isMobile };
};

const Carousel: React.FC<CarouselProps> = ({
  children,
  autoPlay = false,
  autoPlayInterval = 10000,
  showDots = false,
  showArrows = false,
  itemsPerView = { desktop: 3, mobile: 1 },
  className = "",
  endlessScroll = false,
  scrollSpeed = 1,
  enableDrag = true,
}) => {
  const { isMobile } = useResponsive();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [translateX, setTranslateX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState(0);

  const totalItems = children.length;

  const getCurrentItemsPerView = () => {
    if (typeof itemsPerView === "number") return itemsPerView;
    return isMobile ? itemsPerView.mobile || 1 : itemsPerView.desktop || 3;
  };

  const currentItemsPerView = getCurrentItemsPerView();
  const maxIndex = Math.max(0, totalItems - currentItemsPerView);

  // Ensure currentIndex stays within bounds
  useEffect(() => {
    if (currentIndex > maxIndex) {
      setCurrentIndex(maxIndex);
    }
  }, [currentItemsPerView, maxIndex, currentIndex]);

  // Endless scroll effect
  useEffect(() => {
    if (!endlessScroll) return;
    const interval = setInterval(() => {
      setTranslateX((prev) => prev - scrollSpeed);
    }, 50);
    return () => clearInterval(interval);
  }, [endlessScroll, scrollSpeed]);

  useEffect(() => {
    if (!endlessScroll) return;
    const itemWidth = 100 / totalItems;
    const resetPoint = -(itemWidth * totalItems);
    if (translateX <= resetPoint) {
      setTranslateX(0);
    }
  }, [translateX, endlessScroll, totalItems]);

  // Navigation
  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => Math.min(prev + 1, maxIndex));
  }, [maxIndex]);

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  const goToSlide = useCallback(
    (index: number) => {
      setCurrentIndex(Math.max(0, Math.min(index, maxIndex)));
    },
    [maxIndex]
  );

  // Autoplay
  useEffect(() => {
    if (endlessScroll || !autoPlay || totalItems <= currentItemsPerView) return;
    const interval = setInterval(goToNext, autoPlayInterval);
    return () => clearInterval(interval);
  }, [
    autoPlay,
    autoPlayInterval,
    goToNext,
    totalItems,
    currentItemsPerView,
    endlessScroll,
  ]);

  // Drag
  const handleDragStart = (clientX: number, clientY: number) => {
    if (!enableDrag || endlessScroll) return;
    setIsDragging(true);
    setDragStart({ x: clientX, y: clientY });
    setDragOffset(0);
  };

  const handleDragMove = useCallback(
    (clientX: number) => {
      if (!isDragging || !enableDrag || endlessScroll) return;
      const diffX = clientX - dragStart.x;
      const containerWidth = window.innerWidth;
      const itemWidth = containerWidth / currentItemsPerView;
      const dragPercentage = (diffX / itemWidth) * 100;
      setDragOffset(dragPercentage);
    },
    [isDragging, enableDrag, endlessScroll, dragStart.x, currentItemsPerView]
  );

  const handleDragEnd = useCallback(() => {
    if (!isDragging || !enableDrag || endlessScroll) return;
    setIsDragging(false);
    const threshold = 20;
    if (dragOffset > threshold) goToPrevious();
    else if (dragOffset < -threshold) goToNext();
    setDragOffset(0);
  }, [
    isDragging,
    enableDrag,
    endlessScroll,
    dragOffset,
    goToNext,
    goToPrevious,
  ]);

  // Mouse events
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(e.clientX, e.clientY);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    handleDragStart(touch.clientX, touch.clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    handleDragMove(touch.clientX);
  };

  const handleTouchEnd = () => {
    handleDragEnd();
  };

  useEffect(() => {
    if (!isDragging) return;
    const handleGlobalMouseMove = (e: MouseEvent) => handleDragMove(e.clientX);
    const handleGlobalMouseUp = () => handleDragEnd();
    document.addEventListener("mousemove", handleGlobalMouseMove);
    document.addEventListener("mouseup", handleGlobalMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleGlobalMouseMove);
      document.removeEventListener("mouseup", handleGlobalMouseUp);
    };
  }, [isDragging, handleDragMove, handleDragEnd]);

  if (totalItems === 0) return null;

  const numberOfDots = totalItems - currentItemsPerView + 1;

  return (
    <div className={`relative w-full ${className}`}>
      {/* Carousel Container */}
      <div className="relative overflow-hidden">
        <div
          className={`flex transition-transform duration-300 ease-in-out ${
            isDragging ? "cursor-grabbing" : "cursor-grab"
          }`}
          style={{
            transform: endlessScroll
              ? `translateX(${translateX}%)`
              : `translateX(${
                  -(currentIndex * (100 / totalItems)) + dragOffset
                }%)`,
            width: `${(totalItems * 100) / currentItemsPerView}%`,
            transitionDuration: isDragging ? "0ms" : "300ms",
          }}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
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
      {showArrows && totalItems > currentItemsPerView && !endlessScroll && (
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
      {showDots && totalItems > currentItemsPerView && !endlessScroll && (
        <div className="flex justify-center space-x-2 mt-4">
          {Array.from({ length: numberOfDots }).map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`w-3 h-3 rounded-full transition-all duration-200 ${
                index === currentIndex
                  ? "bg-blue-500 dark:bg-blue-400"
                  : "bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500"
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
