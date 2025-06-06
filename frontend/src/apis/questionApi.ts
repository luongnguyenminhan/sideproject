import { Question } from '@/types/question.types';

// Mock data for survey questions
export const mockSurveyQuestions: Question[] = [
  {
    id: '1',
    Question: 'Bạn hiện tại đang là gì?',
    Question_type: 'single_option',
    subtitle: 'Chọn vai trò phù hợp nhất với bạn',
    Question_data: [
      {
        id: 'student',
        label: 'Sinh viên',
      },
      {
        id: 'professional',
        label: 'Nhân viên công ty',
      },
      {
        id: 'freelancer',
        label: 'Freelancer',
      },
      {
        id: 'entrepreneur',
        label: 'Doanh nhân',
      },
      {
        id: 'student_2',
        label: 'Sinh viên',
      },
      {
        id: 'professional_2',
        label: 'Nhân viên công ty',
      },
      {
        id: 'freelancer_2',
        label: 'Freelancer',
      },
      {
        id: 'entrepreneur_2',
        label: 'Doanh nhân',
      },
      {
        id: 'student_3',
        label: 'Sinh viên',
      },
      {
        id: 'professional_3',
        label: 'Nhân viên công ty',
      },
      {
        id: 'freelancer_3',
        label: 'Freelancer',
      },
      {
        id: 'entrepreneur_3',
        label: 'Doanh nhân',
      },
    ],
  },
  {
    id: '2',
    Question: 'Bạn có kỹ năng gì?',
    Question_type: 'multiple_choice',
    subtitle: 'Chọn tất cả các kỹ năng bạn biết',
    Question_data: [
      { id: 'javascript', label: 'JavaScript' },
      { id: 'typescript', label: 'TypeScript' },
      { id: 'react', label: 'React' },
      { id: 'nodejs', label: 'Node.js' },
      { id: 'python', label: 'Python' },
      { id: 'java', label: 'Java' },
      { id: 'csharp', label: 'C#' },
      { id: 'cpp', label: 'C++' },
      { id: 'html', label: 'HTML' },
      { id: 'css', label: 'CSS' },
      { id: 'angular', label: 'Angular' },
      { id: 'vue', label: 'Vue.js' },
      { id: 'nextjs', label: 'Next.js' },
      { id: 'express', label: 'Express.js' },
      { id: 'mongodb', label: 'MongoDB' },
      { id: 'mysql', label: 'MySQL' },
      { id: 'postgresql', label: 'PostgreSQL' },
      { id: 'docker', label: 'Docker' },
      { id: 'kubernetes', label: 'Kubernetes' },
      { id: 'aws', label: 'AWS' },
      { id: 'git', label: 'Git' },
      { id: 'figma', label: 'Figma' },
      { id: 'photoshop', label: 'Photoshop' },
      { id: 'flutter', label: 'Flutter' },
    ],
  },
  {
    id: '3',
    Question: 'Thông tin cá nhân',
    Question_type: 'text_input',
    subtitle: 'Vui lòng nhập thông tin của bạn',
    Question_data: [
      {
        id: 'fullName',
        label: 'Họ và tên',
        type: 'text',
        placeholder: 'Nguyễn Văn A',
        required: true,
      },
      {
        id: 'email',
        label: 'Email',
        type: 'email',
        placeholder: 'example@email.com',
        required: true,
      },
      {
        id: 'phone',
        label: 'Số điện thoại',
        type: 'tel',
        placeholder: '0123456789',
        required: false,
      },
      {
        id: 'company',
        label: 'Công ty',
        type: 'text',
        placeholder: 'Tên công ty của bạn',
        required: false,
      },
    ],
  },
  {
    id: '4',
    Question: 'Bạn quan tâm về lĩnh vực nào?',
    Question_type: 'multiple_choice',
    subtitle: 'Chọn các lĩnh vực bạn quan tâm',
    Question_data: [
      { id: 'javascript', label: 'JavaScript' },
      { id: 'typescript', label: 'TypeScript' },
      { id: 'react', label: 'React' },
      { id: 'nodejs', label: 'Node.js' },
      { id: 'python', label: 'Python' },
      { id: 'java', label: 'Java' },
      { id: 'csharp', label: 'C#' },
      { id: 'cpp', label: 'C++' },
      { id: 'html', label: 'HTML' },
      { id: 'css', label: 'CSS' },
      { id: 'angular', label: 'Angular' },
      { id: 'vue', label: 'Vue.js' },
      { id: 'nextjs', label: 'Next.js' },
      { id: 'express', label: 'Express.js' },
      { id: 'mongodb', label: 'MongoDB' },
      { id: 'mysql', label: 'MySQL' },
    ],
  },
  {
    id: '5',
    Question: 'Mục tiêu của bạn là gì?',
    Question_type: 'single_option',
    subtitle: 'Chọn mục tiêu chính của bạn',
    Question_data: [
      { id: 'learn', label: 'Học hỏi kiến thức mới' },
      { id: 'network', label: 'Mở rộng mối quan hệ' },
      { id: 'career', label: 'Phát triển sự nghiệp' },
      { id: 'business', label: 'Khởi nghiệp kinh doanh' },
    ],
  },
  {
    id: '6',
    Question: 'Đánh giá phản hồi',
    Question_type: 'sub_form',
    subtitle: 'Vui lòng cho chúng tôi biết ý kiến của bạn',
    Question_data: [
      {
        id: '6-1',
        Question: 'Bạn cảm thấy thế nào về khảo sát này?',
        Question_type: 'single_option',
        Question_data: [
          { id: 'excellent', label: 'Rất tốt' },
          { id: 'good', label: 'Tốt' },
          { id: 'average', label: 'Bình thường' },
          { id: 'poor', label: 'Chưa tốt' },
        ],
      },
      {
        id: '6-2',
        Question: 'Bạn có muốn tham gia các khảo sát khác không?',
        Question_type: 'single_option',
        Question_data: [
          { id: 'definitely', label: 'Chắc chắn sẽ tham gia' },
          { id: 'probably', label: 'Có thể sẽ tham gia' },
          { id: 'maybe', label: 'Chưa chắc chắn' },
          { id: 'unlikely', label: 'Không muốn tham gia' },
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
