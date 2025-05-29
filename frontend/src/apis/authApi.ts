/* eslint-disable @typescript-eslint/no-explicit-any */
import axiosInstance from './axiosInstance';
import Cookies from 'js-cookie';
import { handleApiCall, handleApiCallNoData } from '../utils/apiHandler';
import type {
  UserResponse,
  RefreshTokenRequest,
  GoogleDirectLoginRequest,
  GoogleRevokeTokenRequest
} from "../types/auth.type";

const authApi = {
  /**
   * Set the authorization token for future requests
   */
  setToken: (token: string): void => {
    axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  },
  
  /**
   * Clear the authorization token
   */
  clearToken: (): void => {
    delete axiosInstance.defaults.headers.common['Authorization'];
  },

  /**
   * Get Google OAuth login page (HTML response)
   * GET /auth/google/login
   */
  getGoogleAuthUrl: async (login_hint?: string): Promise<string> => {
    console.log('API Call: getGoogleAuthUrl');
    try {
      const url = login_hint ? `/auth/google/login?login_hint=${encodeURIComponent(login_hint)}` : '/auth/google/login';
      // This endpoint returns HTML, not JSON
      const response = await axiosInstance.get(url, { 
        maxRedirects: 0,
        validateStatus: status => status >= 200 && status < 400
      });
      
      console.log('API Response: getGoogleAuthUrl', 'HTML received');
      return response.data;    
    } catch (error: unknown) {
      // If we get a redirect response, return the URL to redirect to
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        if (axiosError.response && axiosError.response.status === 302 && axiosError.response.headers.location) {
          return axiosError.response.headers.location;
        }
      }
      console.error('Error getting Google auth URL:', error);
      throw error;
    }
  },

  /**
   * Get Google OAuth redirect URL
   * GET /auth/google/auth
   */
  getGoogleAuthRedirect: async (login_hint?: string): Promise<string> => {
    console.log('API Call: getGoogleAuthRedirect');
    try {
      const url = login_hint ? `/auth/google/auth?login_hint=${encodeURIComponent(login_hint)}` : '/auth/google/auth';
      const response = await axiosInstance.get(url, { 
        maxRedirects: 0,
        validateStatus: status => status >= 200 && status < 400
      });
      
      // This should return a redirect
      if (response.headers.location) {
        return response.headers.location;
      }
      
      return response.data;    } catch (error: unknown) {
      // If we get a redirect response, return the URL to redirect to
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        if (axiosError.response && axiosError.response.status === 302 && axiosError.response.headers.location) {
          return axiosError.response.headers.location;
        }
      }
      console.error('Error getting Google auth redirect:', error);
      throw error;
    }
  },

  /**
   * Handle Google OAuth callback after user authorization
   * GET /auth/google/callback?code=...
   */
  handleGoogleCallback: async (code: string): Promise<UserResponse | null> => {
    console.log('API Call: handleGoogleCallback', { code: code.substring(0, 10) + '...' });
    
    return handleApiCall<UserResponse>(() => 
      axiosInstance.get(`/auth/google/callback?code=${encodeURIComponent(code)}`)
    );
  },

  /**
   * Direct Google login with access token
   * POST /auth/google/direct-login
   */
  googleDirectLogin: async (tokenData: GoogleDirectLoginRequest): Promise<UserResponse | null> => {
    console.log('API Call: googleDirectLogin');
    
    return handleApiCall<UserResponse>(() => 
      axiosInstance.post('/auth/google/direct-login', tokenData)
    );
  },

  /**
   * Refresh an expired authentication token
   * POST /auth/refresh
   */
  refreshToken: async (tokenData: RefreshTokenRequest): Promise<UserResponse | null> => {
    console.log('API Call: refreshToken');
    
    return handleApiCall<UserResponse>(() => 
      axiosInstance.post('/auth/refresh', { params: tokenData })
    );
  },

  /**
   * Revoke Google access token
   * POST /auth/google/revoke
   */
  revokeGoogleAccess: async (tokenRequest: GoogleRevokeTokenRequest): Promise<void> => {
    console.log('API Call: revokeGoogleAccess');
    
    // Ensure the Authorization header is properly set
    const accessToken = Cookies.get('access_token');
    if (accessToken) {
      authApi.setToken(accessToken);
    }
    
    return handleApiCallNoData(() => 
      axiosInstance.post('/auth/google/revoke', tokenRequest)
    );
  },

  /**
   * Get current authenticated user information
   * This endpoint returns detailed information about the current user
   */
  getMe: async (headers?: Record<string, string>): Promise<UserResponse | null> => {
    console.log('API Call: getMe with token', axiosInstance.defaults.headers.common['Authorization']);
    
    // Ensure the Authorization header is properly set
    const accessToken = Cookies.get('access_token');
    if (accessToken) {
      authApi.setToken(accessToken);
      console.log('API Call: getMe - Re-set Authorization header with token from cookies');
    }
    
    const config = headers ? { headers } : undefined;
    
    return handleApiCall<UserResponse>(() => 
      axiosInstance.get('/users/me', config)
    );
  },
};

export default authApi;