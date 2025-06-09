// SlideIn.tsx - copy từ React Bits
import React, { JSX, useEffect, useState } from 'react';

type Direction = 'left' | 'right' | 'up' | 'down';

interface SlideInProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  direction?: Direction;
  delay?: number; // giây
  isVisible?: boolean; // Thêm prop để control animation
  as?: keyof JSX.IntrinsicElements;
  className?: string;
}

export const SlideIn: React.FC<SlideInProps> = ({
  children,
  direction = 'up',
  delay = 0,
  isVisible = true,
  as = 'div',
  className = '',
  ...rest
}) => {
  const [visible, setVisible] = useState(isVisible);
  const [shouldRender, setShouldRender] = useState(isVisible);
  const tag = as;

  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
      const timeout = setTimeout(() => setVisible(true), delay * 1000);
      return () => clearTimeout(timeout);
    } else {
      setVisible(false);
      const timeout = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timeout);
    }
  }, [delay, isVisible]);

  if (!shouldRender) return null;

  let translate = '';
  switch (direction) {
    case 'left':
      translate = visible ? 'translate-x-0' : '-translate-x-8';
      break;
    case 'right':
      translate = visible ? 'translate-x-0' : 'translate-x-8';
      break;
    case 'down':
      translate = visible ? 'translate-y-0' : 'translate-y-8';
      break;
    default:
      translate = visible ? 'translate-y-0' : '-translate-y-8';
  }
  return React.createElement(
    tag,
    {
      className: `${className} transition-all duration-300 ease-out ${visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'} ${translate}`,
      ...rest,
    },
    children
  );
};

export default SlideIn;
