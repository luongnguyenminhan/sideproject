'use client';

import { Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { QuestionComponentProps, QuestionOption } from '@/types/question.types';

const MultipleChoiceQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const currentAnswers = (selectedAnswers[questionIndex] as string[]) || [];
  const options = question.Question_data as QuestionOption[];

  const getClasses = (isSelected: boolean = false) => {
    return isSelected 
      ? 'bg-[var(--primary)] text-white border-[var(--primary)]' 
      : 'bg-[var(--card)] text-[var(--foreground)] border-[var(--border)] hover:bg-[var(--primary)] hover:text-white';
  };

  const handleOptionSelect = (optionId: string) => {
    const isSelected = currentAnswers.includes(optionId);
    let newAnswers;

    if (isSelected) {
      newAnswers = currentAnswers.filter((id: string) => id !== optionId);
    } else {
      newAnswers = [...currentAnswers, optionId];
    }

    onAnswerChange(questionIndex, 'multiple', newAnswers);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { 
      opacity: 0, 
      x: -20,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 25,
      },
    },
  };

  const useGridLayout = options.length <= 12;

  if (useGridLayout) {
    const getGridCols = () => {
      if (options.length <= 2) return 'grid-cols-1 sm:grid-cols-2';
      if (options.length <= 4) return 'grid-cols-1 sm:grid-cols-2';
      if (options.length <= 6) return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
      return 'grid-cols-1 sm:grid-cols-2';
    };

    return (
      <motion.div 
        className={`grid ${getGridCols()} gap-2 md:gap-3 w-full overflow-y-auto pr-2 px-2 md:px-4 py-2`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {options.map((option, index) => {
          const isSelected = currentAnswers.includes(option.id);
          return (
            <motion.div
              key={option.id}
              variants={itemVariants}
              onClick={() => handleOptionSelect(option.id)}
              className={`
                relative cursor-pointer rounded-lg p-3 md:p-4 text-center border-2 group overflow-hidden transition-all duration-300
                ${getClasses(isSelected)}
              `}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.2 }}
            >
              {/* Pulse Background */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-br from-[color:var(--feature-purple)] to-[color:var(--feature-blue)] rounded-2xl"
                animate={{
                  opacity: isSelected ? [0.3, 0.6, 0.3] : 0,
                }}
                transition={{
                  duration: 2,
                  repeat: isSelected ? Infinity : 0,
                  ease: "easeInOut"
                }}
              />

              <motion.div 
                className='font-medium text-sm md:text-base relative z-10 leading-snug'
                initial={{ y: 0, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: index * 0.05 + 0.2 }}
              >
                {option.label}
              </motion.div>

              {isSelected && (
                <motion.div 
                  className='absolute top-1.5 right-1.5'
                  initial={{ scale: 0, rotate: 180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  exit={{ scale: 0, rotate: -180 }}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 15,
                  }}
                >
                  <motion.div 
                    className='w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-md'
                    animate={{ 
                      scale: [1, 1.1, 1]
                    }}
                    transition={{
                      scale: { duration: 1, repeat: Infinity, ease: "easeInOut" }
                    }}
                  >
                    <Check className='w-3 h-3 text-green-600' />
                  </motion.div>
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </motion.div>
    );
  }

  return (
    <div className='space-y-2 w-full overflow-y-auto pr-2 -mr-2 px-2 md:px-4 py-2'>
      {options.map((option) => {
        const isSelected = currentAnswers.includes(option.id);
        return (
          <div
            key={option.id}
            onClick={() => handleOptionSelect(option.id)}
            className={`
              relative cursor-pointer rounded-lg p-3 md:p-4 transition-all duration-300 border-2 group flex items-center space-x-3 !overflow-x-hidden
              ${getClasses(isSelected)}
              ${isSelected ? 'transform shadow-md' : 'hover:shadow-sm'}
            `}
          >
            <div className='flex-1'>
              <div className='font-medium text-sm md:text-base leading-snug'>{option.label}</div>
            </div>
            {isSelected && (
              <div className='w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-md'>
                <Check className='w-3 h-3 text-green-600' />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default MultipleChoiceQuestion;
