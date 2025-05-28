'use client';

import React, { useEffect, useState } from 'react';
import FacebookPost from './FacebookPost';
import { FacebookPageInfo } from '@/types/facebook.type';
import facebookPostApi from '@/apis/facebookPost';

interface FacebookPostListProps {
  limit?: number;
}

const FacebookPostList: React.FC<FacebookPostListProps> = ({ limit = 5 }) => {
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
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Latest Facebook Posts
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: limit }).map((_, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden animate-pulse"
            >
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
                </div>
              </div>
              <div className="aspect-video bg-gray-300 dark:bg-gray-600"></div>
              <div className="p-6">
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 dark:bg-red-900/40 rounded-full">
            <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
            Failed to load Facebook posts
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
      <div className="text-center py-12">
        <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 max-w-md mx-auto">
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full">
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No posts available
          </h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            There are no Facebook posts to display at the moment.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Info Header */}
      {pageInfo.name && (
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Latest Posts from {pageInfo.name}
          </h2>
          {pageInfo.about && (
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {pageInfo.about}
            </p>
          )}
        </div>
      )}

      {/* Posts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pageInfo.posts.data.slice(0, limit).map((post) => (
          <FacebookPost key={post.id} post={post} />
        ))}
      </div>

      {/* Load More Info */}
      {pageInfo.posts.paging?.next && (
        <div className="text-center pt-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Showing {Math.min(limit, pageInfo.posts.data.length)} of {pageInfo.posts.data.length} posts
          </p>
        </div>
      )}
    </div>
  );
};

export default FacebookPostList;
