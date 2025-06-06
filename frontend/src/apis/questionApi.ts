import { Question } from '@/types/question.types';

// Mock data for survey questions
export const mockSurveyQuestions: Question[] = [
  {
    id: '1',
    Question: 'survey.questions.role.title',
    Question_type: 'single_option',
    subtitle: 'survey.questions.role.subtitle',
    Question_data: [
      {
        id: 'student',
        label: 'survey.questions.role.options.student.label',
        icon: '🎓',
        description: 'survey.questions.role.options.student.description',
        color: 'blue',
      },
      {
        id: 'professional',
        label: 'survey.questions.role.options.professional.label',
        icon: '💼',
        description: 'survey.questions.role.options.professional.description',
        color: 'purple',
      },
      {
        id: 'freelancer',
        label: 'survey.questions.role.options.freelancer.label',
        icon: '🚀',
        description: 'survey.questions.role.options.freelancer.description',
        color: 'green',
      },
      {
        id: 'entrepreneur',
        label: 'survey.questions.role.options.entrepreneur.label',
        icon: '💡',
        description: 'survey.questions.role.options.entrepreneur.description',
        color: 'orange',
      },
    ],
  },
  {
    id: '2',
    Question: 'survey.questions.skills.title',
    Question_type: 'multiple_choice',
    subtitle: 'survey.questions.skills.subtitle',
    Question_data: [
      {
        id: 'javascript',
        label: 'JavaScript',
        icon: '🟨',
        description: 'Programming language for web development',
        color: 'yellow',
      },
      {
        id: 'typescript',
        label: 'TypeScript',
        icon: '🔵',
        description: 'Typed superset of JavaScript',
        color: 'blue',
      },
      {
        id: 'react',
        label: 'React',
        icon: '⚛️',
        description: 'JavaScript library for building UIs',
        color: 'blue',
      },
      {
        id: 'nodejs',
        label: 'Node.js',
        icon: '🟢',
        description: 'JavaScript runtime for server-side development',
        color: 'green',
      },
      {
        id: 'python',
        label: 'Python',
        icon: '🐍',
        description: 'General-purpose programming language',
        color: 'blue',
      },
      {
        id: 'java',
        label: 'Java',
        icon: '☕',
        description: 'Object-oriented programming language',
        color: 'orange',
      },
      {
        id: 'csharp',
        label: 'C#',
        icon: '🔷',
        description: 'Microsoft programming language',
        color: 'purple',
      },
      {
        id: 'cpp',
        label: 'C++',
        icon: '⚡',
        description: 'High-performance programming language',
        color: 'blue',
      },
      {
        id: 'html',
        label: 'HTML',
        icon: '🌐',
        description: 'Markup language for web pages',
        color: 'orange',
      },
      {
        id: 'css',
        label: 'CSS',
        icon: '🎨',
        description: 'Styling language for web pages',
        color: 'blue',
      },
      {
        id: 'angular',
        label: 'Angular',
        icon: '🅰️',
        description: 'TypeScript-based web framework',
        color: 'red',
      },
      {
        id: 'vue',
        label: 'Vue.js',
        icon: '💚',
        description: 'Progressive JavaScript framework',
        color: 'green',
      },
      {
        id: 'nextjs',
        label: 'Next.js',
        icon: '▲',
        description: 'React framework for production',
        color: 'black',
      },
      {
        id: 'express',
        label: 'Express.js',
        icon: '🚂',
        description: 'Web framework for Node.js',
        color: 'gray',
      },
      {
        id: 'mongodb',
        label: 'MongoDB',
        icon: '🍃',
        description: 'NoSQL database',
        color: 'green',
      },
      {
        id: 'mysql',
        label: 'MySQL',
        icon: '🐬',
        description: 'Relational database management system',
        color: 'blue',
      },
      {
        id: 'postgresql',
        label: 'PostgreSQL',
        icon: '🐘',
        description: 'Advanced open source database',
        color: 'blue',
      },
      {
        id: 'docker',
        label: 'Docker',
        icon: '🐳',
        description: 'Containerization platform',
        color: 'blue',
      },
      {
        id: 'kubernetes',
        label: 'Kubernetes',
        icon: '⚙️',
        description: 'Container orchestration platform',
        color: 'blue',
      },
      {
        id: 'aws',
        label: 'AWS',
        icon: '☁️',
        description: 'Amazon cloud computing services',
        color: 'orange',
      },
      {
        id: 'git',
        label: 'Git',
        icon: '📝',
        description: 'Version control system',
        color: 'orange',
      },
      {
        id: 'figma',
        label: 'Figma',
        icon: '🎨',
        description: 'UI/UX design tool',
        color: 'purple',
      },
      {
        id: 'photoshop',
        label: 'Photoshop',
        icon: '🖼️',
        description: 'Image editing software',
        color: 'blue',
      },
      {
        id: 'flutter',
        label: 'Flutter',
        icon: '📱',
        description: 'Mobile app development framework',
        color: 'blue',
      },
    ],
  },
  {
    id: '3',
    Question: 'survey.questions.personal.title',
    Question_type: 'text_input',
    subtitle: 'survey.questions.personal.subtitle',
    Question_data: [
      {
        id: 'fullName',
        label: 'survey.questions.personal.fields.fullName.label',
        type: 'text',
        placeholder: 'survey.questions.personal.fields.fullName.placeholder',
        required: true,
      },
      {
        id: 'email',
        label: 'survey.questions.personal.fields.email.label',
        type: 'email',
        placeholder: 'survey.questions.personal.fields.email.placeholder',
        required: true,
      },
      {
        id: 'phone',
        label: 'survey.questions.personal.fields.phone.label',
        type: 'tel',
        placeholder: 'survey.questions.personal.fields.phone.placeholder',
        required: false,
      },
      {
        id: 'company',
        label: 'survey.questions.personal.fields.company.label',
        type: 'text',
        placeholder: 'survey.questions.personal.fields.company.placeholder',
        required: false,
      },
    ],
  },
  {
    id: '4',
    Question: 'survey.questions.interests.title',
    Question_type: 'multiple_choice',
    subtitle: 'survey.questions.interests.subtitle',
    Question_data: [
      {
        id: 'technology',
        label: 'survey.questions.interests.options.technology.label',
        icon: '💻',
        description: 'survey.questions.interests.options.technology.description',
        color: 'blue',
      },
      {
        id: 'business',
        label: 'survey.questions.interests.options.business.label',
        icon: '📈',
        description: 'survey.questions.interests.options.business.description',
        color: 'green',
      },
      {
        id: 'design',
        label: 'survey.questions.interests.options.design.label',
        icon: '🎨',
        description: 'survey.questions.interests.options.design.description',
        color: 'purple',
      },
      {
        id: 'marketing',
        label: 'survey.questions.interests.options.marketing.label',
        icon: '📢',
        description: 'survey.questions.interests.options.marketing.description',
        color: 'orange',
      },
    ],
  },
  {
    id: '5',
    Question: 'survey.questions.goals.title',
    Question_type: 'single_option',
    subtitle: 'survey.questions.goals.subtitle',
    Question_data: [
      {
        id: 'learn',
        label: 'survey.questions.goals.options.learn.label',
        icon: '📚',
        description: 'survey.questions.goals.options.learn.description',
        color: 'blue',
      },
      {
        id: 'network',
        label: 'survey.questions.goals.options.network.label',
        icon: '🤝',
        description: 'survey.questions.goals.options.network.description',
        color: 'green',
      },
      {
        id: 'career',
        label: 'survey.questions.goals.options.career.label',
        icon: '🚀',
        description: 'survey.questions.goals.options.career.description',
        color: 'purple',
      },
      {
        id: 'business',
        label: 'survey.questions.goals.options.business.label',
        icon: '💼',
        description: 'survey.questions.goals.options.business.description',
        color: 'orange',
      },
    ],
  },
  {
    id: '6',
    Question: 'survey.questions.feedback.title',
    Question_type: 'sub_form',
    subtitle: 'survey.questions.feedback.subtitle',
    Question_data: [
      {
        id: '6-1',
        Question: 'survey.questions.feedback.subQuestions.0.title',
        Question_type: 'single_option',
        Question_data: [
          {
            id: 'excellent',
            label: 'survey.questions.feedback.subQuestions.0.options.excellent',
            icon: '⭐',
            color: 'green',
          },
          {
            id: 'good',
            label: 'survey.questions.feedback.subQuestions.0.options.good',
            icon: '👍',
            color: 'blue',
          },
          {
            id: 'average',
            label: 'survey.questions.feedback.subQuestions.0.options.average',
            icon: '👌',
            color: 'yellow',
          },
          {
            id: 'poor',
            label: 'survey.questions.feedback.subQuestions.0.options.poor',
            icon: '👎',
            color: 'red',
          },
        ],
      },
      {
        id: '6-2',
        Question: 'survey.questions.feedback.subQuestions.1.title',
        Question_type: 'single_option',
        Question_data: [
          {
            id: 'definitely',
            label: 'survey.questions.feedback.subQuestions.1.options.definitely',
            icon: '💯',
            color: 'green',
          },
          {
            id: 'probably',
            label: 'survey.questions.feedback.subQuestions.1.options.probably',
            icon: '✅',
            color: 'blue',
          },
          {
            id: 'maybe',
            label: 'survey.questions.feedback.subQuestions.1.options.maybe',
            icon: '🤔',
            color: 'yellow',
          },
          {
            id: 'unlikely',
            label: 'survey.questions.feedback.subQuestions.1.options.unlikely',
            icon: '❌',
            color: 'red',
          },
        ],
      },
    ],
  },
];

// API function to fetch questions
export async function fetchSurveyQuestions(): Promise<Question[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // In a real application, this would be an actual API call
  return mockSurveyQuestions;
}

// API function to submit survey responses
export async function submitSurveyResponse(responses: Record<number, unknown>): Promise<{ success: boolean; message: string }> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  console.log('Survey responses submitted:', responses);
  
  return {
    success: true,
    message: 'Survey submitted successfully!'
  };
}
