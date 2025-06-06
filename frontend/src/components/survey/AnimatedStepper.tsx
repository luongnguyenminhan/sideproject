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
  return (
    <div className="flex justify-center mb-6 md:mb-8 flex-shrink-0">
      <div className="flex items-center space-x-2 md:space-x-4">
        {questions.map((_, index) => (
          <div key={index} className="flex items-center">
            <motion.div
              className={`
                w-8 h-8 md:w-12 md:h-12 rounded-full flex items-center justify-center font-semibold text-xs md:text-sm relative overflow-hidden
                ${
                  index < currentStep
                    ? 'bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)]'
                    : index === currentStep
                    ? 'bg-[color:var(--primary)] text-[color:var(--primary-foreground)]'
                    : 'bg-[color:var(--muted)] text-[color:var(--muted-foreground)]'
                }
              `}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ 
                scale: index === currentStep ? 1.1 : 1, 
                opacity: 1 
              }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 20,
                delay: index * 0.1
              }}
              whileHover={{ 
                scale: index <= currentStep ? 1.15 : 1.05,
                transition: { duration: 0.2 }
              }}
            >
              {/* Animated Ring for Current Step */}
              {index === currentStep && (
                <motion.div
                  className="absolute inset-0 rounded-full border-4 border-[color:var(--primary)]"
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
                key={`step-${index}-${index < currentStep}`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 400,
                  damping: 10,
                  delay: index < currentStep ? 0 : 0.3
                }}
              >
                {index < currentStep ? (
                  <motion.div
                    initial={{ rotate: -90, scale: 0 }}
                    animate={{ rotate: 0, scale: 1 }}
                    transition={{
                      type: "spring",
                      stiffness: 300,
                      damping: 15
                    }}
                  >
                    <Check className="w-4 h-4 md:w-6 md:h-6" />
                  </motion.div>
                ) : (
                  <motion.span
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    {index + 1}
                  </motion.span>
                )}
              </motion.div>

              {/* Shadow Effect */}
              <motion.div
                className="absolute inset-0 rounded-full"
                style={{
                  background: index <= currentStep 
                    ? 'radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%)'
                    : 'transparent'
                }}
                animate={{
                  opacity: index === currentStep ? [0.5, 0.8, 0.5] : 0.3
                }}
                transition={{
                  duration: 2,
                  repeat: index === currentStep ? Infinity : 0,
                  ease: "easeInOut"
                }}
              />
            </motion.div>

            {/* Progress Line */}
            {index < totalSteps - 1 && (
              <motion.div
                className="relative w-8 md:w-16 h-1 mx-1 md:mx-2 rounded-full overflow-hidden bg-[color:var(--muted)]"
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
                    scaleX: index < currentStep ? 1 : 0
                  }}
                  transition={{
                    duration: 0.8,
                    ease: "easeInOut",
                    delay: index < currentStep ? 0.5 : 0
                  }}
                />
                
                {/* Shimmer Effect */}
                {index < currentStep && (
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
        ))}
      </div>
    </div>
  );
};

export default AnimatedStepper; 