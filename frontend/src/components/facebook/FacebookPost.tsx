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
  profilePictureUrl?: string;
}

const FacebookPost: React.FC<FacebookPostProps> = ({ 
  post, 
  truncateMessage = false, 
  maxMessageLength = 150,
  locale,
  translation,
  profilePictureUrl
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
    <div className="bg-[color:var(--card)] rounded-xl shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-300 border border-[color:var(--border)] overflow-hidden">
      {/* Post Header */}
      <div className="p-6 pb-4">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-[color:var(--primary)] rounded-full flex items-center justify-center">
            <Image 
              className="rounded-full" 
              src={profilePictureUrl || '/assets/logo/logo_web.png'}
              alt={'Facebook Logo'}
              width={40}
              height={40}
            />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-sm text-[color:var(--card-foreground)]">{translation?.post || 'Facebook Post'}</h3>
            <p className="text-sm text-[color:var(--muted-foreground)]">
              {formatDate(post.created_time)}
            </p>
          </div>
        </div>
        {/* Post Message */}
        {displayMessage && (
          <div className="mb-4">
            <p className="text-[color:var(--card-foreground)] leading-relaxed whitespace-pre-wrap min-h-[6rem] max-h-[6rem]">
              {displayMessage}
            </p>
          </div>
        )}
      </div>

      {/* Post Image */}
      {post.full_picture && (
        <div className="relative">
          <div className="aspect-video relative bg-[color:var(--muted)]">
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
              <svg className="w-5 h-5 text-[color:var(--destructive)]" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
              <span className="text-sm text-[color:var(--muted-foreground)]">
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
