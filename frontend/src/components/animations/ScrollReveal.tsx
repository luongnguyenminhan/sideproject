'use client';

import { motion, useInView } from 'framer-motion';
import { ReactNode, useRef } from 'react';

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  direction?: 'up' | 'down' | 'left' | 'right' | 'scale' | 'fade';
  delay?: number;
  duration?: number;
  distance?: number;
  once?: boolean;
}


export default function ScrollReveal({ 
  children, 
  className = "",
  direction = 'up',
  delay = 0,
  duration = 0.8,
  distance = 60,
  once = true
}: ScrollRevealProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { 
    once,
    margin: "-10% 0px -10% 0px"
  });

  // Create custom variant based on direction and distance
  const customVariant = {
    hidden: {
      opacity: 0,
      ...(direction === 'up' && { y: distance }),
      ...(direction === 'down' && { y: -distance }),
      ...(direction === 'left' && { x: distance }),
      ...(direction === 'right' && { x: -distance }),
      ...(direction === 'scale' && { scale: 0.8 }),
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
      scale: 1
    }
  };

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={customVariant}
      transition={{
        duration,
        delay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
} 