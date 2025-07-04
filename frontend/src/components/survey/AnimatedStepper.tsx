'use client';

import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

interface AnimatedStepperProps {
  currentStep: number;
  totalSteps: number;
  questions: Array<{ id?: string; Question: string }>;
}

const AnimatedStepper: React.FC<AnimatedStepperProps> = ({
  currentStep,
  totalSteps,
  questions,
}) => {
  // Show max 7 steps on desktop, 5 on mobile to prevent overflow
  const maxVisibleSteps = 7;
  const maxVisibleStepsMobile = 5;
  
  // Calculate visible range
  const getVisibleRange = () => {
    const maxSteps = window.innerWidth < 768 ? maxVisibleStepsMobile : maxVisibleSteps;
    
    if (totalSteps <= maxSteps) {
      return { start: 0, end: totalSteps - 1 };
    }
    
    // Center current step in visible range
    let start = Math.max(0, currentStep - Math.floor(maxSteps / 2));
    let end = Math.min(totalSteps - 1, start + maxSteps - 1);
    
    // Adjust if we're near the end
    if (end - start < maxSteps - 1) {
      start = Math.max(0, end - maxSteps + 1);
    }

    if (start < 0) {
      start = 0;
    }

    if (end > totalSteps - 1) {
      end = totalSteps - 1;
    }
    
    return { start, end };
  };

  const { start, end } = getVisibleRange();
  const visibleSteps = questions.slice(start, end + 1);

  return (
    <div className="flex justify-center mb-6 md:mb-8 flex-shrink-0">
      <div className="relative w-full max-w-full overflow-hidden">
        {/* Show navigation dots if steps are hidden */}
        {start > 0 && (
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 z-10">
            <div className="flex items-center space-x-1 bg-[color:var(--background)]/80 backdrop-blur-sm rounded-full px-2 py-1">
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
            </div>
          </div>
        )}
        
        {end < totalSteps - 1 && (
          <div className="absolute right-0 top-1/2 transform -translate-y-1/2 z-10">
            <div className="flex items-center space-x-1 bg-[color:var(--background)]/80 backdrop-blur-sm rounded-full px-2 py-1">
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
              <div className="w-1 h-1 bg-[color:var(--muted-foreground)] rounded-full"></div>
            </div>
          </div>
        )}

        {/* Stepper container with smooth scrolling */}
        <motion.div 
          className="flex items-center justify-center space-x-1 md:space-x-2 px-8"
          animate={{ 
            x: start > 0 ? -20 : 0 
          }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {visibleSteps.map((_, index) => {
            const actualIndex = start + index;
            return (
              <div key={actualIndex} className="flex items-center">
                <motion.div
                  className={`
                    w-6 h-6 md:w-10 md:h-10 rounded-full flex items-center justify-center font-semibold text-xs md:text-sm relative overflow-hidden flex-shrink-0
                    ${
                      actualIndex < currentStep
                        ? 'bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)]'
                        : actualIndex === currentStep
                        ? 'bg-[color:var(--primary)] text-[color:var(--primary-foreground)]'
                        : 'bg-[color:var(--muted)] text-[color:var(--muted-foreground)]'
                    }
                  `}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ 
                    scale: actualIndex === currentStep ? 1.1 : 1, 
                    opacity: 1 
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 300,
                    damping: 20,
                    delay: index * 0.1
                  }}
                  whileHover={{ 
                    scale: actualIndex <= currentStep ? 1.15 : 1.05,
                    transition: { duration: 0.2 }
                  }}
                >
                  {/* Animated Ring for Current Step */}
                  {actualIndex === currentStep && (
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 md:border-4 border-[color:var(--primary)]"
                      initial={{ scale: 1, opacity: 0 }}
                      animate={{ scale: 1.3, opacity: 0 }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeOut"
                      }}
                    />
                  )}

                  {/* Step Content */}
                  <motion.div
                    key={`step-${actualIndex}-${actualIndex < currentStep}`}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{
                      type: "spring",
                      stiffness: 400,
                      damping: 10,
                      delay: actualIndex < currentStep ? 0 : 0.3
                    }}
                  >
                    {actualIndex < currentStep ? (
                      <motion.div
                        initial={{ rotate: -90, scale: 0 }}
                        animate={{ rotate: 0, scale: 1 }}
                        transition={{
                          type: "spring",
                          stiffness: 300,
                          damping: 15
                        }}
                      >
                        <Check className="w-3 h-3 md:w-5 md:h-5" />
                      </motion.div>
                    ) : (
                      <motion.span
                        initial={{ y: 10, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="text-xs md:text-sm"
                      >
                        {actualIndex + 1}
                      </motion.span>
                    )}
                  </motion.div>

                  {/* Shadow Effect */}
                  <motion.div
                    className="absolute inset-0 rounded-full"
                    style={{
                      background: actualIndex <= currentStep 
                        ? 'radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%)'
                        : 'transparent'
                    }}
                    animate={{
                      opacity: actualIndex === currentStep ? [0.5, 0.8, 0.5] : 0.3
                    }}
                    transition={{
                      duration: 2,
                      repeat: actualIndex === currentStep ? Infinity : 0,
                      ease: "easeInOut"
                    }}
                  />
                </motion.div>

                {/* Progress Line */}
                {actualIndex < totalSteps - 1 && index < visibleSteps.length - 1 && (
                  <motion.div
                    className="relative w-4 md:w-12 h-0.5 md:h-1 mx-1 rounded-full overflow-hidden bg-[color:var(--muted)] flex-shrink-0"
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ 
                      delay: index * 0.1 + 0.3,
                      duration: 0.5,
                      ease: "easeOut"
                    }}
                  >
                    <motion.div
                      className="absolute inset-0 bg-[color:var(--feature-green)] rounded-full origin-left"
                      initial={{ scaleX: 0 }}
                      animate={{ 
                        scaleX: actualIndex < currentStep ? 1 : 0
                      }}
                      transition={{
                        duration: 0.8,
                        ease: "easeInOut",
                        delay: actualIndex < currentStep ? 0.5 : 0
                      }}
                    />
                    
                    {/* Shimmer Effect */}
                    {actualIndex < currentStep && (
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                        initial={{ x: '-100%' }}
                        animate={{ x: '100%' }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          repeatDelay: 3,
                          ease: "easeInOut"
                        }}
                      />
                    )}
                  </motion.div>
                )}
              </div>
            );
          })}
        </motion.div>

        {/* Progress indicator at bottom for large surveys */}
        {totalSteps > 7 && (
          <div className="mt-2 flex justify-center">
            <div className="text-xs text-[color:var(--muted-foreground)] bg-[color:var(--muted)]/50 px-2 py-1 rounded-full">
              {currentStep + 1} / {totalSteps}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnimatedStepper; 