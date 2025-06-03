'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppSelector } from '@/redux/hooks';
import Cookies from 'js-cookie';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

/**
 * Client-side protected route component
 * Redirects to auth page if not authenticated
 * Integrates with Redux auth state
 */
export default function ProtectedRoute({ 
  children, 
  fallback = <div>Loading...</div>, 
  redirectTo = '/' 
}: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Check for access token in cookies
    const accessToken = Cookies.get('access_token');
    
    // If no token and not authenticated via Redux, redirect to auth
    if (!accessToken && !isAuthenticated && !isLoading) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  // Show loading fallback while checking authentication
  if (isLoading) {
    return <>{fallback}</>;
  }

  // Check for access token as fallback if Redux state isn't ready
  const accessToken = Cookies.get('access_token');
  if (!accessToken && !isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
