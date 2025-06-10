import ResponsiveFacebookCarousel from './ResponsiveFacebookCarousel';
import { FacebookPageInfo } from '@/types/facebook.type';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';

interface FacebookPostCarouselProps {
  limit?: number;
  autoPlay?: boolean;
  truncateMessage?: boolean;
  maxMessageLength?: number;
  pageInfo?: FacebookPageInfo | null;
  locale?: string;
  profilePictureUrl?: string;
}

const FacebookPostCarousel: React.FC<FacebookPostCarouselProps> = async ({ 
  limit = 9,
  autoPlay = true,
  truncateMessage = true,
  maxMessageLength = 150,
  pageInfo,
  profilePictureUrl,

}) => {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  if (!pageInfo?.posts?.data || pageInfo.posts.data.length === 0) {
    return (
      <div className="w-full text-center py-8">
        <div className="bg-[color:var(--muted)] border border-[color:var(--border)] rounded-xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-[color:var(--secondary)] rounded-full">
            <svg className="w-6 h-6 text-[color:var(--muted-foreground)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-2">
            {t('noPostsTitle')}
          </h3>
          <p className="text-[color:var(--muted-foreground)] text-sm">
            {t('noPostsDescription')}
          </p>
        </div>
      </div>
    );
  }

  const posts = pageInfo.posts.data.slice(0, limit);

  return (
    <div className="w-full space-y-6">      {/* Posts Carousel with Responsive Items Per View */}
      <div className="relative">
        <ResponsiveFacebookCarousel
          posts={posts}
          autoPlay={autoPlay}
          truncateMessage={truncateMessage}
          maxMessageLength={maxMessageLength}
          locale={locale}
          translation={{
            unknownTime: t('home.unknownTime'),
            post: pageInfo?.name || t('home.facebookPageName'),
          }}
          profilePictureUrl={profilePictureUrl}
        />
      </div>

      {/* Post Count Info */}
      {posts.length > 0 && (
        <div className="text-center">
          <p className="text-sm text-[color:var(--muted-foreground)]">
            {t('home.facebookPostCountPrefix')} {posts.length} {t('home.facebookPostCountSuffix')}
          </p>
        </div>
      )}
    </div>
  );
};

export default FacebookPostCarousel;
