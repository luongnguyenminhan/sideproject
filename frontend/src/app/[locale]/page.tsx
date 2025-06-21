/* eslint-disable @typescript-eslint/no-unused-vars */
import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"
import React from "react"
import { withAuthState } from '@/hoc/withAuth';
import type { UserResponse } from '@/types/auth.type';
import facebookPostApi from "@/apis/facebookPost";
import TeamSection from '@/components/sections/TeamSection';
import Footer from '@/components/layout/Footer';
import Header from "@/components/layout/header";
import { 
  HomePageWrapper,
  HeroSection,
  FacebookPostsSection,
  FeaturesSection,
  ImageCarouselSection,
  AboutUsSectionWrapper
} from '@/components/home';
import { createFeaturesData } from '@/components/home/home-utils';
import { Metadata } from "next";

interface HomeProps {
  user: UserResponse | null;
  isAuthenticated: boolean;
}
export const metadata: Metadata = {
  title: {
    default: "EnterViu",
    template: "%s | EnterViu"
  },
  description: "EnterViu - Professional Career Platform. Build your profile, discover job opportunities, and connect with employers through our intelligent job matching system.",
  keywords: [
    "EnterViu", 
    "Job Search", 
    "Career", 
    "Profile Building", 
    "Employment", 
    "Job Matching", 
    "Professional", 
    "Resume", 
    "Career Development", 
    "Job Board", 
    "Recruitment", 
    "Next.js", 
    "React", 
    "TypeScript", 
    "i18n", 
    "Internationalization", 
    "Dark Mode",
    "Career Platform",
    "Job Portal",
    "Professional Network"
  ],
  authors: [
    { name: "EnterViu Team", url: "https://enterviu.com" },
    { name: "Career Development Team" }
  ],
  creator: "EnterViu - Professional Career Platform",
  publisher: "EnterViu Organization",
  applicationName: "EnterViu Platform",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  category: "Education",
  classification: "Educational Platform",  metadataBase: new URL("https://enterviu.com"),
  alternates: {
    canonical: "/",
    languages: {
      "vi-VN": "/vi",
      "en-US": "/en",
    },
  },
  icons: {
    icon: [
      { url: "/assets/logo/logo_web.jpg", sizes: "32x32", type: "image/png" },
      { url: "/assets/logo/logo_web.jpg", sizes: "16x16", type: "image/png" },
    ],
    apple: [
      { url: "/assets/logo/logo_web.jpg", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/assets/logo/logo_web.jpg",
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "vi_VN",
    alternateLocale: ["en_US"],
    url: "https://enterviu.com",
    title: "EnterViu - Professional Career Platform",
    description: "Join EnterViu community to build your professional profile, discover job opportunities, and connect with top employers through intelligent matching.",
    siteName: "EnterViu Platform",
    images: [
      {
        url: "/assets/logo/logo_web.jpg",
        width: 1200,
        height: 630,
        alt: "EnterViu Logo - Professional Career Platform",
      },
    ],
    countryName: "Vietnam",
  },
  twitter: {
    card: "summary_large_image",
    site: "@enterviu_official",
    creator: "@enterviu_official",
    title: "EnterViu - Professional Career Platform",
    description: "Join EnterViu community to build your professional profile, discover job opportunities, and connect with top employers through intelligent matching.",
    images: ["/assets/logo/logo_web.jpg"],
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "your-google-site-verification-code",
    yandex: "your-yandex-verification-code",
    yahoo: "your-yahoo-verification-code",
  },  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "apple-mobile-web-app-title": "EnterViu",
    "application-name": "EnterViu Platform",
    "msapplication-TileColor": "#3b82f6",
    "msapplication-TileImage": "/assets/logo/logo_web.jpg",
    "theme-color": "#3b82f6",
  },
};
async function Home({ user, isAuthenticated }: HomeProps) {
  const locale = await getCurrentLocale()
  const dictionary = await getDictionary(locale)
  const t = createTranslator(dictionary)

  const postInformation = await facebookPostApi.getPageInfoWithPosts({ limit: 9 }) || null;

  // Public folder images for carousel
  const carouselImages = [
    '/assets/images/home/abc.jpg',
    '/assets/images/home/bcd.jpg',
    '/assets/images/home/cde.jpg',
    '/assets/images/home/def.jpg',
    '/assets/images/home/fgh.jpg',
    '/assets/images/home/thuongem.jpg'
  ];

  // Prepare features data
  const featuresData = createFeaturesData(t);

  return (
    <HomePageWrapper>
      <Header />      <HeroSection
        user={user}
        isAuthenticated={isAuthenticated}
        welcomeTitle={isAuthenticated 
          ? t('home.welcomeBack', { name: user?.name || user?.username || '' })
          : t('home.title')
        }
        description={isAuthenticated 
          ? t('home.authenticatedDescription')
          : t('home.description')
        }
        getStartedText={t('home.getStarted')}
        learnMoreText={t('home.learnMore')}
        locale={locale}
        dictionary={dictionary}
      />

      <AboutUsSectionWrapper postInformation={postInformation} />

      <FacebookPostsSection
        postInformation={postInformation}
        locale={locale}
        postsTitle={t('home.post')}
        profilePictureUrl={postInformation?.picture?.data?.url}
      />

      <FeaturesSection
        title={t('home.features.title')}
        subtitle={t('home.features.subtitle')}
        features={featuresData}
      />

      <TeamSection />

      {/* <ImageCarouselSection
        images={carouselImages}
        title={t('carousel.title')}
        subtitle={t('carousel.subtitle')}
        description={t('carousel.description')}
        nextText={t('carousel.nextImage')}
        prevText={t('carousel.prevImage')}
        currentText={t('carousel.currentImage')}
      /> */}

      <Footer />
    </HomePageWrapper>
  )
}

export default withAuthState(Home);