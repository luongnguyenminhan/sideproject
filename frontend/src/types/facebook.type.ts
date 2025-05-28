import { CommonResponse } from './common.type';

// Reaction Summary matching Python ReactionSummary
export interface ReactionSummary {
  total_count: number;
  viewer_reaction?: string | null;
}

// Paging Cursors matching Python PagingCursors
export interface PagingCursors {
  before?: string | null;
  after?: string | null;
}

// Paging Info matching Python PagingInfo
export interface PagingInfo {
  cursors?: PagingCursors | null;
  next?: string | null;
}

// Reactions matching Python Reactions
export interface Reactions {
  data: Record<string, unknown>[];
  paging?: PagingInfo | null;
  summary?: ReactionSummary | null;
}

// Facebook Post matching Python FacebookPost
export interface FacebookPost {
  id: string;
  message?: string | null;
  full_picture?: string | null;
  created_time: string; // ISO datetime string
  reactions?: Reactions | null;
}

// Facebook Posts matching Python FacebookPosts
export interface FacebookPosts {
  data: FacebookPost[];
  paging?: PagingInfo | null;
}

// Facebook Page Info matching Python FacebookPageInfo
export interface FacebookPageInfo {
  id: string;
  name: string;
  picture?: {
        data: {
            url: string;
        }
    } | null;
  followers_count?: number | null;
  about?: string | null;
  emails?: string[];
  website?: string | null;
  single_line_address?: string | null;
  posts?: FacebookPosts | null;
}

// Request types
export interface GetPageInfoRequest {
  limit?: number; // 1-25, default: 5
}

// Response Types following the CommonResponse pattern
export type FacebookPageResponse = CommonResponse<FacebookPageInfo>;
export type FacebookPostsResponse = CommonResponse<FacebookPost[]>;