import React from 'react';
import { 
  ParticleBackground, 
  GradientOrb, 
  AnimatedRibbon 
} from '@/components/animations';

interface HomePageWrapperProps {
  children: React.ReactNode;
}

export default function HomePageWrapper({ children }: HomePageWrapperProps) {
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

      {children}
    </div>
  );
}
