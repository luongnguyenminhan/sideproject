import { redirect } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth';
import type { UserResponse } from '@/types/auth.type';

/**
 * Higher-Order Component for server-side route protection
 * Automatically redirects unauthenticated users to the auth page
 */
export function withAuth<T extends object>(
  WrappedComponent: React.ComponentType<T & { user: UserResponse }>,
  redirectTo: string = '/auth'
) {
  return async function AuthenticatedComponent(props: T) {
    const user = await getCurrentUser();
    
    if (!user) {
      redirect(redirectTo);
    }
    
    // Pass the authenticated user data to the wrapped component
    return <WrappedComponent {...props} user={user} />;
  };
}

/**
 * Higher-Order Component to prevent authenticated users from accessing certain pages
 * Useful for login/signup pages that should redirect authenticated users away
 */
export function withoutAuth<T extends object>(
  WrappedComponent: React.ComponentType<T>,
  redirectTo: string = '/'
) {
  return async function UnauthenticatedComponent(props: T) {
    const user = await getCurrentUser();
    
    if (user) {
      redirect(redirectTo);
    }
    
    return <WrappedComponent {...props} />;
  };
}

/**
 * Higher-Order Component that provides auth state to component without redirecting
 * Useful for components that need to behave differently based on auth state
 */
export function withAuthState<T extends object>(
  WrappedComponent: React.ComponentType<T & { user: UserResponse | null; isAuthenticated: boolean }>
) {
  return async function ComponentWithAuth(props: T) {
    const user = await getCurrentUser();
    const isAuthenticated = user !== null;
    
    return <WrappedComponent {...props} user={user} isAuthenticated={isAuthenticated} />;
  };
}
