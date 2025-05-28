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
  description: "A modern Next.js application with internationalization and theme support",
  keywords: ["Next.js", "React", "TypeScript", "i18n", "Internationalization", "Dark Mode"],
  authors: [{ name: "Your Name" }],
  creator: "Your Name",
  metadataBase: new URL("https://your-domain.com"),
  openGraph: {
    type: "website",
    locale: "vi_VN",
    url: "https://your-domain.com",
    title: "CGSEM",
    description: "A modern Next.js application with internationalization and theme support",
    siteName: "CGSEM",
  },
  twitter: {
    card: "summary_large_image",
    title: "CGSEM",
    description: "A modern Next.js application with internationalization and theme support",
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