'use client';

import { Check } from 'lucide-react';
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

  const useGridLayout = options.length <= 12;

  if (useGridLayout) {
    const cols = options.length <= 4 
      ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4' 
      : options.length <= 6 
      ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' 
      : options.length <= 9
      ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3'
      : 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4';

    return (
      <div className={`grid ${cols} gap-3 md:gap-4 h-full overflow-y-auto pr-2`}>
        {options.map((option) => {
          const isSelected = currentAnswers.includes(option.id);
          return (
            <div
              key={option.id}
              onClick={() => handleOptionSelect(option.id)}
              className={`
                relative cursor-pointer rounded-2xl p-6 text-center transition-all duration-300 border-2 group
                ${getClasses(isSelected)}
                ${isSelected ? 'transform scale-105 shadow-[var(--card-hover-shadow)]' : 'hover:shadow-[var(--button-hover-shadow)] hover:-translate-y-1'}
              `}
            >
              <div className='font-semibold text-lg'>{option.label}</div>
              {isSelected && (
                <div className='absolute top-2 right-2'>
                  <div className='w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-md'>
                    <Check className='w-4 h-4 text-green-600' />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className='space-y-3 h-full overflow-y-auto pr-2 -mr-2'>
      {options.map((option) => {
        const isSelected = currentAnswers.includes(option.id);
        return (
          <div
            key={option.id}
            onClick={() => handleOptionSelect(option.id)}
            className={`
              relative cursor-pointer rounded-xl p-4 transition-all duration-300 border-2 group flex items-center space-x-4
              ${getClasses(isSelected)}
              ${isSelected ? 'transform scale-[1.02] shadow-md' : 'hover:shadow-sm'}
            `}
          >
            <div className='flex-1'>
              <div className='font-semibold text-lg'>{option.label}</div>
            </div>
            {isSelected && (
              <div className='w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-md'>
                <Check className='w-4 h-4 text-green-600' />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default MultipleChoiceQuestion;
