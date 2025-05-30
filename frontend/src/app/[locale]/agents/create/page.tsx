'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CreateAgentPayload, Agent } from '@/types/agentTypes';
import { createAgent } from '@/apis/agentApi';
import AgentCreateForm from '@/components/agent/AgentCreateForm';

const CreateAgentPage: React.FC = () => {
  const router = useRouter();
  
  // Page state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Handle form submission
  const handleFormSubmit = async (formData: CreateAgentPayload) => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Create the agent
      const newAgent: Agent = await createAgent(formData);
      
      // Show success message
      setSuccessMessage(`Agent "${newAgent.name}" đã được tạo thành công!`);
      
      // Redirect to agent detail page or agents list after a short delay
      setTimeout(() => {
        router.push(`/agents/${newAgent.id}`);
        // Alternative: redirect to agents list
        // router.push('/agents');
      }, 2000);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      console.error('Failed to create agent:', error);
      setError(error.message || 'Có lỗi xảy ra khi tạo agent. Vui lòng thử lại.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <nav className="flex items-center text-sm text-gray-600 mb-4">
            <button
              onClick={() => router.push('/agents')}
              className="hover:text-blue-600 transition-colors"
            >
              Agents
            </button>
            <span className="mx-2">/</span>
            <span className="text-gray-900">Tạo mới</span>
          </nav>
          
          <h1 className="text-3xl font-bold text-gray-900">
            Tạo Agent Mới
          </h1>
          <p className="mt-2 text-gray-600">
            Tạo một AI agent mới để hỗ trợ công việc của bạn. Chọn loại agent phù hợp và cấu hình theo nhu cầu.
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-green-600">{successMessage}</p>
            </div>
            <p className="mt-1 text-xs text-green-500">
              Đang chuyển hướng đến trang chi tiết agent...
            </p>
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              Thông tin Agent
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              Điền thông tin cơ bản cho agent mới của bạn
            </p>
          </div>
          
          <div className="p-6">
            <AgentCreateForm
              onSubmit={handleFormSubmit}
              isLoading={isLoading}
              submissionError={error}
            />
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-4">
            💡 Hướng dẫn tạo Agent
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Loại Agent</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li><strong>Chat:</strong> Trợ lý AI cho cuộc trò chuyện thông thường</li>
                <li><strong>Phân tích:</strong> Chuyên về phân tích dữ liệu và báo cáo</li>
                <li><strong>Nhiệm vụ:</strong> Quản lý và thực hiện tác vụ cụ thể</li>
                <li><strong>Tùy chỉnh:</strong> Cấu hình linh hoạt theo nhu cầu</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Lưu ý</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Tên agent nên mô tả rõ chức năng</li>
                <li>• Để trống Config ID sẽ dùng cấu hình mặc định</li>
                <li>• Bạn có thể chỉnh sửa agent sau khi tạo</li>
                <li>• Agent mặc định sẽ được kích hoạt ngay</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAgentPage; 