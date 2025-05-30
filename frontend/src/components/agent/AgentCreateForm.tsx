'use client';

import React, { useState, useEffect } from 'react';
import { CreateAgentPayload, AgentType, AgentFormErrors, DefaultConfigTemplate } from '@/types/agentTypes';
import { getDefaultTemplate } from '@/apis/agentApi';

interface AgentCreateFormProps {
  onSubmit: (formData: CreateAgentPayload) => Promise<void>;
  isLoading?: boolean;
  submissionError?: string | null;
}

const AgentCreateForm: React.FC<AgentCreateFormProps> = ({
  onSubmit,
  isLoading = false,
  submissionError = null,
}) => {
  // Form state
  const [formData, setFormData] = useState<CreateAgentPayload>({
    name: '',
    description: '',
    agent_type: AgentType.CHAT,
    config_id: '',
  });

  // Validation errors
  const [errors, setErrors] = useState<AgentFormErrors>({});

  // Template info for selected agent type
  const [template, setTemplate] = useState<DefaultConfigTemplate | null>(null);
  const [loadingTemplate, setLoadingTemplate] = useState(false);

  // Load template when agent type changes
  useEffect(() => {
    const loadTemplate = async () => {
      if (!formData.agent_type) return;
      
      setLoadingTemplate(true);
      try {
        const templateData = await getDefaultTemplate(formData.agent_type);
        setTemplate(templateData);
      } catch (error) {
        console.error('Failed to load template:', error);
      } finally {
        setLoadingTemplate(false);
      }
    };

    loadTemplate();
  }, [formData.agent_type]);

  // Agent type options with labels
  const agentTypeOptions = [
    { value: AgentType.CHAT, label: 'Chat', description: 'Trợ lý AI cho cuộc trò chuyện thông thường' },
    { value: AgentType.ANALYSIS, label: 'Phân tích', description: 'Agent chuyên về phân tích dữ liệu và báo cáo' },
    { value: AgentType.TASK, label: 'Nhiệm vụ', description: 'Agent quản lý và thực hiện các tác vụ cụ thể' },
    { value: AgentType.CUSTOM, label: 'Tùy chỉnh', description: 'Agent tùy chỉnh với cấu hình linh hoạt' },
  ];

  // Validation function
  const validateForm = (): boolean => {
    const newErrors: AgentFormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Tên agent là bắt buộc';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Tên agent phải có ít nhất 2 ký tự';
    }

    if (!formData.agent_type) {
      newErrors.agent_type = 'Vui lòng chọn loại agent';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      // Error will be handled by parent component
    }
  };

  // Handle input changes
  const handleInputChange = (field: keyof CreateAgentPayload, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof AgentFormErrors]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Agent Name */}
        <div>
          <label htmlFor="agent-name" className="block text-sm font-medium text-gray-700 mb-2">
            Tên Agent *
          </label>
          <input
            id="agent-name"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Nhập tên cho agent của bạn"
            disabled={isLoading}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name}</p>
          )}
        </div>

        {/* Agent Type */}
        <div>
          <label htmlFor="agent-type" className="block text-sm font-medium text-gray-700 mb-2">
            Loại Agent *
          </label>
          <select
            id="agent-type"
            value={formData.agent_type}
            onChange={(e) => handleInputChange('agent_type', e.target.value as AgentType)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.agent_type ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isLoading}
          >
            {agentTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {errors.agent_type && (
            <p className="mt-1 text-sm text-red-600">{errors.agent_type}</p>
          )}
          
          {/* Show description for selected agent type */}
          {formData.agent_type && (
            <p className="mt-1 text-sm text-gray-600">
              {agentTypeOptions.find(opt => opt.value === formData.agent_type)?.description}
            </p>
          )}
        </div>

        {/* Template Info */}
        {template && !loadingTemplate && (
          <div className="bg-blue-50 p-4 rounded-md">
            <h4 className="font-medium text-blue-900 mb-2">Cấu hình mặc định</h4>
            <p className="text-sm text-blue-800 mb-2">{template.description}</p>
            <div className="text-xs text-blue-700">
              <p><strong>Mô hình:</strong> {template.template.model_provider} - {template.template.model_name}</p>
              <p><strong>Nhiệt độ:</strong> {template.template.temperature}</p>
              <p><strong>Tối đa tokens:</strong> {template.template.max_tokens}</p>
            </div>
            {template.recommended_use_cases.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-blue-700">Ứng dụng được đề xuất:</p>
                <ul className="text-xs text-blue-600 list-disc list-inside">
                  {template.recommended_use_cases.map((useCase, index) => (
                    <li key={index}>{useCase}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {loadingTemplate && (
          <div className="bg-gray-50 p-4 rounded-md">
            <p className="text-sm text-gray-600">Đang tải thông tin cấu hình...</p>
          </div>
        )}

        {/* Agent Description */}
        <div>
          <label htmlFor="agent-description" className="block text-sm font-medium text-gray-700 mb-2">
            Mô tả Agent (Tùy chọn)
          </label>
          <textarea
            id="agent-description"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Mô tả về agent này và cách sử dụng"
            disabled={isLoading}
          />
        </div>

        {/* Config ID (Optional) */}
        <div>
          <label htmlFor="config-id" className="block text-sm font-medium text-gray-700 mb-2">
            ID Cấu hình (Tùy chọn)
          </label>
          <input
            id="config-id"
            type="text"
            value={formData.config_id}
            onChange={(e) => handleInputChange('config_id', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Để trống để sử dụng cấu hình mặc định"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Để trống để sử dụng cấu hình mặc định cho loại agent đã chọn
          </p>
        </div>

        {/* Submission Error */}
        {submissionError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{submissionError}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
            disabled={isLoading}
          >
            Hủy
          </button>
          <button
            type="submit"
            disabled={isLoading || !formData.name.trim() || !formData.agent_type}
            className={`px-6 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              isLoading || !formData.name.trim() || !formData.agent_type
                ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang tạo...
              </span>
            ) : (
              'Tạo Agent'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentCreateForm; 