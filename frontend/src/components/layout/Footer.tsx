import React from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';
import { 
  FallingText, 
  ScrollReveal,
  ShinyText,
  GradientOrb
} from '@/components/animations';
import { LiquidGlass } from '@/components/ui';
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
    <footer className="relative bg-gradient-to-br from-slate-50/80 to-blue-50/60 dark:from-slate-900/80 dark:to-blue-950/60 border-t border-white/20 dark:border-white/10 backdrop-blur-sm overflow-hidden">
      {/* Background Effects */}
      <GradientOrb 
        size={200} 
        className="top-10 -left-10" 
        color1="rgba(59, 130, 246, 0.03)"
        color2="rgba(147, 51, 234, 0.03)"
        duration={20}
      />
      <GradientOrb 
        size={150} 
        className="bottom-10 -right-10" 
        color1="rgba(147, 51, 234, 0.03)"
        color2="rgba(236, 72, 153, 0.03)"
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
                  <p className="text-gray-600 dark:text-gray-300 leading-relaxed max-w-md">
                    {t('home.description')}
                  </p>
                </FallingText>

                {/* Social Links */}
                <ScrollReveal direction="left" delay={0.4}>
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-800 dark:text-gray-100">
                      {t('footer.social.followUs')}
                    </h4>
                    <div className="flex space-x-4 ">
                      {socialLinks.map((social, index) => (
                        <FallingText key={social.name} variant="scale" delay={0.1 * index}>
                          <LiquidGlass 
                            variant="card" 
                            blur="md" 
                            rounded="xl" 
                            hover={true}
                            className="w-12 h-12 flex items-center justify-center group"
                          >
                            <a 
                              href={social.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="w-full h-full flex items-center justify-center text-lg group-hover:scale-110 transition-transform duration-300"
                            >
                              <FontAwesomeIcon 
                                icon={social.icon} 
                                className="w-5 h-5 text-blue-600 dark:text-blue-400" 
                              />
                            </a>
                          </LiquidGlass>
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
                      <h4 className="font-bold text-lg text-gray-800 dark:text-gray-100">
                        {t(`footer.${section.key}.title`)}
                      </h4>
                    </FallingText>
                    
                    <ul className="space-y-3">
                      {section.links.map((link, linkIndex) => (
                        <li key={link}>
                          <FallingText variant="fade" delay={0.4 + linkIndex * 0.05}>
                            <a 
                              href="#" 
                              className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-300"
                            >
                              {t(`footer.${section.key}.${link}`)}
                            </a>
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
          <LiquidGlass 
            variant="card" 
            blur="md" 
            border={true} 
            className="border-t"
          >
            <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 py-6">
              <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                
                {/* Copyright */}
                <FallingText variant="fade" delay={0.6}>
                  <p className="text-gray-600 dark:text-gray-300 text-sm">
                    {t('footer.copyright')}
                  </p>
                </FallingText>

                {/* Made with love */}
                <FallingText variant="fade" delay={0.7}>
                  <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
                    <span>{t('footer.madeWith')}</span>
                      <span className="text-red-500 hover:scale-125 transition-transform duration-300 cursor-pointer">
                        ❤️
                      </span>
                    <span>{t('footer.location')}</span>
                  </div>
                </FallingText>

                {/* Legal Links */}
                <FallingText variant="fade" delay={0.8}>
                  <div className="flex space-x-6 text-sm">
                      <a href="#" className="text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-300">
                        {t('footer.legal.privacy')}
                      </a>
                      <a href="#" className="text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-300">
                        {t('footer.legal.terms')}
                      </a>
                      <a href="#" className="text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-300">
                        {t('footer.legal.cookies')}
                      </a>
                  </div>
                </FallingText>
              </div>
            </div>
          </LiquidGlass>
        </ScrollReveal>
      </div>
    </footer>
  );
};

export default Footer; 