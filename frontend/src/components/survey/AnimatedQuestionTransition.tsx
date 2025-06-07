'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ReactNode } from 'react';

interface AnimatedQuestionTransitionProps {
  children: ReactNode;
  questionKey: string | number;
  direction: 'forward' | 'backward';
}

const slideVariants = {
  enter: () => ({
    opacity: 0,
  }),
  center: {
    opacity: 1,
  },
  exit: () => ({
    opacity: 0,
  }),
};

const questionHeaderVariants = {
  enter: { opacity: 0 },
  center: { opacity: 1 },
  exit: { opacity: 0 },
};

const contentVariants = {
  enter: { opacity: 0 },
  center: { opacity: 1 },
  exit: { opacity: 0 },
};

const AnimatedQuestionTransition: React.FC<AnimatedQuestionTransitionProps> = ({
  children,
  questionKey,
  direction,
}) => {
  return (
    <div className="relative w-full h-full perspective-1000">
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={questionKey}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 30,
            duration: 0.5,
          }}
          className="w-full h-full"
          style={{ perspective: '1000px' }}
        >
          {/* Question Header Animation */}
          <motion.div
            variants={questionHeaderVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              delay: 0.1,
              duration: 0.4,
              ease: "easeOut"
            }}
          >
            {/* This will contain the question title and subtitle */}
          </motion.div>

          {/* Main Content Animation */}
          <motion.div
            variants={contentVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              delay: 0.2,
              duration: 0.5,
              ease: "easeOut"
            }}
            className="w-full h-full"
          >
            {children}
          </motion.div>

          {/* Decorative Elements */}
          <motion.div
            className="absolute -top-4 -right-4 w-20 h-20 rounded-full blur-xl"
            style={{
              background: `linear-gradient(135deg, 
                hsl(from var(--primary) h s l / 0.2), 
                hsl(from var(--accent) h s l / 0.2))`
            }}
            animate={{
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "linear"
            }}
          />
          
          <motion.div
            className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full blur-xl"
            style={{
              background: `linear-gradient(135deg, 
                hsl(from var(--secondary) h s l / 0.2), 
                hsl(from var(--muted) h s l / 0.2))`
            }}
            animate={{
              rotate: [360, 180, 0],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default AnimatedQuestionTransition; 