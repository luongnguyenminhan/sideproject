'use client';

import { motion, useSpring, useMotionValue } from 'framer-motion';
import { ReactNode, useRef, MouseEvent } from 'react';

interface MagneticCardProps {
  children: ReactNode;
  className?: string;
  strength?: number;
  restoreSpeed?: number;
}

export default function MagneticCard({ 
  children, 
  className = "",
  strength = 20,
}: MagneticCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  
  const springX = useSpring(x, { stiffness: 150, damping: 15 });
  const springY = useSpring(y, { stiffness: 150, damping: 15 });

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const distanceX = e.clientX - centerX;
    const distanceY = e.clientY - centerY;
    
    const maxDistance = Math.max(rect.width, rect.height) / 2;
    const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
    
    if (distance < maxDistance) {
      const factor = (maxDistance - distance) / maxDistance;
      x.set(distanceX * factor * strength / maxDistance);
      y.set(distanceY * factor * strength / maxDistance);
    }
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      style={{
        x: springX,
        y: springY
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`transition-all duration-300 ${className}`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {children}
    </motion.div>
  );
} 