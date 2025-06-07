'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface FallingTextProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
  variant?: 'default' | 'smooth' | 'bounce' | 'slide' | 'fade' | 'scale';
}

const variants = {
  default: {
    initial: { 
      opacity: 0, 
      y: -20,
      filter: "blur(4px)"
    },
    animate: { 
      opacity: 1, 
      y: 0,
      filter: "blur(0px)"
    }
  },
  smooth: {
    initial: { 
      opacity: 0, 
      y: -30,
      scale: 0.95
    },
    animate: { 
      opacity: 1, 
      y: 0,
      scale: 1
    }
  },
  bounce: {
    initial: { 
      opacity: 0, 
      y: -40,
      scale: 0.8
    },
    animate: { 
      opacity: 1, 
      y: 0,
      scale: 1
    }
  },
  slide: {
    initial: { 
      opacity: 0, 
      x: -50,
      rotateX: 15
    },
    animate: { 
      opacity: 1, 
      x: 0,
      rotateX: 0
    }
  },
  fade: {
    initial: { 
      opacity: 0,
      filter: "blur(10px)"
    },
    animate: { 
      opacity: 1,
      filter: "blur(0px)"
    }
  },
  scale: {
    initial: { 
      opacity: 0, 
      scale: 0.5,
      rotate: -5
    },
    animate: { 
      opacity: 1, 
      scale: 1,
      rotate: 0
    }
  }
};

const easeTypes = {
  default: "easeOut",
  smooth: [0.25, 0.1, 0.25, 1],
  bounce: [0.68, -0.55, 0.265, 1.55],
  slide: [0.4, 0, 0.2, 1],
  fade: "easeInOut",
  scale: [0.175, 0.885, 0.32, 1.275]
};

export default function FallingText({ 
  children, 
  delay = 0, 
  duration = 0.8,
  className = "",
  variant = 'default'
}: FallingTextProps) {
  const selectedVariant = variants[variant];
  const ease = easeTypes[variant];

  return (
    <motion.div
      initial={selectedVariant.initial}
      animate={selectedVariant.animate}
      transition={{
        duration,
        delay,
        ease,
        type: variant === 'bounce' ? 'spring' : 'tween',
        stiffness: variant === 'bounce' ? 100 : undefined,
        damping: variant === 'bounce' ? 10 : undefined
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
} 