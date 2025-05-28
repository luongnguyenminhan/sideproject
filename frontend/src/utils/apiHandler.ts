import { AxiosResponse, AxiosError } from 'axios';
import { CommonResponse } from '../types/common.type';

/**
 * Custom error class for API errors
 */
export class ApiException extends Error {
  public readonly status: number;
  public readonly error_code: number;
  public readonly errors?: Record<string, string[]>;

  constructor(status: number, error_code: number, message: string, errors?: Record<string, string[]>) {
    super(message);
    this.name = 'ApiException';
    this.status = status;
    this.error_code = error_code;
    this.errors = errors;
  }
}

/**
 * Generic API handler that processes responses and handles errors
 * @param apiCall - The API call function that returns a Promise<AxiosResponse>
 * @returns Promise<T> - Returns the data if successful, throws ApiException if error
 */
export async function handleApiCall<T>(
  apiCall: () => Promise<AxiosResponse<CommonResponse<T>>>
): Promise<T | null> {
  try {
    const response = await apiCall();
    const data: CommonResponse<T> = response.data;

    // Check if API returned an error (error_code = 1 means error, error_code = 0 means success)
    if (data.error_code !== 0) {
      throw new ApiException(
        response.status,
        data.error_code,
        data.message || 'API Error',
        undefined
      );
    }

    // Return the data if successful (can be null)
    return data.data ?? null;
  } catch (error: unknown) {
    // Handle axios errors (network errors, HTTP errors, etc.)
    if (error instanceof AxiosError) {
      if (error.response) {
        // Server responded with error status
        const responseData = error.response.data;
        
        // If the response follows our CommonResponse format
        if (responseData && typeof responseData.error_code === 'number') {
          throw new ApiException(
            error.response.status,
            responseData.error_code,
            responseData.message || 'API Error',
            responseData.errors
          );
        }
        
        // If it's a standard HTTP error
        throw new ApiException(
          error.response.status,
          1, // Default error code
          error.response.statusText || 'HTTP Error',
          undefined
        );
      } else if (error.request) {
        // Network error
        throw new ApiException(
          0,
          1,
          'Network Error: Unable to reach server',
          undefined
        );
      }
    } else if (error instanceof ApiException) {
      // Re-throw our custom API exceptions
      throw error;
    } else {
      // Other errors
      throw new ApiException(
        0,
        1,
        error instanceof Error ? error.message : 'Unknown Error',
        undefined
      );
    }
  }
  
  // This should never be reached, but satisfies TypeScript
  return null;
}

/**
 * Generic API handler for responses that don't return data (like logout, delete operations)
 * @param apiCall - The API call function that returns a Promise<AxiosResponse>
 * @returns Promise<void> - Returns nothing if successful, throws ApiException if error
 */
export async function handleApiCallNoData(
  apiCall: () => Promise<AxiosResponse<CommonResponse<null>>>
): Promise<void> {
  try {
    const response = await apiCall();
    const data: CommonResponse<null> = response.data;

    // Check if API returned an error (error_code = 1 means error, error_code = 0 means success)
    if (data.error_code !== 0) {
      throw new ApiException(
        response.status,
        data.error_code,
        data.message || 'API Error',
        undefined
      );
    }
  } catch (error: unknown) {
    // Handle axios errors (network errors, HTTP errors, etc.)
    if (error instanceof AxiosError) {
      if (error.response) {
        // Server responded with error status
        const responseData = error.response.data;
        
        // If the response follows our CommonResponse format
        if (responseData && typeof responseData.error_code === 'number') {
          throw new ApiException(
            error.response.status,
            responseData.error_code,
            responseData.message || 'API Error',
            responseData.errors
          );
        }
        
        // If it's a standard HTTP error
        throw new ApiException(
          error.response.status,
          1, // Default error code
          error.response.statusText || 'HTTP Error',
          undefined
        );
      } else if (error.request) {
        // Network error
        throw new ApiException(
          0,
          1,
          'Network Error: Unable to reach server',
          undefined
        );
      }
    } else if (error instanceof ApiException) {
      // Re-throw our custom API exceptions
      throw error;
    } else {
      // Other errors
      throw new ApiException(
        0,
        1,
        error instanceof Error ? error.message : 'Unknown Error',
        undefined
      );
    }
  }
}

/**
 * Helper function to check if an error is an ApiException
 * @param error - The error to check
 * @returns boolean - True if error is ApiException
 */
export function isApiException(error: unknown): error is ApiException {
  return error instanceof ApiException;
}

/**
 * Helper function to extract error message from any error
 * @param error - The error to extract message from
 * @returns string - The error message
 */
export function getErrorMessage(error: unknown): string {
  if (isApiException(error)) {
    return error.message;
  }
  
  if (error instanceof AxiosError && error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unknown error occurred';
}