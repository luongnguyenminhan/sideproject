'use client';

import SurveyContainer from './SurveyContainer';
import { Question } from '@/types/question.types';

interface SurveyClientWrapperProps {
  questions: Question[];
}

export function SurveyClientWrapper({ questions }: SurveyClientWrapperProps) {
  return <SurveyContainer questions={questions} />;
} 