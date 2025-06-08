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