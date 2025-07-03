import axiosInstance from './axiosInstance';

export interface CVRegenResponse {
  success: boolean;
  message: string;
  cv_analysis?: any;
  pdf_file_url?: string;
  pdf_download_url?: string;
  file_size?: number;
  generation_time?: number;
  job_id?: string;
}

export interface ApiResponse<T> {
  error_code: number;
  message: string;
  data: T;
}

export const cvApi = {
  /**
   * Upload CV file và regenerate thành PDF
   */
  regenFromFile: async (
    file: File,
    templateType: string = 'modern',
    colorTheme: string = 'blue',
    customPrompt?: string
  ): Promise<ApiResponse<CVRegenResponse>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('template_type', templateType);
    formData.append('color_theme', colorTheme);
    
    if (customPrompt) {
      formData.append('custom_prompt', customPrompt);
    }

    const response = await axiosInstance.post('/cv/regen-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutes timeout for CV generation
    });

    return response.data;
  },

  /**
   * Process CV file để extract data
   */
  processFile: async (file: File): Promise<ApiResponse<any>> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axiosInstance.post('/cv/process-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }
}; 