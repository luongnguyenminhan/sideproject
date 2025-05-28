'use client';

import React from 'react';
import Image from 'next/image';
import { FacebookPost as FacebookPostType } from '@/types/facebook.type';
import { formatDistanceToNow } from 'date-fns';
import { vi, enUS } from 'date-fns/locale';

interface FacebookPostProps {
  post: FacebookPostType;
  truncateMessage?: boolean;
  maxMessageLength?: number;
  locale?: string;
  translation?: {
    unknownTime?: string;
    post?: string;
  };
}

const FacebookPost: React.FC<FacebookPostProps> = ({ 
  post, 
  truncateMessage = false, 
  maxMessageLength = 150,
  locale,
  translation
}) => {
const formatDate = (dateString: string) => {
    try {
        const date = new Date(dateString);
        return formatDistanceToNow(date,{
  addSuffix: true,
  locale: locale === 'vi' ? vi : enUS,
});
    } catch {
        return translation?.unknownTime || 'Unknown time';
    }
};
  const getTotalReactions = () => {
    return post.reactions?.summary?.total_count || 0;
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };
  const displayMessage = post.message?.split('\n')[0] // Take the first paragraph
    ? (truncateMessage ? truncateText(post.message?.split('\n')[0], maxMessageLength) : post.message?.split('\n')[0])
    : null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Post Header */}
      <div className="p-6 pb-4">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white">{translation?.post || 'Facebook Post'}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {formatDate(post.created_time)}
            </p>
          </div>
        </div>
        {/* Post Message */}
        {displayMessage && (
          <div className="mb-4">
            <p className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap min-h-[6rem] max-h-[6rem]">
              {displayMessage}
            </p>
          </div>
        )}
      </div>

      {/* Post Image */}
      {post.full_picture && (
        <div className="relative">
          <div className="aspect-video relative bg-gray-100 dark:bg-gray-700">
            <Image
              src={post.full_picture}
              alt="Facebook post image"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          </div>
        </div>
      )}

      {/* Post Footer */}
      <div className="p-6 pt-4">
        <div className="flex items-center justify-between">
          {/* Reactions */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {getTotalReactions()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacebookPost;
