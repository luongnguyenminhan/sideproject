'use client';

import {
  ArrowRight,
  Building,
  Check,
  ChevronLeft,
  Mail,
  MessageSquare,
  Phone,
  Search,
  Star,
  Target,
  User,
} from 'lucide-react';
import { useState } from 'react';

const Survey = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const questions = [
    {
      id: 1,
      title: 'What is your current role?',
      subtitle: 'Help us understand your professional background',
      layout: 'grid', // grid, list, or cards
      options: [
        {
          id: 'student',
          label: 'Student',
          icon: '🎓',
          description: 'Currently studying or learning',
          color: 'blue',
        },
        {
          id: 'professional',
          label: 'Professional',
          icon: '💼',
          description: 'Working in a company',
          color: 'purple',
        },
        {
          id: 'freelancer',
          label: 'Freelancer',
          icon: '🚀',
          description: 'Independent contractor',
          color: 'green',
        },
        {
          id: 'entrepreneur',
          label: 'Entrepreneur',
          icon: '💡',
          description: 'Building your own business',
          color: 'orange',
        },
      ],
    },
    {
      id: 2,
      title: 'Tell us about yourself',
      subtitle: 'Please provide some basic information',
      layout: 'input', // New layout type for text inputs
      options: [
        {
          id: 'fullName',
          label: 'Full Name',
          type: 'text',
          placeholder: 'John Doe',
          icon: <User className='w-5 h-5' />,
          required: true,
        },
        {
          id: 'email',
          label: 'Email Address',
          type: 'email',
          placeholder: 'john@example.com',
          icon: <Mail className='w-5 h-5' />,
          required: true,
        },
        {
          id: 'company',
          label: 'Company/Organization',
          type: 'text',
          placeholder: 'Acme Inc.',
          icon: <Building className='w-5 h-5' />,
          required: false,
        },
        {
          id: 'bio',
          label: 'Brief Bio',
          type: 'textarea',
          placeholder: 'Tell us a bit about your background and interests...',
          icon: <MessageSquare className='w-5 h-5' />,
          required: false,
          rows: 4,
        },
      ],
    },
    {
      id: 3,
      title: 'What programming languages do you use?',
      subtitle: 'Select all that apply to your current skillset',
      layout: 'list',
      multiple: true,
      options: [
        {
          id: 'javascript',
          label: 'JavaScript',
          icon: '🟨',
          description: 'Frontend and backend development',
          color: 'yellow',
        },
        {
          id: 'python',
          label: 'Python',
          icon: '🐍',
          description: 'Data science, AI, web development',
          color: 'blue',
        },
        {
          id: 'java',
          label: 'Java',
          icon: '☕',
          description: 'Enterprise applications',
          color: 'red',
        },
        {
          id: 'react',
          label: 'React',
          icon: '⚛️',
          description: 'Frontend framework',
          color: 'cyan',
        },
        {
          id: 'nodejs',
          label: 'Node.js',
          icon: '🟢',
          description: 'Backend JavaScript runtime',
          color: 'green',
        },
        {
          id: 'typescript',
          label: 'TypeScript',
          icon: '🔷',
          description: 'Typed JavaScript',
          color: 'blue',
        },
        {
          id: 'php',
          label: 'PHP',
          icon: '🐘',
          description: 'Server-side scripting',
          color: 'purple',
        },
        {
          id: 'csharp',
          label: 'C#',
          icon: '🔵',
          description: 'Microsoft ecosystem',
          color: 'indigo',
        },
        {
          id: 'swift',
          label: 'Swift',
          icon: '🦉',
          description: 'iOS development',
          color: 'orange',
        },
        {
          id: 'kotlin',
          label: 'Kotlin',
          icon: '🤖',
          description: 'Android development',
          color: 'green',
        },
      ],
    },
    {
      id: 4,
      title: 'What is your experience level?',
      subtitle: 'Be honest about your current expertise',
      layout: 'cards',
      options: [
        {
          id: 'beginner',
          label: 'Beginner',
          icon: '🌱',
          description: 'Just getting started (0-1 years)',
          color: 'green',
        },
        {
          id: 'intermediate',
          label: 'Intermediate',
          icon: '⭐',
          description: 'Some experience (1-3 years)',
          color: 'blue',
        },
        {
          id: 'experienced',
          label: 'Experienced',
          icon: '🏆',
          description: 'Solid experience (3-5 years)',
          color: 'purple',
        },
        {
          id: 'expert',
          label: 'Expert',
          icon: '👑',
          description: 'Deep expertise (5+ years)',
          color: 'gold',
        },
      ],
    },
    {
      id: 5,
      title: 'Which tools do you use regularly?',
      subtitle: 'Select all your frequently used development tools',
      layout: 'grid',
      multiple: true,
      options: [
        { id: 'vscode', label: 'VS Code', icon: '📝', description: 'Code editor', color: 'blue' },
        {
          id: 'github',
          label: 'GitHub',
          icon: '🐙',
          description: 'Version control',
          color: 'gray',
        },
        {
          id: 'docker',
          label: 'Docker',
          icon: '🐳',
          description: 'Containerization',
          color: 'blue',
        },
        { id: 'aws', label: 'AWS', icon: '☁️', description: 'Cloud platform', color: 'orange' },
        { id: 'figma', label: 'Figma', icon: '🎨', description: 'Design tool', color: 'purple' },
        {
          id: 'postman',
          label: 'Postman',
          icon: '📮',
          description: 'API testing',
          color: 'orange',
        },
        { id: 'slack', label: 'Slack', icon: '💬', description: 'Communication', color: 'purple' },
        { id: 'jira', label: 'Jira', icon: '📋', description: 'Project management', color: 'blue' },
        { id: 'notion', label: 'Notion', icon: '📚', description: 'Documentation', color: 'gray' },
        { id: 'mongodb', label: 'MongoDB', icon: '🍃', description: 'Database', color: 'green' },
        { id: 'redis', label: 'Redis', icon: '🔴', description: 'Caching', color: 'red' },
        { id: 'webpack', label: 'Webpack', icon: '📦', description: 'Bundler', color: 'blue' },
      ],
    },
    {
      id: 6,
      title: 'Additional feedback',
      subtitle: 'We value your thoughts and suggestions',
      layout: 'input',
      options: [
        {
          id: 'improvements',
          label: 'What improvements would you like to see?',
          type: 'textarea',
          placeholder: 'Share your ideas for improvements...',
          icon: <Star className='w-5 h-5' />,
          required: false,
          rows: 3,
        },
        {
          id: 'challenges',
          label: 'What are your biggest challenges as a developer?',
          type: 'textarea',
          placeholder: 'Describe the challenges you face...',
          icon: <Target className='w-5 h-5' />,
          required: false,
          rows: 3,
        },
        {
          id: 'other',
          label: "Anything else you'd like to share?",
          type: 'textarea',
          placeholder: 'Feel free to share any additional thoughts...',
          icon: <MessageSquare className='w-5 h-5' />,
          required: false,
          rows: 4,
        },
      ],
    },
    {
      id: 7,
      title: 'What motivates you most in your work?',
      subtitle: 'Choose your primary drivers and values',
      layout: 'list',
      multiple: true,
      options: [
        {
          id: 'learning',
          label: 'Continuous Learning',
          icon: '📚',
          description: 'Growing skills and knowledge',
          color: 'blue',
        },
        {
          id: 'impact',
          label: 'Making Impact',
          icon: '🌟',
          description: 'Creating meaningful change',
          color: 'purple',
        },
        {
          id: 'creativity',
          label: 'Creative Expression',
          icon: '🎨',
          description: 'Building beautiful solutions',
          color: 'pink',
        },
        {
          id: 'collaboration',
          label: 'Team Collaboration',
          icon: '🤝',
          description: 'Working with great people',
          color: 'green',
        },
        {
          id: 'innovation',
          label: 'Innovation',
          icon: '💡',
          description: 'Pushing boundaries',
          color: 'orange',
        },
        {
          id: 'stability',
          label: 'Job Security',
          icon: '🛡️',
          description: 'Stable career path',
          color: 'blue',
        },
        {
          id: 'flexibility',
          label: 'Work Flexibility',
          icon: '⚖️',
          description: 'Work-life balance',
          color: 'teal',
        },
        {
          id: 'leadership',
          label: 'Leadership',
          icon: '👑',
          description: 'Leading teams and projects',
          color: 'purple',
        },
      ],
    },
  ];

  const progress = ((currentStep + 1) / questions.length) * 100;

  const handleAnswerSelect = (questionId, answerId, value = null) => {
    const question = questions.find(q => q.id === questionId);

    if (question.layout === 'input') {
      // For text inputs, store the value directly
      setSelectedAnswers({
        ...selectedAnswers,
        [questionId]: {
          ...selectedAnswers[questionId],
          [answerId]: value,
        },
      });
    } else if (question.multiple) {
      const currentAnswers = selectedAnswers[questionId] || [];
      const isSelected = currentAnswers.includes(answerId);

      if (isSelected) {
        setSelectedAnswers({
          ...selectedAnswers,
          [questionId]: currentAnswers.filter(id => id !== answerId),
        });
      } else {
        setSelectedAnswers({
          ...selectedAnswers,
          [questionId]: [...currentAnswers, answerId],
        });
      }
    } else {
      setSelectedAnswers({
        ...selectedAnswers,
        [questionId]: answerId,
      });
    }
  };

  const handleNext = () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setShowResults(true);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const getColorClasses = (color, isSelected = false) => {
    const colors = {
      blue: isSelected
        ? 'bg-blue-500 text-white border-blue-500'
        : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
      purple: isSelected
        ? 'bg-purple-500 text-white border-purple-500'
        : 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
      green: isSelected
        ? 'bg-green-500 text-white border-green-500'
        : 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
      orange: isSelected
        ? 'bg-orange-500 text-white border-orange-500'
        : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
      red: isSelected
        ? 'bg-red-500 text-white border-red-500'
        : 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
      yellow: isSelected
        ? 'bg-yellow-500 text-white border-yellow-500'
        : 'bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100',
      pink: isSelected
        ? 'bg-pink-500 text-white border-pink-500'
        : 'bg-pink-50 text-pink-700 border-pink-200 hover:bg-pink-100',
      cyan: isSelected
        ? 'bg-cyan-500 text-white border-cyan-500'
        : 'bg-cyan-50 text-cyan-700 border-cyan-200 hover:bg-cyan-100',
      indigo: isSelected
        ? 'bg-indigo-500 text-white border-indigo-500'
        : 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100',
      teal: isSelected
        ? 'bg-teal-500 text-white border-teal-500'
        : 'bg-teal-50 text-teal-700 border-teal-200 hover:bg-teal-100',
      gray: isSelected
        ? 'bg-gray-500 text-white border-gray-500'
        : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100',
      gold: isSelected
        ? 'bg-yellow-600 text-white border-yellow-600'
        : 'bg-yellow-50 text-yellow-800 border-yellow-200 hover:bg-yellow-100',
    };
    return colors[color] || colors.blue;
  };

  const renderOptions = question => {
    const currentAnswers = question.multiple
      ? selectedAnswers[question.id] || []
      : selectedAnswers[question.id];

    // Input layout for text inputs
    if (question.layout === 'input') {
      const inputValues = selectedAnswers[question.id] || {};

      return (
        <div className='space-y-6 max-w-2xl mx-auto'>
          {question.options.map(option => (
            <div key={option.id} className='group'>
              <label className='block text-sm font-semibold text-gray-700 mb-2'>
                <div className='flex items-center space-x-2'>
                  <span className='text-blue-600'>{option.icon}</span>
                  <span>{option.label}</span>
                  {option.required && <span className='text-red-500'>*</span>}
                </div>
              </label>
              {option.type === 'textarea' ? (
                <textarea
                  value={inputValues[option.id] || ''}
                  onChange={e => handleAnswerSelect(question.id, option.id, e.target.value)}
                  placeholder={option.placeholder}
                  rows={option.rows || 3}
                  className='w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 resize-none'
                />
              ) : (
                <input
                  type={option.type || 'text'}
                  value={inputValues[option.id] || ''}
                  onChange={e => handleAnswerSelect(question.id, option.id, e.target.value)}
                  placeholder={option.placeholder}
                  className='w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300'
                />
              )}
            </div>
          ))}
        </div>
      );
    }

    if (question.layout === 'grid') {
      const cols =
        question.options.length <= 4
          ? 'grid-cols-2 md:grid-cols-4'
          : question.options.length <= 6
          ? 'grid-cols-2 md:grid-cols-3'
          : 'grid-cols-2 md:grid-cols-4 lg:grid-cols-6';

      return (
        <div className={`grid ${cols} gap-4`}>
          {question.options.map(option => {
            const isSelected = question.multiple
              ? currentAnswers.includes(option.id)
              : currentAnswers === option.id;
            return (
              <div
                key={option.id}
                onClick={() => handleAnswerSelect(question.id, option.id)}
                className={`
                  relative cursor-pointer rounded-2xl p-6 text-center transition-all duration-300 border-2 group
                  ${getColorClasses(option.color, isSelected)}
                  ${
                    isSelected
                      ? 'transform scale-105 shadow-lg'
                      : 'hover:shadow-md hover:-translate-y-1'
                  }
                `}
              >
                <div className='text-3xl mb-3 transition-transform duration-300 group-hover:scale-110'>
                  {option.icon}
                </div>
                <div className='font-semibold text-lg mb-1'>{option.label}</div>
                <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
                  {option.description}
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

    if (question.layout === 'list') {
      return (
        <div className='space-y-3 max-h-96 overflow-y-auto'>
          {question.options.map(option => {
            const isSelected = question.multiple
              ? currentAnswers.includes(option.id)
              : currentAnswers === option.id;
            return (
              <div
                key={option.id}
                onClick={() => handleAnswerSelect(question.id, option.id)}
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
                  <div className='font-semibold text-lg'>{option.label}</div>
                  <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
                    {option.description}
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
    }

    // Cards layout (default)
    return (
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
        {question.options.map(option => {
          const isSelected = question.multiple
            ? currentAnswers.includes(option.id)
            : currentAnswers === option.id;
          return (
            <div
              key={option.id}
              onClick={() => handleAnswerSelect(question.id, option.id)}
              className={`
                relative cursor-pointer rounded-2xl p-8 text-center transition-all duration-300 border-2 group
                ${getColorClasses(option.color, isSelected)}
                ${
                  isSelected
                    ? 'transform scale-105 shadow-xl'
                    : 'hover:shadow-lg hover:-translate-y-2'
                }
              `}
            >
              <div className='text-4xl mb-4 transition-transform duration-300 group-hover:scale-110'>
                {option.icon}
              </div>
              <div className='font-bold text-xl mb-2'>{option.label}</div>
              <div className={`text-sm opacity-80 ${isSelected ? 'text-white' : ''}`}>
                {option.description}
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

  const isQuestionAnswered = question => {
    const answers = selectedAnswers[question.id];

    if (question.layout === 'input') {
      // For input questions, check if all required fields are filled
      const inputValues = answers || {};
      return question.options.every(option => {
        if (option.required) {
          return inputValues[option.id] && inputValues[option.id].trim() !== '';
        }
        return true;
      });
    }

    if (question.multiple) {
      return answers && answers.length > 0;
    }
    return answers !== undefined;
  };

  if (showResults) {
    return (
      <div className='min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100'>
        <div className='container mx-auto px-4 py-8'>
          <div className='text-center mb-12'>
            <div className='inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium mb-4'>
              <Check className='w-4 h-4' />
              <span>Survey Complete</span>
            </div>
            <h1 className='text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 bg-clip-text text-transparent mb-4'>
              Thank You!
            </h1>
            <p className='text-xl text-gray-600 max-w-2xl mx-auto'>
              Your responses have been recorded. Here's what you selected:
            </p>
          </div>

          {/* Results Summary */}
          <div className='max-w-4xl mx-auto bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl border border-white/20 mb-8'>
            <h3 className='text-2xl font-bold text-gray-900 mb-6'>Your Selections</h3>
            <div className='space-y-6'>
              {Object.entries(selectedAnswers).map(([questionId, answers]) => {
                const question = questions.find(q => q.id === parseInt(questionId));

                if (question.layout === 'input') {
                  // Display text input answers
                  return (
                    <div key={questionId} className='border-b border-gray-200 pb-4 last:border-b-0'>
                      <h4 className='font-semibold text-lg text-gray-900 mb-3'>{question.title}</h4>
                      <div className='space-y-2'>
                        {Object.entries(answers).map(([fieldId, value]) => {
                          const option = question.options.find(opt => opt.id === fieldId);
                          if (!value) return null;
                          return (
                            <div key={fieldId} className='bg-gray-50 rounded-lg p-3'>
                              <div className='font-medium text-sm text-gray-600 mb-1'>
                                {option.label}:
                              </div>
                              <div className='text-gray-900'>{value}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                }

                // Display multiple choice answers
                const answerArray = Array.isArray(answers) ? answers : [answers];
                return (
                  <div key={questionId} className='border-b border-gray-200 pb-4 last:border-b-0'>
                    <h4 className='font-semibold text-lg text-gray-900 mb-3'>{question.title}</h4>
                    <div className='flex flex-wrap gap-2'>
                      {answerArray.map(answerId => {
                        const option = question.options.find(opt => opt.id === answerId);
                        return (
                          <div
                            key={answerId}
                            className={`inline-flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium ${getColorClasses(
                              option.color,
                              true,
                            )}`}
                          >
                            <span>{option.icon}</span>
                            <span>{option.label}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className='text-center'>
            <button
              onClick={() => {
                setShowResults(false);
                setCurrentStep(0);
                setSelectedAnswers({});
              }}
              className='bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1'
            >
              Take Survey Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentStep];

  return (
    <div className='min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100'>
      <div className='container mx-auto px-4 py-8'>
        {/* Header */}
        {/* Header */}
        <div className='bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl border border-white/20 p-6 mb-8'>
          <div className='flex justify-between items-center'>
            <div className='text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
              DEVELOPER SURVEY
            </div>
            <div className='hidden md:flex space-x-8 text-sm text-gray-600 font-medium'>
              <span className='hover:text-blue-600 cursor-pointer transition-colors'>HOME</span>
              <span className='hover:text-blue-600 cursor-pointer transition-colors'>SURVEYS</span>
              <span className='hover:text-blue-600 cursor-pointer transition-colors'>
                ANALYTICS
              </span>
              <span className='hover:text-blue-600 cursor-pointer transition-colors'>
                COMMUNITY
              </span>
              <span className='hover:text-blue-600 cursor-pointer transition-colors'>HELP</span>
            </div>
            <div className='flex items-center space-x-4'>
              <Search className='w-5 h-5 text-gray-400 cursor-pointer hover:text-blue-600 transition-colors' />
              <div className='flex items-center space-x-2 text-sm text-gray-600 font-medium cursor-pointer hover:text-blue-600 transition-colors'>
                <Phone className='w-4 h-4' />
                <span>CONTACT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Survey Card */}
        <div className='max-w-6xl mx-auto'>
          <div className='bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 p-8 md:p-12'>
            {/* Progress Indicator */}
            <div className='flex justify-center mb-12'>
              <div className='flex items-center space-x-4'>
                {questions.map((_, index) => (
                  <div key={index} className='flex items-center'>
                    <div
                      className={`
                      w-12 h-12 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-300
                      ${
                        index < currentStep
                          ? 'bg-green-500 text-white'
                          : index === currentStep
                          ? 'bg-blue-600 text-white ring-4 ring-blue-200 shadow-lg'
                          : 'bg-gray-200 text-gray-500'
                      }
                    `}
                    >
                      {index < currentStep ? <Check className='w-6 h-6' /> : index + 1}
                    </div>
                    {index < questions.length - 1 && (
                      <div
                        className={`
                        w-16 h-1 mx-2 rounded-full transition-all duration-300
                        ${index < currentStep ? 'bg-green-500' : 'bg-gray-200'}
                      `}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Question Header */}
            <div className='text-center mb-12'>
              <div className='inline-flex items-center space-x-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6'>
                <span>
                  Question {currentStep + 1} of {questions.length}
                </span>
                {currentQuestion.multiple && <span>• Multiple Choice</span>}
              </div>
              <h1 className='text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 bg-clip-text text-transparent mb-4'>
                {currentQuestion.title}
              </h1>
              <p className='text-xl text-gray-600 max-w-3xl mx-auto'>{currentQuestion.subtitle}</p>
            </div>

            {/* Options */}
            <div className='mb-12'>{renderOptions(currentQuestion)}</div>

            {/* Navigation */}
            <div className='flex justify-between items-center mb-8'>
              <button
                onClick={handleBack}
                disabled={currentStep === 0}
                className={`
                  flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300
                  ${
                    currentStep === 0
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }
                `}
              >
                <ChevronLeft className='w-5 h-5' />
                <span>Previous</span>
              </button>

              <button
                onClick={handleNext}
                disabled={!isQuestionAnswered(currentQuestion)}
                className={`
                  flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold transition-all duration-300 transform
                  ${
                    isQuestionAnswered(currentQuestion)
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 hover:shadow-xl hover:-translate-y-1'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }
                `}
              >
                <span>{currentStep === questions.length - 1 ? 'Complete Survey' : 'Continue'}</span>
                <ArrowRight className='w-5 h-5' />
              </button>
            </div>

            {/* Progress Bar */}
            <div className='space-y-3'>
              <div className='flex justify-between text-sm font-medium text-gray-600'>
                <span>Progress</span>
                <span>{Math.round(progress)}% Complete</span>
              </div>
              <div className='w-full bg-gray-200 rounded-full h-4 overflow-hidden'>
                <div
                  className='bg-gradient-to-r from-blue-600 to-purple-600 h-full rounded-full transition-all duration-700 ease-out relative'
                  style={{ width: `${progress}%` }}
                >
                  <div className='absolute inset-0 bg-white/20 rounded-full animate-pulse'></div>
                </div>
              </div>
              <div className='text-center text-sm text-gray-500 mt-2'>
                {currentStep + 1} of {questions.length} questions completed
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Survey;
