import React from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';
import { 
  FallingText, 
  MagneticCard, 
  ScrollReveal,
  ShinyText,
  GradientOrb
} from '@/components/animations';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFacebook, 
  faTwitter, 
  faLinkedin, 
  faInstagram 
} from '@fortawesome/free-brands-svg-icons';

const Footer: React.FC = async () => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  const footerSections = [
    {
      key: 'company',
      links: ['about', 'team', 'careers', 'contact']
    },
    {
      key: 'products', 
      links: ['webDevelopment', 'mobileApps', 'aiSolutions', 'consulting']
    },
    {
      key: 'resources',
      links: ['documentation', 'blog', 'support', 'community']
    }
  ];

  const socialLinks = [
    { icon: faFacebook, name: 'Facebook', url: 'https://facebook.com' },
    { icon: faTwitter, name: 'Twitter', url: 'https://twitter.com' },
    { icon: faLinkedin, name: 'LinkedIn', url: 'https://linkedin.com' },
    { icon: faInstagram, name: 'Instagram', url: 'https://instagram.com' }
  ];

  return (
    <footer className="relative bg-gradient-to-br from-[color:var(--card)] to-[color:var(--muted)] border-t border-[color:var(--border)] overflow-hidden">
      {/* Background Effects */}
      <GradientOrb 
        size={200} 
        className="top-10 -left-10" 
        color1="rgba(59, 130, 246, 0.05)"
        color2="rgba(147, 51, 234, 0.05)"
        duration={20}
      />
      <GradientOrb 
        size={150} 
        className="bottom-10 -right-10" 
        color1="rgba(147, 51, 234, 0.05)"
        color2="rgba(236, 72, 153, 0.05)"
        duration={25}
        delay={5}
      />

      <div className="relative z-10">
        {/* Main Footer Content */}
        <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 py-16">
          <ScrollReveal direction="up" delay={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8">
              
              {/* Brand Section */}
              <div className="lg:col-span-2 space-y-6">
                <FallingText variant="bounce" delay={0.2}>
                  <ShinyText className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)]">
                    {t('common.branding')}
                  </ShinyText>
                </FallingText>
                
                <FallingText variant="fade" delay={0.3}>
                  <p className="text-[color:var(--muted-foreground)] leading-relaxed max-w-md">
                    {t('home.description')}
                  </p>
                </FallingText>

                {/* Social Links */}
                <ScrollReveal direction="left" delay={0.4}>
                  <div className="space-y-4">
                    <h4 className="font-semibold text-[color:var(--card-foreground)]">
                      {t('footer.social.followUs')}
                    </h4>
                    <div className="flex space-x-4 ">
                      {socialLinks.map((social, index) => (
                        <FallingText key={social.name} variant="scale" delay={0.1 * index}>
                          <MagneticCard strength={10}>
                            <a 
                              href={social.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="w-12 h-12 bg-gradient-to-br from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] rounded-xl flex items-center justify-center text-lg text-white hover:scale-110 transition-transform duration-300 group relative overflow-hidden"
                            >
                              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-500"></div>
                              <FontAwesomeIcon 
                                icon={social.icon} 
                                className="relative z-10 w-5 h-5 text-[color:var(--foreground)]" 
                              />
                            </a>
                          </MagneticCard>
                        </FallingText>
                      ))}
                    </div>
                  </div>
                </ScrollReveal>
              </div>

              {/* Footer Links */}
              {footerSections.map((section, sectionIndex) => (
                <div key={section.key} className="space-y-6">
                  <ScrollReveal direction="up" delay={0.2 + sectionIndex * 0.1}>
                    <FallingText variant="slide" delay={0.3}>
                      <h4 className="font-bold text-lg text-[color:var(--card-foreground)]">
                        {t(`footer.${section.key}.title`)}
                      </h4>
                    </FallingText>
                    
                    <ul className="space-y-3">
                      {section.links.map((link, linkIndex) => (
                        <li key={link}>
                          <FallingText variant="fade" delay={0.4 + linkIndex * 0.05}>
                            <MagneticCard strength={5}>
                              <a 
                                href="#" 
                                className="text-[color:var(--muted-foreground)] hover:text-[color:var(--primary)] transition-colors duration-300 hover:underline"
                              >
                                {t(`footer.${section.key}.${link}`)}
                              </a>
                            </MagneticCard>
                          </FallingText>
                        </li>
                      ))}
                    </ul>
                  </ScrollReveal>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>

        {/* Bottom Bar */}
        <ScrollReveal direction="up" delay={0.5}>
          <div className="border-t border-[color:var(--border)] bg-[color:var(--muted)]/50 backdrop-blur-sm">
            <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 py-6">
              <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                
                {/* Copyright */}
                <FallingText variant="fade" delay={0.6}>
                  <p className="text-[color:var(--muted-foreground)] text-sm">
                    {t('footer.copyright')}
                  </p>
                </FallingText>

                {/* Made with love */}
                <FallingText variant="fade" delay={0.7}>
                  <div className="flex items-center space-x-2 text-sm text-[color:var(--muted-foreground)]">
                    <span>{t('footer.madeWith')}</span>
                    <MagneticCard strength={15}>
                      <span className="text-red-500 hover:scale-125 transition-transform duration-300 cursor-pointer">
                        ❤️
                      </span>
                    </MagneticCard>
                    <span>{t('footer.location')}</span>
                  </div>
                </FallingText>

                {/* Legal Links */}
                <FallingText variant="fade" delay={0.8}>
                  <div className="flex space-x-6 text-sm">
                    <MagneticCard strength={5}>
                      <a href="#" className="text-[color:var(--muted-foreground)] hover:text-[color:var(--primary)] transition-colors duration-300">
                        {t('footer.legal.privacy')}
                      </a>
                    </MagneticCard>
                    <MagneticCard strength={5}>
                      <a href="#" className="text-[color:var(--muted-foreground)] hover:text-[color:var(--primary)] transition-colors duration-300">
                        {t('footer.legal.terms')}
                      </a>
                    </MagneticCard>
                    <MagneticCard strength={5}>
                      <a href="#" className="text-[color:var(--muted-foreground)] hover:text-[color:var(--primary)] transition-colors duration-300">
                        {t('footer.legal.cookies')}
                      </a>
                    </MagneticCard>
                  </div>
                </FallingText>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </footer>
  );
};

export default Footer; 