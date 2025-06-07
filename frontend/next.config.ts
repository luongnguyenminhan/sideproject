import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: [
      'images.unsplash.com',
      'i.pravatar.cc',
      'ui-avatars.com',
      'lh3.googleusercontent.com',
      'scontent.fsgn5-1.fna.fbcdn.net',
      'scontent.fsgn5-2.fna.fbcdn.net',
      'scontent.fsgn5-3.fna.fbcdn.net',
      'scontent.fsgn5-4.fna.fbcdn.net',
      'scontent.fsgn5-5.fna.fbcdn.net',
      'scontent.fsgn5-6.fna.fbcdn.net',
      'scontent.fsgn5-7.fna.fbcdn.net',
      'scontent.fsgn5-8.fna.fbcdn.net',
      'scontent.fsgn5-9.fna.fbcdn.net',
      'scontent.fsgn5-10.fna.fbcdn.net',
      'scontent.fsgn5-11.fna.fbcdn.net',
      'scontent.fsgn5-12.fna.fbcdn.net',
      'scontent.fsgn5-13.fna.fbcdn.net',
      'scontent.fsgn5-14.fna.fbcdn.net',
      'scontent.fsgn5-15.fna.fbcdn.net',
      'external.fsgn5-1.fna.fbcdn.net',
      'external.fsgn5-2.fna.fbcdn.net',
      'external.fsgn5-3.fna.fbcdn.net',
      'platform-lookaside.fbsbx.com',
      'lookaside.fbsbx.com',
      'https://www.plantuml.com'
    ],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'i.pravatar.cc',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'www.plantuml.com',
        pathname: '/plantuml/**',
      },
      {
        protocol: 'https',
        hostname: 'scontent.fsgn5-*.fna.fbcdn.net',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.fbcdn.net',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.fbsbx.com',
        pathname: '/**',
      },
    ],
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "frame-ancestors *", // ✅ Cho phép nhúng từ mọi nơi
          },
        ],
      },
    ];
  },
};

export default nextConfig;