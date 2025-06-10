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
    default: "CGSEM",
    template: "%s | CGSEM"
  },
  description: "CGSEM - Club Geoscience Engineering & Management. A modern platform for geoscience education, research, and community building with cutting-edge technology.",
  keywords: [
    "CGSEM", 
    "Geoscience", 
    "Engineering", 
    "Management", 
    "Club", 
    "Education", 
    "Research", 
    "Geology", 
    "Earth Sciences", 
    "Mining", 
    "Environmental", 
    "Next.js", 
    "React", 
    "TypeScript", 
    "i18n", 
    "Internationalization", 
    "Dark Mode",
    "Student Organization",
    "Academic Club",
    "Science Community"
  ],
  authors: [
    { name: "CGSEM Team", url: "https://cgsem.org" },
    { name: "Club Development Team" }
  ],
  creator: "CGSEM - Club Geoscience Engineering & Management",
  publisher: "CGSEM Organization",
  applicationName: "CGSEM Platform",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  category: "Education",
  classification: "Educational Platform",
  metadataBase: new URL("https://cgsem.org"),
  alternates: {
    canonical: "/",
    languages: {
      "vi-VN": "/vi",
      "en-US": "/en",
    },
  },
  icons: {
    icon: [
      { url: "/assets/logo/logo_web.png", sizes: "32x32", type: "image/png" },
      { url: "/assets/logo/logo_web.png", sizes: "16x16", type: "image/png" },
    ],
    apple: [
      { url: "/assets/logo/logo_web.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/assets/logo/logo_web.png",
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "vi_VN",
    alternateLocale: ["en_US"],
    url: "https://cgsem.org",
    title: "CGSEM - Club Geoscience Engineering & Management",
    description: "Join CGSEM community for geoscience education, research collaboration, and professional development in earth sciences and engineering.",
    siteName: "CGSEM Platform",
    images: [
      {
        url: "/assets/logo/logo_web.png",
        width: 1200,
        height: 630,
        alt: "CGSEM Logo - Club Geoscience Engineering & Management",
      },
    ],
    countryName: "Vietnam",
  },
  twitter: {
    card: "summary_large_image",
    site: "@cgsem_official",
    creator: "@cgsem_official",
    title: "CGSEM - Club Geoscience Engineering & Management",
    description: "Join CGSEM community for geoscience education, research collaboration, and professional development in earth sciences and engineering.",
    images: ["/assets/logo/logo_web.png"],
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
  },
  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "apple-mobile-web-app-title": "CGSEM",
    "application-name": "CGSEM Platform",
    "msapplication-TileColor": "#3b82f6",
    "msapplication-TileImage": "/assets/logo/logo_web.png",
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
      <Header />

      <HeroSection
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

      <ImageCarouselSection
        images={carouselImages}
        title={t('carousel.title')}
        subtitle={t('carousel.subtitle')}
        description={t('carousel.description')}
        nextText={t('carousel.nextImage')}
        prevText={t('carousel.prevImage')}
        currentText={t('carousel.currentImage')}
      />

      <Footer />
    </HomePageWrapper>
  )
}

export default withAuthState(Home);