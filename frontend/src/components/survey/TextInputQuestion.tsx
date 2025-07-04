'use client';

import { User, Mail, Building, MessageSquare, PenTool } from 'lucide-react';
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

  // Handle single free-form text input when no structured options
  const handleFreeFormChange = (value: string) => {
    onAnswerChange(questionIndex, 'text', value);
  };

  const getIcon = (fieldId: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      fullName: <User className='w-5 h-5' />,
      name: <User className='w-5 h-5' />,
      email: <Mail className='w-5 h-5' />,
      company: <Building className='w-5 h-5' />,
      bio: <MessageSquare className='w-5 h-5' />,
      text: <PenTool className='w-5 h-5' />,
      answer: <PenTool className='w-5 h-5' />,
    };
    return iconMap[fieldId] || <PenTool className='w-5 h-5' />;
  };

  // If no structured options provided, render free-form text input
  if (!options || options.length === 0) {
    const freeFormValue = typeof selectedAnswers[questionIndex] === 'string' 
      ? selectedAnswers[questionIndex] as string 
      : '';

    return (
      <div className='space-y-4 max-w-2xl mx-auto'>
        <div className='group'>
          <label className='block text-sm font-semibold text-[color:var(--foreground)] mb-3'>
            <div className='flex items-center space-x-2'>
              <span className='text-[color:var(--primary)]'>
                <PenTool className='w-5 h-5' />
              </span>
              <span>{question.subtitle || 'Your Answer'}</span>
              <span className='text-[color:var(--destructive)]'>*</span>
            </div>
          </label>
          
          <textarea
            value={freeFormValue}
            onChange={(e) => handleFreeFormChange(e.target.value)}
            placeholder={`Share your thoughts about: ${question.Question}`}
            rows={4}
            className='w-full px-4 py-3 rounded-xl border-2 border-[color:var(--border)] bg-[color:var(--background)] text-[color:var(--foreground)] focus:border-[color:var(--primary)] focus:ring-4 focus:ring-[color:var(--primary)]/20 transition-all duration-300 resize-none placeholder:text-[color:var(--muted-foreground)]'
          />
          
          <div className='mt-2 text-xs text-[color:var(--muted-foreground)]'>
            💡 Take your time to share your experience and thoughts
          </div>
        </div>
      </div>
    );
  }

  // Render structured input fields if options are provided
  return (
    <div className='space-y-6 max-w-2xl mx-auto'>
      {options.map((option) => (
        <div key={option.id} className='group'>
          <label className='block text-sm font-semibold text-[color:var(--foreground)] mb-2'>
            <div className='flex items-center space-x-2'>
              <span className='text-[color:var(--primary)]'>{getIcon(option.id)}</span>
              <span>{option.label}</span>
              {option.required && <span className='text-[color:var(--destructive)]'>*</span>}
            </div>
          </label>
          {option.type === 'textarea' ? (
            <textarea
              value={inputValues[option.id] || ''}
              onChange={(e) => handleInputChange(option.id, e.target.value)}
              placeholder={option.placeholder || ''}
              rows={option.rows || 3}
              className='w-full px-4 py-3 rounded-xl border-2 border-[color:var(--border)] bg-[color:var(--background)] text-[color:var(--foreground)] focus:border-[color:var(--primary)] focus:ring-4 focus:ring-[color:var(--primary)]/20 transition-all duration-300 resize-none placeholder:text-[color:var(--muted-foreground)]'
            />
          ) : (
            <input
              type={option.type || 'text'}
              value={inputValues[option.id] || ''}
              onChange={(e) => handleInputChange(option.id, e.target.value)}
              placeholder={option.placeholder || ''}
              className='w-full px-4 py-3 rounded-xl border-2 border-[color:var(--border)] bg-[color:var(--background)] text-[color:var(--foreground)] focus:border-[color:var(--primary)] focus:ring-4 focus:ring-[color:var(--primary)]/20 transition-all duration-300 placeholder:text-[color:var(--muted-foreground)]'
            />
          )}
        </div>
      ))}
    </div>
  );
};

export default TextInputQuestion;
