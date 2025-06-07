'use client';

import { motion } from 'framer-motion';

interface GradientOrbProps {
  size?: number;
  className?: string;
  color1?: string;
  color2?: string;
  blur?: number;
  duration?: number;
  delay?: number;
}

export default function GradientOrb({ 
  size = 200, 
  className = "",
  color1 = "rgba(59, 130, 246, 0.3)",
  color2 = "rgba(147, 51, 234, 0.3)",
  blur = 40,
  duration = 8,
  delay = 0
}: GradientOrbProps) {
  return (
    <motion.div
      className={`absolute rounded-full pointer-events-none ${className}`}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle, ${color1} 0%, ${color2} 50%, transparent 100%)`,
        filter: `blur(${blur}px)`,
      }}
      animate={{
        x: [0, 100, -50, 0],
        y: [0, -80, 60, 0],
        scale: [1, 1.2, 0.8, 1],
        rotate: [0, 180, 360],
        opacity: [0.5, 0.8, 0.3, 0.5]
      }}
      transition={{
        duration,
        delay,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  );
} 