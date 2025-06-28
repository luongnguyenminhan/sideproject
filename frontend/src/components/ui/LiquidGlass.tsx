import React from 'react';
import { cn } from '@/lib/utils';

interface LiquidGlassProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'subtle' | 'strong' | 'card' | 'nav';
  blur?: 'sm' | 'md' | 'lg' | 'xl';
  opacity?: number;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl';
  border?: boolean;
  shadow?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  hover?: boolean;
  as?: React.ElementType;
}

const LiquidGlass = React.forwardRef<HTMLDivElement, LiquidGlassProps>(({
  children,
  className,
  variant = 'default',
  blur = 'md',
  opacity = 0.1,
  rounded = 'xl',
  border = true,
  shadow = 'lg',
  hover = true,
  as: Component = 'div',
  ...props
}, ref) => {
  const baseStyles = "relative overflow-hidden transition-all duration-300";
  
  const variantStyles = {
    default: "bg-white/10 dark:bg-white/5",
    subtle: "bg-white/5 dark:bg-white/[0.02]",
    strong: "bg-white/20 dark:bg-white/10", 
    card: "bg-white/8 dark:bg-white/[0.03]",
    nav: "bg-white/15 dark:bg-white/8"
  };

  const blurStyles = {
    sm: "backdrop-blur-sm",
    md: "backdrop-blur-md", 
    lg: "backdrop-blur-lg",
    xl: "backdrop-blur-xl"
  };

  const roundedStyles = {
    sm: "rounded-sm",
    md: "rounded-md",
    lg: "rounded-lg", 
    xl: "rounded-xl",
    '2xl': "rounded-2xl",
    '3xl': "rounded-3xl"
  };

  const shadowStyles = {
    sm: "shadow-sm",
    md: "shadow-md",
    lg: "shadow-lg shadow-black/5 dark:shadow-black/20",
    xl: "shadow-xl shadow-black/10 dark:shadow-black/30",
    '2xl': "shadow-2xl shadow-black/15 dark:shadow-black/40"
  };

  const borderStyles = border 
    ? "border border-white/20 dark:border-white/10" 
    : "";

  const hoverStyles = hover 
    ? "hover:bg-white/15 dark:hover:bg-white/8 hover:border-white/30 dark:hover:border-white/20 hover:shadow-xl hover:shadow-black/10 dark:hover:shadow-black/30" 
    : "";

  const combinedStyles = cn(
    baseStyles,
    variantStyles[variant],
    blurStyles[blur],
    roundedStyles[rounded], 
    shadowStyles[shadow],
    borderStyles,
    hoverStyles,
    className
  );

  return (
    <Component
      ref={ref}
      className={combinedStyles}
      style={{ 
        backgroundImage: `linear-gradient(135deg, rgba(255,255,255,${opacity}) 0%, rgba(255,255,255,${opacity * 0.5}) 100%)`,
        ...props.style 
      }}
      {...props}
    >
      {/* Subtle gradient overlay for extra glass effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.08] via-transparent to-transparent pointer-events-none" />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </Component>
  );
});

LiquidGlass.displayName = "LiquidGlass";

export default LiquidGlass;