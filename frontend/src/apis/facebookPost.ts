import axiosInstance from './axiosInstance';
import { handleApiCall } from '../utils/apiHandler';
import {
  FacebookPageResponse,
  GetPageInfoRequest,
  FacebookPageInfo
} from '../types/facebook.type';

const facebookPostApi = {
  /**
   * Get Facebook page info with posts
   * @param params - Request parameters including optional limit
   * @returns Promise<FacebookPageInfo | null> - Page info with posts data
   */
  getPageInfoWithPosts: async (params?: GetPageInfoRequest): Promise<FacebookPageInfo | null> => {
    console.log('API Call: getPageInfoWithPosts', params);
    
    return handleApiCall<FacebookPageInfo>(() => 
      axiosInstance.get<FacebookPageResponse>('/facebook-graph/page-info', { params })
    );
  },
};

export default facebookPostApi;