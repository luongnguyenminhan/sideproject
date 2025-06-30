export interface QuestionOption {
  id: string;
  label: string;
  // Chỉ giữ lại các thuộc tính cần thiết cho text input
  type?: string;
  placeholder?: string;
  required?: boolean;
  rows?: number;
}

export interface Question {
  id?: string;
  Question: string;
  Question_type: 'multiple_choice' | 'single_option' | 'text_input' | 'sub_form';
  Question_data: QuestionOption[] | Question[] | null;
  subtitle?: string;
}

export interface QuestionComponentProps {
  question: Question;
  questionIndex: number;
  selectedAnswers: Record<string, unknown>;
  onAnswerChange: (questionIndex: number, answerId: string, value?: unknown) => void;
}

export interface SurveyResponse {
  questionIndex: number;
  questionId?: string;
  questionType: string;
  answer: unknown;
  timestamp: Date;
}

export interface SurveyState {
  currentStep: number;
  selectedAnswers: Record<number, unknown>;
  responses: SurveyResponse[];
  isCompleted: boolean;
  startTime: Date;
  endTime?: Date;
}

export interface SurveyProcessRequest {
  type: string;
  answers: Record<number, unknown>;
  conversation_id?: string;
  timestamp?: string;
}

export interface WebsocketMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface SurveyProcessResponse {
  session_id?: string;
  human_readable_response?: string;
  ai_response?: string;
  websocket_messages?: WebsocketMessage[];
}
