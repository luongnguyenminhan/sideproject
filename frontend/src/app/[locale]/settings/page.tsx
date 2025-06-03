import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { withAuth } from '@/hoc/withAuth';
import type { UserResponse } from '@/types/auth.type';
import ThemeSwapper from '@/components/global/themeSwapper';
import LanguageSwitcher from '@/components/global/languageSwapper';

interface SettingsPageProps {
  user: UserResponse;
}

async function SettingsPage({ user }: SettingsPageProps) {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  return (
      <div className="min-h-screen p-8 bg-gradient-to-br from-[color:var(--gradient-bg-from)] to-[color:var(--gradient-bg-to)]">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-xl p-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
            {t('settings.title') || 'Settings'}
          </h1>
          
          <div className="space-y-8">
            {/* Account Settings */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('settings.account') || 'Account Settings'}
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {t('settings.currentUser') || 'Currently signed in as'}
                  </p>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {user.name || user.username} ({user.email})
                  </p>
                </div>
                <div className="flex gap-4">
                  <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
                    {t('settings.updateAccount') || 'Update Account'}
                  </button>
                  <button className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors">
                    {t('settings.deleteAccount') || 'Delete Account'}
                  </button>
                </div>
              </div>
            </div>

            {/* Appearance Settings */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('settings.appearance') || 'Appearance'}
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {t('settings.theme') || 'Theme'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t('settings.themeDescription') || 'Choose your preferred theme'}
                    </p>
                  </div>
                  <ThemeSwapper />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {t('settings.language') || 'Language'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t('settings.languageDescription') || 'Choose your preferred language'}
                    </p>
                  </div>
                  <LanguageSwitcher />
                </div>
              </div>
            </div>

            {/* Notifications Settings */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('settings.notifications') || 'Notifications'}
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {t('settings.emailNotifications') || 'Email Notifications'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t('settings.emailNotificationsDescription') || 'Receive notifications via email'}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {t('settings.pushNotifications') || 'Push Notifications'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t('settings.pushNotificationsDescription') || 'Receive push notifications in your browser'}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Security Settings */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                {t('settings.security') || 'Security'}
              </h2>
              <div className="space-y-4">
                <button className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg transition-colors">
                  {t('settings.changePassword') || 'Change Password'}
                </button>
                <button className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
                  {t('settings.enableTwoFactor') || 'Enable Two-Factor Authentication'}
                </button>
                <button className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                  {t('settings.downloadData') || 'Download My Data'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
  );
}

export default withAuth(SettingsPage);
