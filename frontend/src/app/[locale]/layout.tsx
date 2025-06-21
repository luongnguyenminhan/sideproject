import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { type Locale } from "@/i18n.config";
import { ThemeProvider } from "next-themes";
import { ReduxProvider } from "@/redux/provider";
import PageWrapper from "@/components/layout/page-wrapper";
import ClientWrapper from "@/components/layout/client-wrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Enterviu",
    template: "%s | Enterviu"
  },
  description: "Enterviu",
  keywords: [
    "Enterviu", 
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
    { name: "Enterviu Team", url: "https://app.wc504.io.vn" },
    { name: "Club Development Team" }
  ],
  creator: "Enterviu",
  publisher: "Enterviu Organization",
  applicationName: "Enterviu Platform",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  category: "Education",
  classification: "Educational Platform",
  metadataBase: new URL("https://app.wc504.io.vn"),
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
    url: "https://app.wc504.io.vn",
    title: "Enterviu",
    description: "Join Enterviu community for geoscience education, research collaboration, and professional development in earth sciences and engineering.",
    siteName: "Enterviu Platform",
    images: [
      {
        url: "/assets/logo/logo_web.jpg",
        width: 1200,
        height: 630,
        alt: "Enterviu Logo",
      },
    ],
    countryName: "Vietnam",
  },
  twitter: {
    card: "summary_large_image",
    site: "@Enterviu_official",
    creator: "@Enterviu_official",
    title: "Enterviu - Club Geoscience Engineering & Management",
    description: "Join Enterviu community for geoscience education, research collaboration, and professional development in earth sciences and engineering.",
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
  },
  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "apple-mobile-web-app-title": "Enterviu",
    "application-name": "Enterviu Platform",
    "msapplication-TileColor": "#3b82f6",
    "msapplication-TileImage": "/assets/logo/logo_web.jpg",
    "theme-color": "#3b82f6",
  },
};

interface RootLayoutProps {
  children: React.ReactNode
  params: Promise<{ locale: Locale }>
}

export default async function RootLayout({
  children,
  params,
}: RootLayoutProps) {
  const { locale } = await params
  
  return (
    <html
      lang={locale}
      dir="ltr"
      className="scroll-smooth"
      suppressHydrationWarning
    >
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="color-scheme" content="light dark" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen transition-colors duration-300`}
        suppressHydrationWarning={true}>
          <ThemeProvider attribute="class">
            <ReduxProvider>
              <ClientWrapper>
                <PageWrapper>
                  <div className="relative min-h-screen">
                    {/* Background Pattern */}
                    <div className="absolute inset-0 bg-grid-pattern opacity-5 dark:opacity-10"></div>

                    {/* Main Content */}
                    <div className="relative z-10">
                      {children}
                    </div>
                  </div>
                </PageWrapper>
              </ClientWrapper>
            </ReduxProvider>
          </ThemeProvider>
        </body>
      </html>
  )
}