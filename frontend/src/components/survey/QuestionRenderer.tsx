'use client';

import { QuestionComponentProps } from '@/types/question.types';
import MultipleChoiceQuestion from './MultipleChoiceQuestion';
import SingleOptionQuestion from './SingleOptionQuestion';
import TextInputQuestion from './TextInputQuestion';
import SubFormQuestion from './SubFormQuestion';

const QuestionRenderer: React.FC<QuestionComponentProps> = (props) => {
  const { question } = props;

  switch (question.Question_type) {
    case 'multiple_choice':
      return <MultipleChoiceQuestion {...props} />;
    case 'single_option':
      return <SingleOptionQuestion {...props} />;
    case 'text_input':
      return <TextInputQuestion {...props} />;
    case 'sub_form':
      return <SubFormQuestion {...props} />;
    default:
      return <div>Unsupported question type: {question.Question_type}</div>;
  }
};

export default QuestionRenderer;
