'use client';

import { Check } from 'lucide-react';
import { QuestionComponentProps, QuestionOption } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';

const SingleOptionQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const { t } = useTranslation();
  const currentAnswer = selectedAnswers[questionIndex];
  const options = question.Question_data as QuestionOption[];

  const getColorClasses = (color: string = 'blue', isSelected: boolean = false) => {
    const colorMap = {
      blue: isSelected ? 'bg-[var(--feature-blue-text)] text-white border-[var(--feature-blue-text)]' : 'bg-[var(--feature-blue)] text-[var(--feature-blue-text)] border-[var(--border)] hover:bg-[var(--feature-blue-text)] hover:text-white',
      purple: isSelected ? 'bg-[var(--feature-purple-text)] text-white border-[var(--feature-purple-text)]' : 'bg-[var(--feature-purple)] text-[var(--feature-purple-text)] border-[var(--border)] hover:bg-[var(--feature-purple-text)] hover:text-white',
      green: isSelected ? 'bg-[var(--feature-green-text)] text-white border-[var(--feature-green-text)]' : 'bg-[var(--feature-green)] text-[var(--feature-green-text)] border-[var(--border)] hover:bg-[var(--feature-green-text)] hover:text-white',
      orange: isSelected ? 'bg-orange-500 text-white border-orange-500' : 'bg-orange-50 text-orange-700 border-[var(--border)] hover:bg-orange-500 hover:text-white',
      yellow: isSelected ? 'bg-[var(--feature-yellow-text)] text-white border-[var(--feature-yellow-text)]' : 'bg-[var(--feature-yellow)] text-[var(--feature-yellow-text)] border-[var(--border)] hover:bg-[var(--feature-yellow-text)] hover:text-white',
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
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
              ${getColorClasses(option.color, isSelected)}
              ${isSelected ? 'transform scale-105 shadow-[var(--card-hover-shadow)]' : 'hover:shadow-[var(--button-hover-shadow)] hover:-translate-y-2'}
            `}
          >
            <div className='text-4xl mb-4 transition-transform duration-300 group-hover:scale-110'>
              {option.icon}
            </div>
            <div className='font-bold text-xl mb-2'>{t(option.label || '')}</div>
            <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
              {t(option.description || '')}
            </div>
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
