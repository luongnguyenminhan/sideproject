import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { withAuth } from '@/hoc/withAuth';
import type { UserResponse } from '@/types/auth.type';
import Image from 'next/image';

interface ProfilePageProps {
  user: UserResponse;
}

async function ProfilePage({ user }: ProfilePageProps) {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  return (
      <div className="min-h-screen p-8 bg-gradient-to-br from-[color:var(--gradient-bg-from)] to-[color:var(--gradient-bg-to)]">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-xl p-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
            {t('profile.title')}
          </h1>
          
          <div className="flex flex-col md:flex-row gap-8">
            {/* Profile Picture Section */}
            <div className="flex flex-col items-center space-y-4">
              <div className="relative">
                <Image
                  src={user.profile_picture || '/file.svg'}
                  alt={user.name || user.username}
                  width={128}
                  height={128}
                  className="rounded-full border-4 border-[color:var(--gradient-text-from)] shadow-lg"
                />
              </div>
              <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
                {t('profile.changePhoto')}
              </button>
            </div>

            {/* Profile Information */}
            <div className="flex-1 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('auth.name')}
                  </label>
                  <input
                    type="text"
                    value={user.name || ''}
                    readOnly
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('auth.username')}
                  </label>
                  <input
                    type="text"
                    value={user.username}
                    readOnly
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('auth.email')}
                  </label>
                  <input
                    type="email"
                    value={user.email}
                    readOnly
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('auth.role')}
                  </label>
                  <input
                    type="text"
                    value={user.role}
                    readOnly
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              
              <div className="flex gap-4 pt-6">
                <button className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
                  {t('profile.editProfile')}
                </button>
                <button className="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                  {t('profile.changePassword')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
  );
}

export default withAuth(ProfilePage);
