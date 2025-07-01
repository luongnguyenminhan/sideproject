import { useTranslation } from '@/contexts/TranslationContext';
import ThemeSwapper from '../global/themeSwapper';
import LanguageSwitcher from '../global/languageSwapper';

export default function UserSettingsContent() {
    const { t } = useTranslation();
  return (
    <div className="space-y-8">
      {/* Appearance Settings */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          {t('userSettings.appearance')}
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                {t('userSettings.theme')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('userSettings.themeDescription')}
              </p>
            </div>
            <ThemeSwapper />
            
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                {t('userSettings.language')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('userSettings.languageDescription')}
              </p>
            </div>
            <LanguageSwitcher />
          </div>
        </div>
      </div>
      {/* Notifications Settings */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          {t('userSettings.notifications')}
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                {t('userSettings.emailNotifications')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('userSettings.emailNotificationsDescription')}
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
                {t('userSettings.pushNotifications')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('userSettings.pushNotificationsDescription')}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
