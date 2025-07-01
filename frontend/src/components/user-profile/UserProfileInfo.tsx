import type { UserResponse } from '@/types/auth.type';
import Image from 'next/image';
import { useTranslation } from '@/contexts/TranslationContext';
import { Button } from '../ui';

interface UserProfileInfoProps {
  user: UserResponse;
}

export default function UserProfileInfo({ user }: UserProfileInfoProps) {
  const { t } = useTranslation();
  return (
    <div>
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
        {t('userProfile.title')}
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
        </div>
        {/* Profile Information */}
        <div className="flex-1 flex flex-col gap-4 justify-center">
          {/* Username & Email */}
          <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-6 mb-4">
            <div>
              <span className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t('userProfile.username')}
              </span>
              <span className="text-md font-semibold text-gray-900 dark:text-white">
                {user.username}
              </span>
            </div>
            <div>
              <span className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t('userProfile.email')}
              </span>
              <span className="text-md font-semibold text-gray-900 dark:text-white">
                {user.email}
              </span>
            </div>
          </div>
          {/* Name & Birthday, Address */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('userProfile.name')}
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
                {t('userProfile.birthday')}
              </label>
              <input
                type="date"
                readOnly
                value={'2004-05-02'}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('userProfile.address')}
              </label>
              <input
                type="text"
                value={'Ho Chi Minh City, Vietnam'}
                readOnly
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="flex gap-4 pt-6">
            <Button className="px-6 py-3 bg-[var(--feature-blue)] hover:bg-[var(--feature-blue-dark)] text-white rounded-lg transition-colors">
              {t('userProfile.editProfile')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
