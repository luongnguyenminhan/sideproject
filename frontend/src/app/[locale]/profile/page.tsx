import ProfileClient from "@/components/user-profile/ProfileClient";
import { TranslationProvider } from "@/contexts/TranslationContext";
import { withAuth } from "@/hoc/withAuth";
import { UserResponse } from "@/types/auth.type";
import { getCurrentLocale } from "@/utils/getCurrentLocale";
import getDictionary from "@/utils/translation";

interface ProfilePageProps {
  user: UserResponse;
}

async function ProfilePage({ user }: ProfilePageProps) {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  return (
    <TranslationProvider dictionary={dictionary} locale={locale}>
      <ProfileClient user={user} />;
    </TranslationProvider>
  );
}

export default withAuth(ProfilePage);
