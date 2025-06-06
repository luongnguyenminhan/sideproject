'use client';

import { Check } from 'lucide-react';
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

  return (
    <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
      {options.map((option) => {
        const isSelected = currentAnswer === option.id;
        return (
          <div
            key={option.id}
            onClick={() => handleOptionSelect(option.id)}
            className={`
              relative cursor-pointer rounded-2xl p-8 text-center transition-all duration-300 border-2 group
              ${getClasses(isSelected)}
              ${isSelected ? 'transform scale-105 shadow-[var(--card-hover-shadow)]' : 'hover:shadow-[var(--button-hover-shadow)] hover:-translate-y-2'}
            `}
          >
            <div className='font-bold text-xl'>{option.label}</div>
            {isSelected && (
              <div className='absolute top-3 right-3'>
                <div className='w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg'>
                  <Check className='w-5 h-5 text-green-600' />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default SingleOptionQuestion;
