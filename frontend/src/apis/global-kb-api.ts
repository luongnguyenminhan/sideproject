import axiosInstance from './axiosInstance';
import type {
  IndexAdminDocumentsRequest,
  SearchGlobalKBRequest,
  InitializeGlobalKBRequest,
  IndexAdminDocumentsResponse,
  SearchGlobalKBResponse,
  InitializeGlobalKBResponse,
  GetGlobalKBStatsResponse,
  UploadGlobalKBFileResponse,
} from '@/types/global-kb.type';

export const globalKBAPI = {
  // Initialize Global Knowledge Base
  initialize: async (
    data: InitializeGlobalKBRequest
  ): Promise<InitializeGlobalKBResponse> => {
    const response = await axiosInstance.post('/global-kb/initialize', data);
    return response.data;
  },

  // Index Admin Documents
  indexAdminDocuments: async (
    data: IndexAdminDocumentsRequest
  ): Promise<IndexAdminDocumentsResponse> => {
    const response = await axiosInstance.post('/global-kb/admin-documents', data);
    return response.data;
  },

  // Search Global Knowledge Base
  search: async (
    data: SearchGlobalKBRequest
  ): Promise<SearchGlobalKBResponse> => {
    const response = await axiosInstance.post('/global-kb/search', data);
    return response.data;
  },

  // Get Global KB Statistics
  getStats: async (): Promise<GetGlobalKBStatsResponse> => {
    const response = await axiosInstance.get('/global-kb/stats');
    return response.data;
  },

  // Upload file to Global KB (admin)
  uploadFile: async (file: File, title?: string, category?: string, tags?: string[]): Promise<UploadGlobalKBFileResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (category) formData.append('category', category);
    if (tags) formData.append('tags', tags.join(','));
    const response = await axiosInstance.post('/global-kb/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    if (response.data.error_code === 0) {
      return response.data.data as UploadGlobalKBFileResponse;
    } else {
      throw new Error(response.data.message || 'File upload failed');
    }
  },

  // Xóa file/document khỏi Global KB
  deleteFile: async (docId: string) => {
    const response = await axiosInstance.delete(`/global-kb/file/${docId}`);
    return response.data;
  },
};