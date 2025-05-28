import { Metadata } from 'next';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { getDictionary, createTranslator } from '@/utils/translation';
import LoginForm from '@/components/auth/loginForm';

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  return {
    title: t('auth.login') || 'Login',
    description: t('auth.loginDescription') || 'Sign in to your account',
  };
}

interface LoginPageProps {
  searchParams?: Promise<{
    callbackUrl?: string;
    error?: string;
  }>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const callbackUrl = params?.callbackUrl;
  const error = params?.error;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {error && (
        <div className="sm:mx-auto sm:w-full sm:max-w-md mb-4">
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            Authentication error occurred. Please try again.
          </div>
        </div>
      )}
      <LoginForm callbackUrl={callbackUrl} />
    </div>
  );
}