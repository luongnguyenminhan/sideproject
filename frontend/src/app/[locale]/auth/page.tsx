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

  // Get current locale and translations
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  return (
    <div className="min-h-screen flex flex-col justify-center bg-gradient-to-br from-[color:var(--auth-bg-from)] via-[color:var(--auth-bg-via)] to-[color:var(--auth-bg-to)]">
      {error && (
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-4">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg">
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