// FadeIn.tsx - copy từ React Bits
import React, { JSX, useEffect, useState } from 'react';

interface FadeInProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  delay?: number; // giây
  as?: keyof JSX.IntrinsicElements;
  className?: string;
}

export const FadeIn: React.FC<FadeInProps> = ({
  children,
  delay = 0,
  as = 'div',
  className = '',
  ...rest
}) => {
  const [visible, setVisible] = useState(false);
  const tag = as;
  useEffect(() => {
    const timeout = setTimeout(() => setVisible(true), delay * 1000);
    return () => clearTimeout(timeout);
  }, [delay]);
  return React.createElement(
    tag,
    {
      className: `${className} transition-opacity duration-700 ${visible ? 'opacity-100' : 'opacity-0'}`,
      ...rest,
    },
    children
  );
};

export default FadeIn;
