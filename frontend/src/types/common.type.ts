/* eslint-disable @typescript-eslint/no-explicit-any */
// Operator enum matching the Python Operator enum
export enum Operator {
  Eq = "eq",
  Ne = "ne", // This is the not equal operator
  Lt = "lt", // This is the less than operator
  Lte = "lte",
  Gt = "gt",
  Gte = "gte",
  Contains = "contains",
  Startswith = "startswith",
  Endswith = "endswith",
  InList = "in_list",
  NotIn = "not_in",
  IsNull = "is_null",
  IsNotNull = "is_not_null"
}

// Base request schema - added modelName property to avoid empty interface warning
export interface RequestSchema {
  /** Optional metadata field to identify the model type */
  _modelType?: string;
}


// Filter item matching the Python Filter class
export interface FilterItem {
  field: string;
  operator: Operator;
  value: string | number | boolean | Array<any> | null;
}

// Filterable request schema with pagination and filtering capability
export interface FilterableRequestSchema extends RequestSchema {
  page?: number;
  page_size?: number;
  filters?: FilterItem[];
}

// Common response matching the Python APIResponse
export interface CommonResponse<T = unknown> {
  error_code: number;
  message: string;
  description?: string;
  data?: T | null;
}

// Api error response
export interface ApiError {
  status: number;
  error_code: number;
  message: string;
  errors?: Record<string, string[]>;
}

// Auth state for the application
export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: null | {
    id: string;
    email: string;
    username: string;
    confirmed: boolean;
    profile_picture?: string;
  };
  error: string | null;
}

// Pagination parameter for requests
export interface PaginationParameter {
  page: number;
  page_size: number;
}

// Pagination information matching the Python PagingInfo class
export interface PagingInfo {
  total: number;
  total_pages: number;
  page: number;
  page_size: number;
}

// Paginated response data matching the Python PaginatedResponse
export interface Pagination<T = unknown> {
  items: T[];
  paging: PagingInfo;
}

// Legacy pagination metadata for backward compatibility
export interface PaginationMetadata {
  total_count: number;
  page_size: number;
  current_page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export type ApiResponse<T> = Promise<CommonResponse<T>>;
export type ApiErrorResponse = Promise<ApiError>;