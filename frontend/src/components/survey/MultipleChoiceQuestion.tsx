'use client';

import { Check } from 'lucide-react';
import { QuestionComponentProps, QuestionOption } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';

const MultipleChoiceQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const { t } = useTranslation();
  const currentAnswers = (selectedAnswers[questionIndex] as string[]) || [];
  const options = question.Question_data as QuestionOption[];

  const getColorClasses = (color: string = 'blue', isSelected: boolean = false) => {
    const colorMap = {
      blue: isSelected ? 'bg-[var(--feature-blue-text)] text-white border-[var(--feature-blue-text)]' : 'bg-[var(--feature-blue)] text-[var(--feature-blue-text)] border-[var(--border)] hover:bg-[var(--feature-blue-text)] hover:text-white',
      purple: isSelected ? 'bg-[var(--feature-purple-text)] text-white border-[var(--feature-purple-text)]' : 'bg-[var(--feature-purple)] text-[var(--feature-purple-text)] border-[var(--border)] hover:bg-[var(--feature-purple-text)] hover:text-white',
      green: isSelected ? 'bg-[var(--feature-green-text)] text-white border-[var(--feature-green-text)]' : 'bg-[var(--feature-green)] text-[var(--feature-green-text)] border-[var(--border)] hover:bg-[var(--feature-green-text)] hover:text-white',
      orange: isSelected ? 'bg-orange-500 text-white border-orange-500' : 'bg-orange-50 text-orange-700 border-[var(--border)] hover:bg-orange-500 hover:text-white',
      red: isSelected ? 'bg-red-500 text-white border-red-500' : 'bg-red-50 text-red-700 border-[var(--border)] hover:bg-red-500 hover:text-white',
      yellow: isSelected ? 'bg-[var(--feature-yellow-text)] text-white border-[var(--feature-yellow-text)]' : 'bg-[var(--feature-yellow)] text-[var(--feature-yellow-text)] border-[var(--border)] hover:bg-[var(--feature-yellow-text)] hover:text-white',
      cyan: isSelected ? 'bg-cyan-500 text-white border-cyan-500' : 'bg-cyan-50 text-cyan-700 border-[var(--border)] hover:bg-cyan-500 hover:text-white',
      gray: isSelected ? 'bg-gray-500 text-white border-gray-500' : 'bg-gray-50 text-gray-700 border-[var(--border)] hover:bg-gray-500 hover:text-white',
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
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
                ${getColorClasses(option.color, isSelected)}
                ${isSelected ? 'transform scale-105 shadow-[var(--card-hover-shadow)]' : 'hover:shadow-[var(--button-hover-shadow)] hover:-translate-y-1'}
              `}
            >
              <div className='text-3xl mb-3 transition-transform duration-300 group-hover:scale-110'>
                {option.icon}
              </div>
              <div className='font-semibold text-lg mb-1'>{t(option.label || '')}</div>
              <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
                {t(option.description || '')}
              </div>
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
              ${getColorClasses(option.color, isSelected)}
              ${isSelected ? 'transform scale-[1.02] shadow-md' : 'hover:shadow-sm'}
            `}
          >
            <div className='text-2xl transition-transform duration-300 group-hover:scale-110'>
              {option.icon}
            </div>
            <div className='flex-1'>
              <div className='font-semibold text-lg'>{t(option.label || '')}</div>
              <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
                {t(option.description || '')}
              </div>
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
