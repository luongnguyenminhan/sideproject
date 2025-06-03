'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export async function logoutAction() {
  // Remove the cookie (server-side)
  const cookieStore = await cookies();
  cookieStore.set('access_token', '', { path: '/', maxAge: -1 });
  cookieStore.set('refresh_token', '', { path: '/', maxAge: -1 });
  redirect('/');
}
