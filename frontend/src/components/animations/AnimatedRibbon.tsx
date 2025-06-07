'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface AnimatedRibbonProps {
  count?: number;
  thickness?: number;
  speed?: number;
  maxAge?: number;
  enableFade?: boolean;
  enableWaves?: boolean;
  className?: string;
}

export default function AnimatedRibbon({
  count = 1,
  thickness = 30,
  speed = 0.5,
  maxAge = 500,
  enableFade = true,
  enableWaves = true,
  className = ""
}: AnimatedRibbonProps) {
  const [ribbons, setRibbons] = useState<Array<{
    id: number;
    x: number;
    y: number;
    age: number;
    opacity: number;
    rotation: number;
  }>>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setRibbons(prev => {
        const newRibbons = prev
          .map(ribbon => ({
            ...ribbon,
            age: ribbon.age + 1,
            opacity: enableFade ? Math.max(0, 1 - (ribbon.age / maxAge)) : 1,
            y: ribbon.y + speed,
            x: enableWaves ? ribbon.x + Math.sin(ribbon.age * 0.05) * 2 : ribbon.x
          }))
          .filter(ribbon => ribbon.age < maxAge);

        if (newRibbons.length < count) {
          const newRibbon = {
            id: Math.random(),
            x: Math.random() * 100,
            y: -10,
            age: 0,
            opacity: 1,
            rotation: Math.random() * 360
          };
          newRibbons.push(newRibbon);
        }

        return newRibbons;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [count, speed, maxAge, enableFade, enableWaves]);

  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {ribbons.map(ribbon => (
        <motion.div
          key={ribbon.id}
          className="absolute"
          style={{
            left: `${ribbon.x}%`,
            top: `${ribbon.y}%`,
            opacity: ribbon.opacity,
            transform: `rotate(${ribbon.rotation}deg)`,
          }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0 }}
        >
          <div
            className="bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] rounded-full blur-sm"
            style={{
              width: `${thickness}px`,
              height: '4px',
            }}
          />
        </motion.div>
      ))}
    </div>
  );
} 