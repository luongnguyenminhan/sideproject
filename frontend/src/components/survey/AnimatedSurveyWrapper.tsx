'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface AnimatedSurveyWrapperProps {
  children: ReactNode;
  currentStep: number;
  totalSteps: number;
}

const AnimatedSurveyWrapper: React.FC<AnimatedSurveyWrapperProps> = ({
  children,
  currentStep,
  totalSteps,
}) => {
  // Calculate progress-based hue for dynamic colors
  const progressHue = (currentStep / Math.max(totalSteps - 1, 1)) * 360;

  return (
    <div className="fixed inset-0 overflow-hidden">
      {/* Enhanced Base Gradient Background */}
      <motion.div 
        className="absolute inset-0 bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]"
        animate={{
          background: `linear-gradient(135deg, 
            hsl(${progressHue}, 60%, 8%) 0%, 
            hsl(${(progressHue + 60) % 360}, 50%, 12%) 35%,
            hsl(${(progressHue + 120) % 360}, 40%, 15%) 100%)`
        }}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />

      {/* Floating Orbs with Progress-based Animation */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Large Primary Orb */}
        <motion.div
          className="absolute w-96 h-96 rounded-full blur-3xl"
          style={{
            background: `radial-gradient(circle, 
              hsl(${progressHue}, 70%, 25%) 0%, 
              hsl(${(progressHue + 40) % 360}, 60%, 20%) 50%, 
              transparent 70%)`
          }}
          initial={{ x: -100, y: -100 }}
          animate={{ 
            x: [window.innerWidth * 0.1, window.innerWidth * 0.8, window.innerWidth * 0.2],
            y: [window.innerHeight * 0.2, window.innerHeight * 0.7, window.innerHeight * 0.3],
            scale: [0.8, 1.2, 0.9],
            rotate: [0, 180, 360]
          }}
          transition={{
            duration: 20 + currentStep * 2,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Secondary Orb */}
        <motion.div
          className="absolute w-64 h-64 rounded-full blur-2xl"
          style={{
            background: `radial-gradient(circle, 
              hsl(${(progressHue + 120) % 360}, 80%, 30%) 0%, 
              hsl(${(progressHue + 160) % 360}, 70%, 25%) 50%, 
              transparent 70%)`
          }}
          initial={{ x: window.innerWidth + 50, y: window.innerHeight / 2 }}
          animate={{ 
            x: [window.innerWidth * 0.9, window.innerWidth * 0.1, window.innerWidth * 0.7],
            y: [window.innerHeight * 0.8, window.innerHeight * 0.2, window.innerHeight * 0.6],
            scale: [1, 0.7, 1.1],
            rotate: [360, 180, 0]
          }}
          transition={{
            duration: 25 + currentStep * 1.5,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Tertiary Orb */}
        <motion.div
          className="absolute w-48 h-48 rounded-full blur-xl"
          style={{
            background: `radial-gradient(circle, 
              hsl(${(progressHue + 240) % 360}, 90%, 35%) 0%, 
              hsl(${(progressHue + 280) % 360}, 80%, 30%) 50%, 
              transparent 70%)`
          }}
          initial={{ x: window.innerWidth / 2, y: -50 }}
          animate={{ 
            x: [window.innerWidth * 0.4, window.innerWidth * 0.6, window.innerWidth * 0.3],
            y: [window.innerHeight * 0.1, window.innerHeight * 0.9, window.innerHeight * 0.4],
            scale: [0.9, 1.3, 0.8],
            rotate: [0, -180, -360]
          }}
          transition={{
            duration: 18 + currentStep * 1.8,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Animated Particles */}
        {Array.from({ length: 15 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full"
            style={{
              background: `hsl(${(progressHue + i * 24) % 360}, 80%, 60%)`,
              boxShadow: `0 0 10px hsl(${(progressHue + i * 24) % 360}, 80%, 60%)`
            }}
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: 0.3
            }}
            animate={{
              x: [
                Math.random() * window.innerWidth,
                Math.random() * window.innerWidth,
                Math.random() * window.innerWidth
              ],
              y: [
                Math.random() * window.innerHeight,
                Math.random() * window.innerHeight,
                Math.random() * window.innerHeight
              ],
              opacity: [0.3, 0.8, 0.3],
              scale: [0.5, 1.2, 0.5]
            }}
            transition={{
              duration: 15 + Math.random() * 10,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.5
            }}
          />
        ))}

        {/* Grid Pattern Overlay */}
        <motion.div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, 
              hsl(${progressHue}, 100%, 80%) 1px, transparent 0)`,
            backgroundSize: '40px 40px'
          }}
          animate={{
            backgroundPosition: ['0px 0px', '40px 40px', '0px 0px']
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        {/* Ambient Light Effects */}
        <motion.div
          className="absolute top-0 left-1/4 w-1/2 h-1/3 rounded-full blur-3xl opacity-10"
          style={{
            background: `radial-gradient(ellipse, 
              hsl(${progressHue}, 100%, 50%) 0%, 
              transparent 70%)`
          }}
          animate={{
            opacity: [0.05, 0.15, 0.05],
            scale: [1, 1.2, 1]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        <motion.div
          className="absolute bottom-0 right-1/4 w-2/3 h-1/2 rounded-full blur-3xl opacity-10"
          style={{
            background: `radial-gradient(ellipse, 
              hsl(${(progressHue + 180) % 360}, 100%, 50%) 0%, 
              transparent 70%)`
          }}
          animate={{
            opacity: [0.1, 0.2, 0.1],
            scale: [1.1, 0.9, 1.1]
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Content Container with Backdrop Blur */}
      <div className="relative z-10 w-full h-full bg-[color:var(--background)]/20 backdrop-blur-sm">
        <motion.div
          className="w-full h-full"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          {children}
        </motion.div>
      </div>

      {/* Progress Indicator Light */}
      <motion.div
        className="absolute top-0 left-0 h-1 bg-gradient-to-r from-transparent via-white to-transparent"
        initial={{ width: '0%' }}
        animate={{ width: `${(currentStep / Math.max(totalSteps - 1, 1)) * 100}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </div>
  );
};

export default AnimatedSurveyWrapper; 