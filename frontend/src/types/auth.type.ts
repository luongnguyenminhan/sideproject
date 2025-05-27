import { CommonResponse, RequestSchema, FilterableRequestSchema, Pagination } from './common.type';

// User Response matching Python UserResponse
export interface UserResponse {
  id: string;
  email: string;
  role: string;
  name?: string | null;
  username: string;
  confirmed: boolean;
  create_date?: string | null;
  update_date?: string | null;
  profile_picture?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  locale?: string | null;
  google_id?: string | null;
  access_token?: string | null;
  refresh_token?: string | null;
  token_type?: string | null;
}

// Search User Request matching Python SearchUserRequest
export type SearchUserRequest = FilterableRequestSchema;

// Refresh Token Request matching Python RefreshTokenRequest
export interface RefreshTokenRequest extends RequestSchema {
  refresh_token: string;
}

// Google Direct Login Request matching Python GoogleDirectLoginRequest
export interface GoogleDirectLoginRequest {
  access_token: string;
  id_token?: string | null;
  refresh_token?: string | null;
  expires_in?: number | null;
  token_type?: string | null;
  scope?: string | null;
}

// Google Revoke Token Request matching Python GoogleRevokeTokenRequest
export interface GoogleRevokeTokenRequest {
  token: string;
}

// OAuth User Info matching Python OAuthUserInfo
export interface OAuthUserInfo {
  email: string;
  name?: string | null;
  picture?: string | null;
}

// Response Types
export type SearchUserResponse = CommonResponse<Pagination<UserResponse>>;
export type GoogleLoginResponse = CommonResponse<UserResponse>;
export type TokenRefreshResponse = CommonResponse<UserResponse>;
export type GoogleRevokeResponse = CommonResponse<null>;
export type MeResponse = CommonResponse<UserResponse>;

// Legacy type aliases for backward compatibility with existing code
export type TokenRefreshRequest = RefreshTokenRequest;

export type LoginResponseModel = GoogleLoginResponse;
export type TokenRefreshResponseModel = TokenRefreshResponse;
export type LogoutResponseModel = CommonResponse<null>;
export type GoogleAuthUrlResponse = string; // This returns HTML or redirect URL
export type GoogleCallbackResponse = GoogleLoginResponse;
export type MeResponseModel = MeResponse;