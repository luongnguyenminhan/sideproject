'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface ShinyTextProps {
  children: ReactNode;
  className?: string;
  shimmerWidth?: number;
  shimmerDuration?: number;
  delay?: number;
}

export default function ShinyText({ 
  children, 
  className = "",
  shimmerWidth = 100,
  shimmerDuration = 2,
  delay = 0
}: ShinyTextProps) {
  return (
    <motion.div
      className={`relative inline-block overflow-hidden ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay }}
    >
      {children}
      
      {/* Shimmer effect */}
      <motion.div
        className="absolute inset-0 -skew-x-12"
        style={{
          background: `linear-gradient(90deg, 
            transparent 0%, 
            rgba(255,255,255,0.4) 50%, 
            transparent 100%)`,
          width: `${shimmerWidth}%`,
        }}
        initial={{ x: '-100%' }}
        animate={{ x: '100%' }}
        transition={{
          duration: shimmerDuration,
          repeat: Infinity,
          repeatDelay: 3,
          ease: "easeInOut",
          delay
        }}
      />
    </motion.div>
  );
} 