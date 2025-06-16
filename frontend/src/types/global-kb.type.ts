/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ApiResponse } from './common.type';

// Document Data
export interface AdminDocumentData {
  id?: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  source?: string;
  create_date?: string;
}

// Request Types
export interface SearchGlobalKBRequest {
  query?: string;
  top_k?: number;
  category?: string;
}

// Response Types
export interface GlobalKBResponse {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  source?: string;
  create_date: string;
}

export interface GlobalKBStats {
  total_documents: number;
  [key: string]: any;
}

export interface UploadGlobalKBFileResponse {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  source: string;
  create_date: string;
}

// API Response Types
export type GetGlobalKBStatsResponse = ApiResponse<GlobalKBStats>;