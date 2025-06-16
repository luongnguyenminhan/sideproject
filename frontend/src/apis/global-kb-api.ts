import axiosInstance from './axiosInstance';
import type {
  AdminDocumentData,
  SearchGlobalKBRequest,
  GlobalKBResponse,
  GetGlobalKBStatsResponse,
  UploadGlobalKBFileResponse,
  ApiResponse,
} from '@/types/global-kb.type';

export const globalKBAPI = {
  // List all documents
  list: async (): Promise<ApiResponse<GlobalKBResponse[]>> => {
    const response = await axiosInstance.get('/global-kb/');
    return response.data;
  },

  // Get a single document
  get: async (docId: string): Promise<ApiResponse<GlobalKBResponse>> => {
    const response = await axiosInstance.get(`/global-kb/${docId}`);
    return response.data;
  },

  // Create a document
  create: async (data: AdminDocumentData): Promise<ApiResponse<GlobalKBResponse>> => {
    const response = await axiosInstance.post('/global-kb/', data);
    return response.data;
  },

  // Update a document
  update: async (docId: string, data: Partial<AdminDocumentData>): Promise<ApiResponse<GlobalKBResponse>> => {
    const response = await axiosInstance.put(`/global-kb/${docId}`, data);
    return response.data;
  },

  // Delete a document
  delete: async (docId: string): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete(`/global-kb/${docId}`);
    return response.data;
  },

  // Search Global Knowledge Base
  search: async (
    data: SearchGlobalKBRequest
  ): Promise<ApiResponse<GlobalKBResponse[]>> => {
    const response = await axiosInstance.post('/global-kb/search', data);
    return response.data;
  },

  // Get Global KB Statistics
  getStats: async (): Promise<GetGlobalKBStatsResponse> => {
    const response = await axiosInstance.get('/global-kb/stats');
    return response.data;
  },

  // Upload file to Global KB
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

  // Delete file/document from Global KB
  deleteFile: async (docId: string): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete(`/global-kb/file/${docId}`);
    return response.data;
  },
};