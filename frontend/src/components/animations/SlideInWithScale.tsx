// SlideInWithScale.tsx - Enhanced animation cho chat bubble
import React, { useEffect, useState } from 'react';

interface SlideInWithScaleProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  isVisible: boolean;
  direction?: 'up' | 'down' | 'left' | 'right';
  className?: string;
}

export const SlideInWithScale: React.FC<SlideInWithScaleProps> = ({
  children,
  isVisible,
  direction = 'up',
  className = '',
  ...rest
}) => {
  const [shouldRender, setShouldRender] = useState(isVisible);

  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
    } else {
      // Delay unmount to allow exit animation
      const timer = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  if (!shouldRender) return null;

  let translateClass = '';
  switch (direction) {
    case 'up':
      translateClass = isVisible ? 'translate-y-0' : 'translate-y-8';
      break;
    case 'down':
      translateClass = isVisible ? 'translate-y-0' : '-translate-y-8';
      break;
    case 'left':
      translateClass = isVisible ? 'translate-x-0' : 'translate-x-8';
      break;
    case 'right':
      translateClass = isVisible ? 'translate-x-0' : '-translate-x-8';
      break;
  }

  return (
    <div
      className={`${className} transition-all duration-300 ease-out ${
        isVisible 
          ? 'opacity-100 scale-100 translate-y-0' 
          : 'opacity-0 scale-95 translate-y-8'
      } ${translateClass}`}
      {...rest}
    >
      {children}
    </div>
  );
};

export default SlideInWithScale;