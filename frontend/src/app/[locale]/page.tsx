import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"
import React from "react"
import { withAuthState } from '@/hoc/withAuth';
import type { UserResponse } from '@/types/auth.type';
import { FacebookPostCarousel } from '@/components/facebook';
import facebookPostApi from "@/apis/facebookPost";
import AboutUsSection from '@/components/about-us/AboutUsSection';
import TeamSection from '@/components/sections/TeamSection';
import Footer from '@/components/layout/Footer';
import ImageCarousel from '@/components/ui/ImageCarousel';
import Header from "@/components/layout/header";
import { 
  FallingText, 
  ParticleBackground, 
  MagneticCard, 
  GradientOrb, 
  ScrollReveal,
  MagnetButton,
  AnimatedRibbon
} from '@/components/animations';
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
      { url: "/Logo CLB 2023.png", sizes: "32x32", type: "image/png" },
      { url: "/Logo CLB 2023.png", sizes: "16x16", type: "image/png" },
    ],
    apple: [
      { url: "/Logo CLB 2023.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/Logo CLB 2023.png",
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
        url: "/Logo CLB 2023.png",
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
    images: ["/Logo CLB 2023.png"],
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
    "msapplication-TileImage": "/Logo CLB 2023.png",
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
    '/abc.jpg',
    '/bcd.jpg',
    '/cde.jpg',
    '/def.jpg',
    '/fgh.jpg',
    '/thuongem.jpg'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] relative overflow-hidden">
      {/* Enhanced Animated Background Effects */}
      <ParticleBackground 
        particleCount={40} 
        color="rgba(59, 130, 246, 0.4)"
        className="opacity-50"
      />
      <AnimatedRibbon count={5} thickness={15} speed={0.2} className="opacity-20" />
      
      {/* Multiple Gradient Orbs for React Bits feel */}
      <GradientOrb 
        size={400} 
        className="top-20 -left-32" 
        color1="rgba(59, 130, 246, 0.1)"
        color2="rgba(147, 51, 234, 0.1)"
        duration={15}
      />
      <GradientOrb 
        size={300} 
        className="top-40 right-10" 
        color1="rgba(236, 72, 153, 0.1)"
        color2="rgba(59, 130, 246, 0.1)"
        duration={18}
        delay={3}
      />
      <GradientOrb 
        size={250} 
        className="bottom-32 -left-16" 
        color1="rgba(147, 51, 234, 0.1)"
        color2="rgba(236, 72, 153, 0.1)"
        duration={20}
        delay={6}
      />
      <GradientOrb 
        size={200} 
        className="bottom-20 right-20" 
        color1="rgba(34, 197, 94, 0.1)"
        color2="rgba(59, 130, 246, 0.1)"
        duration={22}
        delay={9}
      />

      <Header />

      {/* Enhanced Hero Section */}
      <section className="relative py-32 px-6 sm:px-8 lg:px-12">
        <div className="max-w-6xl mx-auto text-center space-y-12">
          {/* Main Title with Shiny Effect */}
          <FallingText variant="bounce" delay={0.2} duration={1.5}>
            <div 
              className="text-5xl md:text-7xl lg:text-8xl font-bold bg-clip-text text-transparent leading-tight bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-8"
            >
              {isAuthenticated 
                ? t('home.welcomeBack', { name: user?.name || user?.username || '' })
                : t('home.title') || 'Welcome to Our Platform'
              }
            </div>
          </FallingText>

          {/* Subtitle */}
          <FallingText variant="fade" delay={0.6} duration={1.2}>
            <div className="text-xl md:text-2xl lg:text-3xl text-[color:var(--muted-foreground)] max-w-4xl mx-auto leading-relaxed">
              {isAuthenticated 
                ? t('home.authenticatedDescription') || 'Welcome back! Discover new features and updates.'
                : t('home.description') || 'Experience the future of web applications with our modern platform.'
              }
            </div>
          </FallingText>

          {/* Call to Action Buttons */}
          <FallingText variant="scale" delay={1} duration={1}>
            <div className="flex flex-col sm:flex-row gap-8 justify-center mt-16">
              <MagnetButton magnetStrength={0.8}>
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] rounded-xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <button className="relative px-12 py-4 text-lg text-[color:var(--primary-foreground)] font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-[var(--button-hover-shadow)] transform hover:-translate-y-2 bg-gradient-to-br from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:from-blue-700 hover:to-blue-900 border border-white/20">
                    {t('home.getStarted') || 'Get Started'}
                  </button>
                </div>
              </MagnetButton>
              
              <MagnetButton magnetStrength={0.5}>
                <div className="group relative">
                  <div className="absolute inset-0 bg-[color:var(--card)] rounded-xl blur-sm opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
                  <button className="relative px-12 py-4 text-lg bg-[color:var(--card)] hover:bg-[color:var(--muted)] text-[color:var(--card-foreground)] font-semibold rounded-xl border-2 border-[color:var(--border)] transition-all duration-300 hover:border-[color:var(--ring)] transform hover:-translate-y-2 backdrop-blur-sm">
                    {t('home.learnMore') || 'Learn More'}
                  </button>
                </div>
              </MagnetButton>
            </div>
          </FallingText>
        </div>
      </section>

      {/* About Us Section */}
      <ScrollReveal direction="up" delay={0.2}>
        <section className="py-8 px-6 sm:px-8 lg:px-12">
          <div className="max-w-[85%] mx-auto">
            {postInformation && (
              <AboutUsSection pageInfo={postInformation}/>
            )}
          </div>
        </section>
      </ScrollReveal>

      {/* Facebook Posts Carousel */}
      <ScrollReveal direction="up" delay={0.4}>
        <section className="py-8 px-6 sm:px-8 lg:px-12">
          <div className="max-w-[85%] mx-auto">
            <FallingText variant="bounce" delay={0.2}>
              <div className="text-center mb-12">
                <div className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-4">
                  {t('home.post') || 'Latest Posts'}
                </div>
                <p className="text-xl text-[color:var(--muted-foreground)] max-w-2xl mx-auto">
                  {t('home.facebookPostCountPrefix')} 9 {t('home.facebookPostCountSuffix')}
                </p>
              </div>
            </FallingText>
            
            <FacebookPostCarousel 
              limit={9} 
              autoPlay={true} 
              truncateMessage={true}
              maxMessageLength={120}
              pageInfo={postInformation}
              locale={locale}
            />
          </div>
        </section>
      </ScrollReveal>

      {/* Enhanced Features Section */}
      <ScrollReveal direction="up" delay={0.2}>
        <section className="py-20 px-6 sm:px-8 lg:px-12">
          <div className="max-w-6xl mx-auto">
        <FallingText variant="bounce" className="text-center mb-20">
          <div 
            className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-6"
          >
            {t('home.features.title')}
          </div>
          <p className="text-xl text-[color:var(--muted-foreground)] max-w-2xl mx-auto">
            {t('home.features.subtitle')}
          </p>
        </FallingText>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">            
          <ScrollReveal direction="up" delay={0.1}>
            <MagneticCard strength={20}>
          <div className="bg-[color:var(--card)] rounded-2xl p-12 shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 border border-[color:var(--border)] hover:border-[color:var(--feature-blue-text)] h-full group relative overflow-hidden">              
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            <div className="relative z-10">
              <div className="w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-[color:var(--feature-blue)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
            <svg className="w-10 h-10 text-[color:var(--feature-blue-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
              </div>
              <h3 className="text-2xl font-semibold text-[color:var(--card-foreground)] mb-6">
            {t('home.features.fastPerformance.title')}
              </h3>
              <p className="text-[color:var(--muted-foreground)] leading-relaxed text-lg mb-6">
            {t('home.features.fastPerformance.description')}
              </p>
              <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-blue)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Optimized performance</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-blue)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Lightning-fast loading</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-blue)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Seamless user experience</span>
            </div>
              </div>
            </div>
          </div>
            </MagneticCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={0.2}>
            <MagneticCard strength={20}>
          <div className="bg-[color:var(--card)] rounded-2xl p-12 shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 border border-[color:var(--border)] hover:border-[color:var(--feature-green-text)] h-full group relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-green-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            <div className="relative z-10">
              <div className="w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-[color:var(--feature-green)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
            <svg className="w-10 h-10 text-[color:var(--feature-green-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
              </div>
              <h3 className="text-2xl font-semibold text-[color:var(--card-foreground)] mb-6">
            {t('home.features.globalReady.title')}
              </h3>
              <p className="text-[color:var(--muted-foreground)] leading-relaxed text-lg mb-6">
            {t('home.features.globalReady.description')}
              </p>
              <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-green)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Multi-language support</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-green)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Global accessibility</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-green)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Cultural adaptation</span>
            </div>
              </div>
            </div>
          </div>
            </MagneticCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={0.3}>
            <MagneticCard strength={20}>
          <div className="bg-[color:var(--card)] rounded-2xl p-12 shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 border border-[color:var(--border)] hover:border-[color:var(--feature-purple-text)] h-full group relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            <div className="relative z-10">
              <div className="w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-[color:var(--feature-purple)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
            <svg className="w-10 h-10 text-[color:var(--feature-purple-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
              </div>
              <h3 className="text-2xl font-semibold text-[color:var(--card-foreground)] mb-6">
            {t('home.features.modernStack.title')}
              </h3>
              <p className="text-[color:var(--muted-foreground)] leading-relaxed text-lg mb-6">
            {t('home.features.modernStack.description')}
              </p>
              <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-purple)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Next.js & React</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-purple)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">TypeScript support</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-purple)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Modern development tools</span>
            </div>
              </div>
            </div>
          </div>
            </MagneticCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={0.4}>
            <MagneticCard strength={20}>
          <div className="bg-[color:var(--card)] rounded-2xl p-12 shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 border border-[color:var(--border)] hover:border-[color:var(--feature-yellow-text)] h-full group relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            <div className="relative z-10">
              <div className="w-20 h-20 rounded-xl flex items-center justify-center mb-8 bg-[color:var(--feature-yellow)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
            <svg className="w-10 h-10 text-[color:var(--feature-yellow-text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
              </div>
              <h3 className="text-2xl font-semibold text-[color:var(--card-foreground)] mb-6">
            {t('home.features.darkMode.title')}
              </h3>
              <p className="text-[color:var(--muted-foreground)] leading-relaxed text-lg mb-6">
            {t('home.features.darkMode.description')}
              </p>
              <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-yellow)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Dark & light themes</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-yellow)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Eye-friendly design</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[color:var(--feature-yellow)] rounded-full"></div>
              <span className="text-[color:var(--muted-foreground)]">Automatic switching</span>
            </div>
              </div>
            </div>
          </div>
            </MagneticCard>
          </ScrollReveal>
        </div>
          </div>
        </section>
      </ScrollReveal>

      {/* Team Section */}
      <TeamSection />

      {/* Image Carousel Demo Section */}
      <ImageCarousel
        images={carouselImages}
        title={t('carousel.title')}
        subtitle={t('carousel.subtitle')}
        description={t('carousel.description')}
        nextText={t('carousel.nextImage')}
        prevText={t('carousel.prevImage')}
        currentText={t('carousel.currentImage')}
        autoPlay={true}
        interval={5000}
      />

      {/* Footer */}
      <Footer />
    </div>
  )
}

export default withAuthState(Home);