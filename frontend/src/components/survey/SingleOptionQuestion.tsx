'use client';

import { Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { QuestionComponentProps, QuestionOption } from '@/types/question.types';

const SingleOptionQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const currentAnswer = selectedAnswers[questionIndex];
  const options = question.Question_data as QuestionOption[];

  const getClasses = (isSelected: boolean = false) => {
    return isSelected 
      ? 'bg-[var(--primary)] text-white border-[var(--primary)]' 
      : 'bg-[var(--card)] text-[var(--foreground)] border-[var(--border)] hover:bg-[var(--primary)] hover:text-white';
  };

  const handleOptionSelect = (optionId: string) => {
    onAnswerChange(questionIndex, optionId);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { 
      opacity: 0, 
      y: 20,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 20,
      },
    },
  };

  return (
    <motion.div 
      className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-8'
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {options.map((option, index) => {
        const isSelected = currentAnswer === option.id;
        return (
          <motion.div
            key={option.id}
            variants={itemVariants}
            onClick={() => handleOptionSelect(option.id)}
            className={`
              relative cursor-pointer rounded-2xl p-8 text-center border-2 group overflow-hidden
              ${getClasses(isSelected)}
            `}
            whileHover={{ 
              scale: 1.05, 
              y: -8,
              transition: { duration: 0.2 }
            }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.3 }}
          >
            {/* Animated Background Gradient */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-br from-[color:var(--feature-purple)] to-[color:var(--feature-blue)] rounded-2xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: isSelected ? 1 : 0 }}
              transition={{ duration: 0.3 }}
            />

            {/* Shimmer Effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
              initial={{ x: '-100%' }}
              animate={{ x: isSelected ? '100%' : '-100%' }}
              transition={{
                duration: 0.8,
                ease: "easeInOut",
              }}
            />

            <motion.div 
              className='font-bold text-xl relative z-10'
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: index * 0.1 + 0.3 }}
            >
              {option.label}
            </motion.div>

            {/* Animated Check Icon */}
            {isSelected && (
              <motion.div 
                className='absolute top-3 right-3'
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                  type: "spring",
                  stiffness: 400,
                  damping: 10,
                }}
              >
                <motion.div 
                  className='w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg'
                  animate={{
                    boxShadow: [
                      "0 4px 8px rgba(0,0,0,0.1)",
                      "0 8px 16px rgba(0,0,0,0.2)",
                      "0 4px 8px rgba(0,0,0,0.1)"
                    ]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <Check className='w-5 h-5 text-green-600' />
                </motion.div>
              </motion.div>
            )}

            {/* Floating Particles */}
            {isSelected && (
              <div className="absolute inset-0 pointer-events-none">
                {Array.from({ length: 6 }).map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute w-1 h-1 bg-white rounded-full"
                    style={{
                      left: `${20 + Math.random() * 60}%`,
                      top: `${20 + Math.random() * 60}%`,
                    }}
                    animate={{
                      y: [-10, -20, -10],
                      opacity: [0, 1, 0],
                      scale: [0, 1, 0],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      delay: i * 0.3,
                      ease: "easeInOut"
                    }}
                  />
                ))}
              </div>
            )}
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default SingleOptionQuestion;
