import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import getDictionary, { createTranslator } from '@/utils/translation';
import { 
  FallingText, 
  MagneticCard, 
  ScrollReveal,
  ShinyText
} from '@/components/animations';

const TeamSection: React.FC = async () => {
  const currentLocale = await getCurrentLocale();
  const dictionary = await getDictionary(currentLocale);
  const t = createTranslator(dictionary);

  const teamMembers = [
    {
      key: 'ceo',
      avatar: '👨‍💼',
      color: 'from-[color:var(--feature-blue)] to-[color:var(--feature-blue)]/80'
    },
    {
      key: 'cto', 
      avatar: '👨‍💻',
      color: 'from-[color:var(--feature-purple)] to-[color:var(--feature-purple)]/80'
    },
    {
      key: 'designer',
      avatar: '🎨',
      color: 'from-[color:var(--feature-green)] to-[color:var(--feature-green)]/80'
    }
  ];

  const values = [
    {
      key: 'innovation',
      icon: '💡',
      color: 'from-[color:var(--feature-yellow)] to-[color:var(--feature-yellow)]/80'
    },
    {
      key: 'quality',
      icon: '⭐',
      color: 'from-[color:var(--feature-blue)] to-[color:var(--feature-blue)]/80'
    },
    {
      key: 'community',
      icon: '🤝',
      color: 'from-[color:var(--feature-green)] to-[color:var(--feature-green)]/80'
    }
  ];

  return (
    <section className="py-20 px-6 sm:px-8 lg:px-12">
      <div className="max-w-6xl mx-auto">
        {/* Team Header */}
        <ScrollReveal direction="up" delay={0.1}>
          <div className="text-center mb-20">
            <FallingText variant="bounce" delay={0.2}>
              <ShinyText className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] mb-6">
                {t('team.title')}
              </ShinyText>
            </FallingText>
            <FallingText variant="fade" delay={0.4}>
              <p className="text-xl md:text-2xl text-[color:var(--muted-foreground)] max-w-3xl mx-auto">
                {t('team.subtitle')}
              </p>
            </FallingText>
          </div>
        </ScrollReveal>

        {/* Leadership Team */}
        <ScrollReveal direction="up" delay={0.2}>
          <div className="mb-20">
            <FallingText variant="slide" delay={0.3}>
              <h3 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)]">
                {t('team.leadership.title')}
              </h3>
            </FallingText>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {teamMembers.map((member, index) => (
                <ScrollReveal key={member.key} direction="up" delay={0.1 * (index + 1)}>
                  <MagneticCard strength={15}>
                    <Card className="bg-[color:var(--card)] border-[color:var(--border)] shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 backdrop-blur-sm h-full group">
                      <CardContent className="p-8 text-center space-y-6">
                        {/* Avatar */}
                        <div className={`w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br ${member.color} flex items-center justify-center text-4xl group-hover:scale-110 transition-transform duration-300`}>
                          {member.avatar}
                        </div>

                        {/* Name */}
                        <FallingText variant="fade" delay={0.2}>
                          <h4 className="text-2xl font-bold text-[color:var(--card-foreground)]">
                            {t(`team.leadership.${member.key}.name`)}
                          </h4>
                        </FallingText>

                        {/* Role */}
                        <FallingText variant="slide" delay={0.3}>
                          <p className="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)]">
                            {t(`team.leadership.${member.key}.role`)}
                          </p>
                        </FallingText>

                        {/* Bio */}
                        <FallingText variant="fade" delay={0.4}>
                          <p className="text-[color:var(--muted-foreground)] leading-relaxed">
                            {t(`team.leadership.${member.key}.bio`)}
                          </p>
                        </FallingText>

                        {/* Experience */}
                        <FallingText variant="scale" delay={0.5}>
                          <div className={`inline-block px-4 py-2 rounded-full bg-gradient-to-r ${member.color} text-sm font-semibold`}>
                            {t(`team.leadership.${member.key}.experience`)}
                          </div>
                        </FallingText>
                      </CardContent>
                    </Card>
                  </MagneticCard>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </ScrollReveal>

        {/* Core Values */}
        <ScrollReveal direction="up" delay={0.3}>
          <div>
            <FallingText variant="slide" delay={0.2}>
              <h3 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)]">
                {t('team.values.title')}
              </h3>
            </FallingText>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {values.map((value, index) => (
                <ScrollReveal key={value.key} direction="up" delay={0.1 * (index + 1)}>
                  <MagneticCard strength={20}>
                    <Card className="bg-[color:var(--card)] border-[color:var(--border)] shadow-lg hover:shadow-[var(--card-hover-shadow)] transition-all duration-500 backdrop-blur-sm h-full group relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
                      
                      <CardContent className="p-8 text-center space-y-6 relative z-10">
                        {/* Icon */}
                        <div className={`w-16 h-16 mx-auto rounded-xl bg-gradient-to-br ${value.color} flex items-center justify-center text-3xl group-hover:scale-110 group-hover:rotate-12 transition-all duration-300`}>
                          {value.icon}
                        </div>

                        {/* Title */}
                        <FallingText variant="bounce" delay={0.2}>
                          <h4 className="text-xl font-bold text-[color:var(--card-foreground)]">
                            {t(`team.values.${value.key}.title`)}
                          </h4>
                        </FallingText>

                        {/* Description */}
                        <FallingText variant="fade" delay={0.3}>
                          <p className="text-[color:var(--muted-foreground)] leading-relaxed">
                            {t(`team.values.${value.key}.description`)}
                          </p>
                        </FallingText>
                      </CardContent>
                    </Card>
                  </MagneticCard>
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