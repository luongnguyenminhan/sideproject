'use client'

import React from 'react'

interface TypingIndicatorProps {
  variant?: 'dots' | 'pulse' | 'wave'
  size?: 'sm' | 'md' | 'lg'
  color?: string
  text?: string
  className?: string
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  variant = 'dots',
  size = 'md',
  color = 'var(--primary)',
  text,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  }

  const containerClasses = {
    sm: 'space-x-0.5',
    md: 'space-x-1',
    lg: 'space-x-1.5'
  }

  if (variant === 'dots') {
    return (
      <div className={`flex items-center ${containerClasses[size]} ${className}`}>
        {text && (
          <span className="text-sm text-[color:var(--muted-foreground)] mr-2">
            {text}
          </span>
        )}
        <div className="flex space-x-1">
          <div 
            className={`${sizeClasses[size]} rounded-full animate-bounce`}
            style={{ 
              backgroundColor: `color-mix(in srgb, ${color} 80%, transparent)`,
              animationDelay: '0ms',
              animationDuration: '1.4s',
              animationIterationCount: 'infinite'
            }}
          />
          <div 
            className={`${sizeClasses[size]} rounded-full animate-bounce`}
            style={{ 
              backgroundColor: `color-mix(in srgb, ${color} 80%, transparent)`,
              animationDelay: '200ms',
              animationDuration: '1.4s',
              animationIterationCount: 'infinite'
            }}
          />
          <div 
            className={`${sizeClasses[size]} rounded-full animate-bounce`}
            style={{ 
              backgroundColor: `color-mix(in srgb, ${color} 80%, transparent)`,
              animationDelay: '400ms',
              animationDuration: '1.4s',
              animationIterationCount: 'infinite'
            }}
          />
        </div>
      </div>
    )
  }

  if (variant === 'pulse') {
    return (
      <div className={`flex items-center ${className}`}>
        {text && (
          <span className="text-sm text-[color:var(--muted-foreground)] mr-2">
            {text}
          </span>
        )}
        <div 
          className={`${sizeClasses[size]} rounded-full animate-pulse`}
          style={{ 
            backgroundColor: `color-mix(in srgb, ${color} 60%, transparent)`,
            animationDuration: '1s'
          }}
        />
      </div>
    )
  }

  if (variant === 'wave') {
    return (
      <div className={`flex items-center ${className}`}>
        {text && (
          <span className="text-sm text-[color:var(--muted-foreground)] mr-2">
            {text}
          </span>
        )}
        <div className="flex space-x-0.5">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`w-1 bg-opacity-60 rounded-full animate-pulse`}
              style={{
                height: size === 'sm' ? '8px' : size === 'md' ? '12px' : '16px',
                backgroundColor: `color-mix(in srgb, ${color} 70%, transparent)`,
                animationDelay: `${i * 100}ms`,
                animationDuration: '1.2s',
                animationIterationCount: 'infinite'
              }}
            />
          ))}
        </div>
      </div>
    )
  }

  return null
}

// Predefined typing indicator components for common use cases
export const DotsTypingIndicator: React.FC<{ text?: string; className?: string }> = ({ text, className }) => (
  <TypingIndicator variant="dots" text={text} className={className} />
)

export const PulseTypingIndicator: React.FC<{ text?: string; className?: string }> = ({ text, className }) => (
  <TypingIndicator variant="pulse" text={text} className={className} />
)

export const WaveTypingIndicator: React.FC<{ text?: string; className?: string }> = ({ text, className }) => (
  <TypingIndicator variant="wave" text={text} className={className} />
)
