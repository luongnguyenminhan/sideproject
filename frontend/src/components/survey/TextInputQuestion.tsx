'use client';

import { User, Mail, Building, MessageSquare } from 'lucide-react';
import { QuestionComponentProps, QuestionOption } from '@/types/question.types';

const TextInputQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const inputValues = (selectedAnswers[questionIndex] as Record<string, string>) || {};
  const options = question.Question_data as QuestionOption[];

  const handleInputChange = (fieldId: string, value: string) => {
    const newValues = {
      ...inputValues,
      [fieldId]: value,
    };
    onAnswerChange(questionIndex, 'input', newValues);
  };

  const getIcon = (fieldId: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      fullName: <User className='w-5 h-5' />,
      email: <Mail className='w-5 h-5' />,
      company: <Building className='w-5 h-5' />,
      bio: <MessageSquare className='w-5 h-5' />,
    };
    return iconMap[fieldId] || <User className='w-5 h-5' />;
  };

  return (
    <div className='space-y-6 max-w-2xl mx-auto'>
      {options.map((option) => (
        <div key={option.id} className='group'>
          <label className='block text-sm font-semibold text-[var(--foreground)] mb-2'>
            <div className='flex items-center space-x-2'>
              <span className='text-[var(--primary)]'>{getIcon(option.id)}</span>
              <span>{option.label}</span>
              {option.required && <span className='text-[var(--destructive)]'>*</span>}
            </div>
          </label>
          {option.type === 'textarea' ? (
            <textarea
              value={inputValues[option.id] || ''}
              onChange={(e) => handleInputChange(option.id, e.target.value)}
              placeholder={option.placeholder || ''}
              rows={option.rows || 3}
              className='w-full px-4 py-3 rounded-xl border-2 border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] focus:border-[var(--primary)] focus:ring-4 focus:ring-[var(--primary)]/20 transition-all duration-300 resize-none placeholder:text-[var(--muted-foreground)]'
            />
          ) : (
            <input
              type={option.type || 'text'}
              value={inputValues[option.id] || ''}
              onChange={(e) => handleInputChange(option.id, e.target.value)}
              placeholder={option.placeholder || ''}
              className='w-full px-4 py-3 rounded-xl border-2 border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] focus:border-[var(--primary)] focus:ring-4 focus:ring-[var(--primary)]/20 transition-all duration-300 placeholder:text-[var(--muted-foreground)]'
            />
          )}
        </div>
      ))}
    </div>
  );
};

export default TextInputQuestion;
