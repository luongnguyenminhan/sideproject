import { Metadata } from 'next';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { getDictionary, createTranslator } from '@/utils/translation';
import LoginForm from '@/components/auth/loginForm';
import ThemeSwapper from '@/components/global/themeSwapper';
import LanguageSwitcher from '@/components/global/languageSwapper';

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

  // Get current locale and translations
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <header className="relative w-full h-full">
      <div className="fixed top-6 right-6 z-10 flex items-center gap-4">
        <ThemeSwapper />
        <LanguageSwitcher />
      </div>
      </header>

      {error && (
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-4">
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
        {t('auth.authenticationError')}
        </div>
      </div>
      )}
      <LoginForm 
      callbackUrl={callbackUrl} 
      translations={{
        login: t('auth.login'),
        loginWithGoogle: t('auth.loginWithGoogle'),
        signInWithGoogle: t('auth.signInWithGoogle'),
        bySigningIn: t('auth.bySigningIn'),
        signingIn: t('common.loading'),
        loginSuccess: t('auth.loginSuccess'),
        connectingToGoogle: t('auth.connectingToGoogle') || 'Connecting to Google...',
        pleaseWait: t('auth.pleaseWait') || 'This process will happen automatically, please wait a moment.',
        unableToConnect: t('auth.unableToConnect') || 'Unable to connect to Google login service. Please try again later.',
        openingGoogleLogin: t('auth.openingGoogleLogin') || 'Opening Google login window...',
        allowPopups: t('auth.allowPopups') || 'Please allow pop-ups and try again'
      }}
      />
    </div>
  );
}