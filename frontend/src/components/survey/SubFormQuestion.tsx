'use client';

import { QuestionComponentProps, Question } from '@/types/question.types';
import QuestionRenderer from './QuestionRenderer';
import { useTranslation } from '@/contexts/TranslationContext';

const SubFormQuestion: React.FC<QuestionComponentProps> = ({
  question,
  questionIndex,
  selectedAnswers,
  onAnswerChange,
}) => {
  const { t } = useTranslation();
  const subQuestions = question.Question_data as Question[];
  const subFormAnswers = (selectedAnswers[questionIndex] as Record<string, unknown>) || {};

  const handleSubQuestionChange = (subQuestionIndex: number, answerId: string, value?: unknown) => {
    const newSubFormAnswers = {
      ...subFormAnswers,
      [subQuestionIndex]: value !== undefined ? value : answerId,
    };
    onAnswerChange(questionIndex, 'subform', newSubFormAnswers);
  };

  return (
    <div className='h-full overflow-y-auto pr-2 -mr-2'>
      <div className='space-y-4 pb-4'>
        {subQuestions.map((subQuestion, subIndex) => (
          <div key={subIndex} className='bg-[var(--muted)] rounded-2xl p-4 md:p-6 flex-shrink-0'>
          <h3 className='text-xl font-semibold text-[var(--foreground)] mb-4'>
            {t(subQuestion.Question)}
          </h3>
          {subQuestion.subtitle && (
            <p className='text-[var(--muted-foreground)] mb-6'>{t(subQuestion.subtitle)}</p>
          )}
          <QuestionRenderer
            question={subQuestion}
            questionIndex={subIndex}
            selectedAnswers={subFormAnswers}
            onAnswerChange={handleSubQuestionChange}
          />
          </div>
        ))}
      </div>
    </div>
  );
};

export default SubFormQuestion;
