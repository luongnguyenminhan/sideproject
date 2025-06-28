import React from 'react';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';
import { 
  FallingText, 
  ScrollReveal,
  ShinyText
} from '@/components/animations';
import { LiquidGlass } from '@/components/ui';

const TeamSection: React.FC = async () => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  const teamMembers = [
    {
      key: 'ceo',
      avatar: '👨‍💼',
      color: 'from-blue-500/20 to-blue-600/30'
    },
    {
      key: 'cto', 
      avatar: '👨‍💻',
      color: 'from-purple-500/20 to-purple-600/30'
    },
    {
      key: 'designer',
      avatar: '🎨',
      color: 'from-green-500/20 to-green-600/30'
    }
  ];

  const values = [
    {
      key: 'innovation',
      icon: '💡',
      color: 'from-yellow-500/20 to-yellow-600/30'
    },
    {
      key: 'quality',
      icon: '⭐',
      color: 'from-blue-500/20 to-blue-600/30'
    },
    {
      key: 'community',
      icon: '🤝',
      color: 'from-green-500/20 to-green-600/30'
    }
  ];

  return (
    <section className="py-20 px-6 sm:px-8 lg:px-12">
      <div className="max-w-6xl mx-auto">
        {/* Team Header */}
        <ScrollReveal direction="up" delay={0.1}>
          <div className="text-center mb-20">
            <FallingText variant="bounce" delay={0.2}>
              <ShinyText className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 dark:from-blue-400 dark:via-purple-400 dark:to-pink-400 mb-6">
                {t('team.title')}
              </ShinyText>
            </FallingText>
            <FallingText variant="fade" delay={0.4}>
              <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                {t('team.subtitle')}
              </p>
            </FallingText>
          </div>
        </ScrollReveal>

        {/* Leadership Team */}
        <ScrollReveal direction="up" delay={0.2}>
          <div className="mb-20">
            <FallingText variant="slide" delay={0.3}>
              <h3 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                {t('team.leadership.title')}
              </h3>
            </FallingText>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {teamMembers.map((member, index) => (
                <ScrollReveal key={member.key} direction="up" delay={0.1 * (index + 1)}>
                  <LiquidGlass 
                    variant="card" 
                    blur="lg" 
                    rounded="2xl" 
                    shadow="xl" 
                    hover={true}
                    className="p-8 h-full group"
                  >
                    <div className="text-center space-y-6">
                      {/* Avatar */}
                      <div className={`w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br ${member.color} backdrop-blur-sm border border-white/20 flex items-center justify-center text-4xl group-hover:scale-110 transition-transform duration-300`}>
                        {member.avatar}
                      </div>

                      {/* Name */}
                      <FallingText variant="fade" delay={0.2}>
                        <h4 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                          {t(`team.leadership.${member.key}.name`)}
                        </h4>
                      </FallingText>

                      {/* Role */}
                      <FallingText variant="slide" delay={0.3}>
                        <p className="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                          {t(`team.leadership.${member.key}.role`)}
                        </p>
                      </FallingText>

                      {/* Bio */}
                      <FallingText variant="fade" delay={0.4}>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                          {t(`team.leadership.${member.key}.bio`)}
                        </p>
                      </FallingText>

                      {/* Experience */}
                      <FallingText variant="scale" delay={0.5}>
                        <LiquidGlass 
                          variant="subtle" 
                          rounded="3xl" 
                          className="inline-block px-4 py-2"
                        >
                          <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">
                            {t(`team.leadership.${member.key}.experience`)}
                          </span>
                        </LiquidGlass>
                      </FallingText>
                    </div>
                  </LiquidGlass>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </ScrollReveal>

        {/* Core Values */}
        <ScrollReveal direction="up" delay={0.3}>
          <div>
            <FallingText variant="slide" delay={0.2}>
              <h3 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                {t('team.values.title')}
              </h3>
            </FallingText>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {values.map((value, index) => (
                <ScrollReveal key={value.key} direction="up" delay={0.1 * (index + 1)}>
                  <LiquidGlass 
                    variant="card" 
                    blur="lg" 
                    rounded="2xl" 
                    shadow="xl" 
                    hover={true}
                    className="p-8 h-full group relative"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                    
                    <div className="text-center space-y-6 relative z-10">
                      {/* Icon */}
                      <div className={`w-16 h-16 mx-auto rounded-xl bg-gradient-to-br ${value.color} backdrop-blur-sm border border-white/20 flex items-center justify-center text-3xl group-hover:scale-110 group-hover:rotate-12 transition-all duration-300`}>
                        {value.icon}
                      </div>

                      {/* Title */}
                      <FallingText variant="bounce" delay={0.2}>
                        <h4 className="text-xl font-bold text-gray-800 dark:text-gray-100">
                          {t(`team.values.${value.key}.title`)}
                        </h4>
                      </FallingText>

                      {/* Description */}
                      <FallingText variant="fade" delay={0.3}>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                          {t(`team.values.${value.key}.description`)}
                        </p>
                      </FallingText>
                    </div>
                  </LiquidGlass>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};

export default TeamSection; 