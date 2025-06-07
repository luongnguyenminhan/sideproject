import React from 'react';
import ImageCarousel from '@/components/ui/ImageCarousel';

interface ImageCarouselSectionProps {
  images: string[];
  title: string;
  subtitle: string;
  description: string;
  nextText: string;
  prevText: string;
  currentText: string;
}

export default function ImageCarouselSection({
  images,
  title,
  subtitle,
  description,
  nextText,
  prevText,
  currentText
}: ImageCarouselSectionProps) {
  return (
    <ImageCarousel
      images={images}
      title={title}
      subtitle={subtitle}
      description={description}
      nextText={nextText}
      prevText={prevText}
      currentText={currentText}
      autoPlay={true}
      interval={5000}
    />
  );
}
