"use client";
import React from 'react';
import UserSidebar from './UserSidebar';
import UserSettingsContent from './UserSettingsContent';
import type { UserResponse } from '@/types/auth.type';
import UserProfileInfo from './UserProfileInfo';

interface ProfileClientProps {
  user: UserResponse;
}

const ProfileClient: React.FC<ProfileClientProps> = ({ user }) => {
  const [section, setSection] = React.useState('profile');

  let content = null;
  if (section === 'profile') {
    content = <UserProfileInfo user={user}/>;
  } else if (section === 'settings') {
    content = <UserSettingsContent />;
  } else {
    content = <div className="text-gray-700 dark:text-gray-200">Coming soon...</div>;
  }

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-[color:var(--gradient-bg-from)] to-[color:var(--gradient-bg-to)]">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-8">
        <div className="w-full md:w-64 order-1">
          <UserSidebar active={section} onNavigate={setSection} />
        </div>
        <div className="flex-1 order-2">
          {content}
        </div>
      </div>
    </div>
  );
};

export default ProfileClient;
