import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { FacebookPageInfo } from "@/types/facebook.type";
import { getCurrentLocale } from "@/utils/getCurrentLocale";
import getDictionary, { createTranslator } from "@/utils/translation";
import Image from "next/image";
import {
  FallingText,
  MagneticCard,
  ScrollReveal,
  AnimatedRibbon,
} from "@/components/animations";

interface AboutUsSectionProps {
  pageInfo: FacebookPageInfo;
  locale?: string;
}

const AboutUsSection: React.FC<AboutUsSectionProps> = async ({ pageInfo }) => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  return (
    <section className="relative py-12">
      <div className="max-w-screen mx-auto">
        {/* Facebook Page Info Card */}
        {pageInfo && (
          <ScrollReveal direction="up" delay={0.2}>
            <div className="mb-12 relative">
              <AnimatedRibbon
                count={3}
                thickness={20}
                speed={0.3}
                className="opacity-30"
              />

              <MagneticCard strength={12}>
                <Card className="bg-[color:var(--card)] border-[color:var(--border)] shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 backdrop-blur-sm bg-gradient-to-br from-[color:var(--card)] to-[color:var(--card)]/90 relative overflow-hidden group">
                  {/* Animated background effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>

                  <CardHeader className="text-center relative z-10">
                    <FallingText variant="bounce" delay={0.3}>
                      <div className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
                        {t("aboutUs.title") || "About Us"}
                      </div>
                    </FallingText>
                  </CardHeader>

                  <CardContent className="space-y-8 relative z-10">
                    {/* Page Profile Section */}
                    <div className="flex flex-col md:flex-row items-center gap-8">
                      {/* Profile Picture */}
                      {pageInfo.picture?.data?.url && (
                        <FallingText variant="scale" delay={0.4}>
                          <MagneticCard strength={15}>
                            <div className="flex-shrink-0 relative group/avatar">
                              <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--feature-blue)] via-[color:var(--feature-purple)] to-[color:var(--feature-blue)] rounded-full opacity-75 blur-lg group-hover/avatar:opacity-100 group-hover/avatar:scale-110 transition-all duration-500"></div>
                              <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--feature-purple)] to-[color:var(--feature-blue)] rounded-full opacity-50 blur-md animate-pulse"></div>
                              <Image
                                src={pageInfo.picture.data.url}
                                alt={pageInfo.name || "Facebook Page"}
                                className="relative w-28 h-28 md:w-36 md:h-36 rounded-full border-4 border-[color:var(--feature-blue)] shadow-2xl object-cover transition-transform duration-500 group-hover/avatar:scale-105 group-hover/avatar:rotate-3"
                                width={1920}
                                height={1920}
                              />
                            </div>
                          </MagneticCard>
                        </FallingText>
                      )}

                      {/* Page Information */}
                      <div className="flex-1 text-center md:text-left space-y-4">
                        {pageInfo.name && (
                          <FallingText variant="slide" delay={0.5}>
                            <div className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)]">
                              {pageInfo.name}
                            </div>
                          </FallingText>
                        )}

                        {/* Followers Count & Email */}
                        {pageInfo.followers_count !== undefined && (
                          <FallingText variant="fade" delay={0.6}>
                            <div className="flex items-center justify-center md:justify-start gap-4 flex-wrap">
                              <MagneticCard strength={8}>
                                <div className="flex items-center gap-2 bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-blue)]/80 px-4 py-2 rounded-full group relative overflow-hidden">
                                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                                  <svg
                                    className="w-5 h-5 text-[color:var(--feature-blue-text)] relative z-10"
                                    fill="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                                  </svg>
                                  <span className="text-sm font-semibold text-[color:var(--feature-blue-text)] relative z-10">
                                    {pageInfo.followers_count?.toLocaleString()}{" "}
                                    {t("aboutUs.social.followers") ||
                                      "followers"}
                                  </span>
                                </div>
                              </MagneticCard>

                              {pageInfo.emails?.[0] && (
                                <MagneticCard strength={8}>
                                  <div className="flex items-center gap-2 bg-gradient-to-r from-[color:var(--feature-green)] to-[color:var(--feature-green)]/80 px-4 py-2 rounded-full group relative overflow-hidden">
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                                    <svg
                                      className="w-4 h-4 text-[color:var(--feature-green-text)] relative z-10"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                      />
                                    </svg>
                                    <span className="text-sm font-semibold text-[color:var(--feature-green-text)] relative z-10">
                                      {pageInfo.emails[0]}
                                    </span>
                                  </div>
                                </MagneticCard>
                              )}
                            </div>
                          </FallingText>
                        )}

                        {/* About Section */}
                        {pageInfo.about && (
                          <FallingText variant="fade" delay={0.7}>
                            <div className="space-y-3">
                              <h4 className="text-sm font-bold text-[color:var(--muted-foreground)] uppercase tracking-wide">
                                {t("aboutUs.social.about") || "About"}
                              </h4>
                              <p className="text-[color:var(--card-foreground)] leading-relaxed text-lg">
                                {pageInfo.about}
                              </p>
                            </div>
                          </FallingText>
                        )}
                      </div>
                    </div>

                    {/* Stats & Links Grid */}
                    <ScrollReveal direction="up" delay={0.8}>
                      <div className="pt-6 border-t border-[color:var(--border)]">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          {/* Facebook Link */}
                          <MagneticCard strength={15}>
                            <div className="h-32 text-center p-6 bg-gradient-to-br from-[color:var(--feature-blue)] to-[color:var(--feature-blue)]/80 rounded-2xl group relative overflow-hidden transition-all duration-500 hover:shadow-lg hover:scale-105 flex flex-col justify-center">
                              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                              <a
                                href="https://www.facebook.com/cangiuocschoolmedia"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block relative z-10 hover:opacity-80 transition-opacity"
                              >
                                <div className="w-10 h-10 mx-auto mb-3 bg-white/20 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                  <svg
                                    className="w-6 h-6 text-[color:var(--feature-blue-text)]"
                                    fill="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                                  </svg>
                                </div>
                                <span className="text-sm font-semibold text-[color:var(--feature-blue-text)] truncate">
                                  CLB Truyền Thông và Sự Kiện Trường THPT Cần Giuộc
                                </span>
                              </a>
                            </div>
                          {/* Address */}
                          </MagneticCard>
                          {pageInfo.single_line_address && (
                            <MagneticCard strength={15}>
                              <div className="h-32 text-center p-6 bg-gradient-to-br from-[color:var(--feature-yellow)] to-[color:var(--feature-yellow)]/80 rounded-2xl group relative overflow-hidden transition-all duration-500 hover:shadow-lg hover:scale-105 flex flex-col justify-center">
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                                <div className="relative z-10">
                                  <div className="w-10 h-10 mx-auto mb-3 bg-white/20 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                    <svg
                                      className="w-6 h-6 text-[color:var(--feature-yellow-text)]"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                                      />
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                                      />
                                    </svg>
                                  </div>
                                  <span className="text-sm font-semibold text-[color:var(--feature-yellow-text)] block truncate">
                                    {pageInfo.single_line_address}
                                  </span>
                                </div>
                              </div>
                            </MagneticCard>
                          )}{" "}
                          {/* Contact */}
                          {pageInfo.emails && pageInfo.emails.length > 0 && (
                            <MagneticCard strength={15}>
                              <div className="h-32 text-center p-6 bg-gradient-to-br from-[color:var(--feature-green)] to-[color:var(--feature-green)]/80 rounded-2xl group relative overflow-hidden transition-all duration-500 hover:shadow-lg hover:scale-105 flex flex-col justify-center">
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                                <div className="relative z-10">
                                  <div className="w-10 h-10 mx-auto mb-3 bg-white/20 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                    <svg
                                      className="w-6 h-6 text-[color:var(--feature-green-text)]"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                      />
                                    </svg>
                                  </div>
                                  <span className="text-sm font-semibold text-[color:var(--feature-green-text)] block truncate">
                                    {pageInfo.emails[0]}
                                  </span>
                                </div>
                              </div>
                            </MagneticCard>
                          )}
                        </div>
                      </div>
                    </ScrollReveal>
                  </CardContent>
                </Card>
              </MagneticCard>
            </div>
          </ScrollReveal>
        )}
      </div>
    </section>
  );
};

export default AboutUsSection;
