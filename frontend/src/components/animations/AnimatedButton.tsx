// AnimatedButton.tsx - copy từ React Bits
import React from 'react';

interface AnimatedButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  animation?: 'scale' | 'rotate' | 'pulse' | 'shake';
  className?: string;
}

export const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  animation = 'scale',
  className = '',
  children,
  ...rest
}) => {
  let animClass = '';
  switch (animation) {
    case 'scale':
      animClass = 'transition-transform duration-200 hover:scale-110';
      break;
    case 'rotate':
      animClass = 'transition-transform duration-300 hover:rotate-12';
      break;
    case 'pulse':
      animClass = 'animate-pulse';
      break;
    case 'shake':
      animClass = 'hover:animate-shake';
      break;
    default:
      animClass = '';
  }
  return (
    <button className={`${className} ${animClass}`} {...rest}>
      {children}
    </button>
  );
};

export default AnimatedButton;
