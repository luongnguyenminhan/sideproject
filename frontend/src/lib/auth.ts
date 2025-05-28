// Server-side authentication utilities
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import authApi from '@/apis/authApi';
import type { UserResponse } from '@/types/auth.type';

/**
 * Server-side function to get current authenticated user
 * Returns user data if authenticated, null otherwise
 */
export async function getCurrentUser(): Promise<UserResponse | null> {
  try {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('access_token')?.value;
    
    if (!accessToken) {
      return null;
    }

    const user = await authApi.getMe({ Authorization: `Bearer ${accessToken}` });
    return user;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
}

/**
 * Server-side function to check if user is authenticated
 * Returns true if authenticated, false otherwise
 */
export async function isAuthenticated(): Promise<boolean> {
  const user = await getCurrentUser();
  return user !== null;
}

/**
 * Server-side function to require authentication
 * Redirects to auth page if not authenticated
 * Returns user data if authenticated
 */
export async function requireAuth(redirectTo: string = '/auth'): Promise<UserResponse> {
  const user = await getCurrentUser();
  
  if (!user) {
    redirect(redirectTo);
  }
  
  return user;
}

/**
 * Server-side function to prevent access for authenticated users
 * Redirects to home page if authenticated (useful for auth pages)
 */
export async function preventAuthenticatedAccess(redirectTo: string = '/'): Promise<void> {
  const authenticated = await isAuthenticated();
  
  if (authenticated) {
    redirect(redirectTo);
  }
}

/**
 * Server-side function to get authentication status and user data
 * Returns both the authenticated status and user data
 */
export async function getAuthState(): Promise<{
  isAuthenticated: boolean;
  user: UserResponse | null;
}> {
  const user = await getCurrentUser();
  return {
    isAuthenticated: user !== null,
    user,
  };
}
