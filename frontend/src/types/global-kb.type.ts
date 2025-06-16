/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ApiResponse } from './common.type';

// Admin Document Data
export interface AdminDocumentData {
  id?: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  source?: string;
}

// Request Types
export interface IndexAdminDocumentsRequest {
  documents: AdminDocumentData[];
}

export interface SearchGlobalKBRequest {
  query: string;
  top_k?: number;
  category?: string;
}

export interface InitializeGlobalKBRequest {
  include_defaults?: boolean;
}

// Response Types
export interface GlobalKBSearchResult {
  content: string;
  metadata: Record<string, any>;
  similarity_score: number;
  source: string;
  doc_id: string;
}

export interface GlobalKBSearchResponse {
  results: GlobalKBSearchResult[];
  query: string;
  total_results: number;
}

export interface GlobalKBIndexResponse {
  successful_docs: string[];
  failed_docs: Array<{ id: string; error: string }>;
  total_documents: number;
  indexed_count: number;
  collection_name: string;
}

export interface GlobalKBStats {
  collection_name: string;
  exists: boolean;
  status: string;
  error?: string;
}

export interface UploadGlobalKBFileResponse {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  source: string; // file url
}

// API Response Types
export type IndexAdminDocumentsResponse = ApiResponse<GlobalKBIndexResponse>;
export type SearchGlobalKBResponse = ApiResponse<GlobalKBSearchResponse>;
export type InitializeGlobalKBResponse = ApiResponse<any>;
export type GetGlobalKBStatsResponse = ApiResponse<GlobalKBStats>;