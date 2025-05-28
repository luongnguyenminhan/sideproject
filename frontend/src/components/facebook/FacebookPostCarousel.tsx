'use client';

import React, { useEffect, useState } from 'react';
import FacebookPost from './FacebookPost';
import { Carousel } from '@/components/ui';
import { FacebookPageInfo } from '@/types/facebook.type';
import facebookPostApi from '@/apis/facebookPost';

interface FacebookPostCarouselProps {
  limit?: number;
  autoPlay?: boolean;
  itemsPerView?: number;
  truncateMessage?: boolean;
  maxMessageLength?: number;
  locale?: string;
  translation?: {
    postsTitle?: string;
    postCountPrefix?: string;
    postCountSuffix?: string;
    errorTitle?: string;
    noPostsTitle?: string;
    noPostsDescription?: string;
    unknownTime?: string;
    post?: string;
  };
}

const FacebookPostCarousel: React.FC<FacebookPostCarouselProps> = ({ 
  limit = 9,
  autoPlay = true,
  itemsPerView = 3,
  truncateMessage = true,
  maxMessageLength = 150,
  translation,
  locale
}) => {
  const [pageInfo, setPageInfo] = useState<FacebookPageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await facebookPostApi.getPageInfoWithPosts({ limit });
        setPageInfo(data);
      } catch (err) {
        console.error('Error fetching Facebook posts:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch Facebook posts');
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, [limit]);

  if (loading) {
    return (
      <div className="w-full">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            Latest Facebook Posts
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: itemsPerView }).map((_, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden animate-pulse"
            >
              <div className="p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded mb-1"></div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
                </div>
              </div>
              <div className="aspect-video bg-gray-300 dark:bg-gray-600"></div>
              <div className="p-4">
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full text-center py-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 dark:bg-red-900/40 rounded-full">
            <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
            {translation?.errorTitle || 'Error Fetching Posts'}
          </h3>
          <p className="text-red-600 dark:text-red-400 text-sm">
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!pageInfo?.posts?.data || pageInfo.posts.data.length === 0) {
    return (
      <div className="w-full text-center py-8">
        <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full">
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            {translation?.noPostsTitle || 'No Facebook Posts Available'}
          </h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            {translation?.noPostsDescription || 'There are no Facebook posts to display at the moment.'}
          </p>
        </div>
      </div>
    );
  }

  const posts = pageInfo.posts.data.slice(0, limit);

  return (
    <div className="w-full space-y-6">
      {/* Page Info Header */}
      {pageInfo.name && (
        <div className="text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {translation?.postsTitle || 'Latest Posts from'} {pageInfo.name}
          </h2>
          {pageInfo.about && (
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto text-sm md:text-base">
              {pageInfo.about}
            </p>
          )}
        </div>
      )}

      {/* Posts Carousel */}
      <Carousel
        autoPlay={autoPlay}
        autoPlayInterval={6000}
        itemsPerView={itemsPerView}
        className="w-full"
      >
        {posts.map((post) => (
          <FacebookPost
            key={post.id}
            post={post}
            truncateMessage={truncateMessage}
            maxMessageLength={maxMessageLength}
            locale={locale}
            translation={{
              unknownTime: translation?.unknownTime,
              post: translation?.post,
            }}
          />
        ))}
      </Carousel>

      {/* Post Count Info */}
      {posts.length > 0 && (
        <div className="text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {translation?.postCountPrefix || 'Showing'} {posts.length} {translation?.postCountSuffix || 'posts from this page.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default FacebookPostCarousel;
