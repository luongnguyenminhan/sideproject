"use client"
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

type Theme = 'light' | 'dark' | 'system'

const ThemeSwapper = () => {
    const [theme, setTheme] = useState<Theme>('system')
    const [mounted, setMounted] = useState(false)

    // Function to apply theme to document
    const applyTheme = (newTheme: Theme) => {
        const html = document.documentElement
        
        if (newTheme === 'system') {
            // Remove data-theme attribute to let system preference take over
            html.removeAttribute('data-theme')
            localStorage.removeItem('theme')
        } else {
            html.setAttribute('data-theme', newTheme)
            localStorage.setItem('theme', newTheme)
        }
    }

    // Function to get current effective theme
    const getEffectiveTheme = (): 'light' | 'dark' => {
        const html = document.documentElement
        const dataTheme = html.getAttribute('data-theme')
        
        if (dataTheme === 'light' || dataTheme === 'dark') {
            return dataTheme
        }
        
        // If no data-theme, check system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }

    // Initialize theme on mount
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme') as Theme
        
        if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
            setTheme(savedTheme)
            applyTheme(savedTheme)
        } else {
            // Default to system
            setTheme('system')
            applyTheme('system')
        }
        
        setMounted(true)
    }, [])

    // Listen for system theme changes
    useEffect(() => {
        if (!mounted) return

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handleChange = () => {
            // Only update if current theme is system
            if (theme === 'system') {
                // Force a re-render to update the icon
                setTheme('system')
            }
        }

        mediaQuery.addEventListener('change', handleChange)
        return () => mediaQuery.removeEventListener('change', handleChange)
    }, [mounted, theme])

    const handleThemeChange = () => {
        let newTheme: Theme
        
        if (theme === 'light') {
            newTheme = 'dark'
        } else {
            newTheme = 'light'
        }
        
        setTheme(newTheme)
        applyTheme(newTheme)
    }

    // Don't render anything until mounted to prevent hydration mismatch
    if (!mounted) {
        return (
            <motion.div 
              className="bg-[color:var(--card)]/80 backdrop-blur-xl p-3 rounded-2xl shadow-lg border border-[color:var(--border)]/30"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
                <div className="h-6 w-6 bg-[color:var(--muted)] rounded animate-pulse" />
            </motion.div>
        )
    }

    const effectiveTheme = getEffectiveTheme()
    
    const getThemeIcon = () => {
        if (effectiveTheme === 'dark') {
            return (
                // Sun icon for dark mode (click to switch)
                <motion.svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-6 w-6 text-yellow-400" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                  initial={{ rotate: 0, scale: 0 }}
                  animate={{ rotate: 180, scale: 1 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </motion.svg>
            )
        } else {
            return (
                // Moon icon for light mode (click to switch)
                <motion.svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-6 w-6 text-[color:var(--foreground)]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                  initial={{ rotate: 180, scale: 0 }}
                  animate={{ rotate: 0, scale: 1 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </motion.svg>
            )
        }
    }

    const getTooltipText = () => {
        if (theme === 'light') return 'Switch to dark mode'
        if (theme === 'dark') return 'Switch to system mode'
        return 'Switch to light mode'
    }

    return (
        <div className="relative inline-block">
            <motion.button
                onClick={handleThemeChange}
                className="bg-[color:var(--card)]/90 hover:bg-[color:var(--card)] p-2.5 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-[color:var(--border)]/50 backdrop-blur-xl relative overflow-hidden group"
                aria-label="Toggle theme"
                title={getTooltipText()}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
            >
                {                /* Hover background gradient */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-[color:var(--feature-yellow)]/20 to-[color:var(--feature-blue)]/20 rounded-xl"
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                />

                {                /* Glow effect */}
                <motion.div
                  className="absolute inset-0 rounded-xl"
                  animate={{
                    boxShadow: effectiveTheme === 'dark' 
                      ? ['0 0 20px rgba(251, 191, 36, 0.3)', '0 0 40px rgba(251, 191, 36, 0.5)', '0 0 20px rgba(251, 191, 36, 0.3)']
                      : ['0 0 20px rgba(99, 102, 241, 0.3)', '0 0 40px rgba(99, 102, 241, 0.5)', '0 0 20px rgba(99, 102, 241, 0.3)']
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />

                <div className="relative z-10">
                  <AnimatePresence mode="wait">
                    {getThemeIcon()}
                  </AnimatePresence>
                </div>
            </motion.button>
            
            {/* Enhanced theme indicator */}
            <motion.div 
              className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-[color:var(--card)] shadow-lg"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, duration: 0.4 }}
            >
                <AnimatePresence mode="wait">
                  {theme === 'dark' && (
                      <motion.div 
                        className="w-full h-full bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full" 
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ scale: 1, rotate: 0 }}
                        exit={{ scale: 0, rotate: 180 }}
                        transition={{ duration: 0.3 }}
                      />
                  )}
                  {theme === 'light' && (
                      <motion.div 
                        className="w-full h-full bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full" 
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ scale: 1, rotate: 0 }}
                        exit={{ scale: 0, rotate: 180 }}
                        transition={{ duration: 0.3 }}
                      />
                  )}
                  {theme === 'system' && (
                      <motion.div 
                        className="w-full h-full bg-gradient-to-r from-gray-400 to-gray-600 rounded-full" 
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ scale: 1, rotate: 0 }}
                        exit={{ scale: 0, rotate: 180 }}
                        transition={{ duration: 0.3 }}
                      />
                  )}
                </AnimatePresence>
            </motion.div>
            
            {            /* Floating particles effect */}
            <div className="absolute inset-0 pointer-events-none">
              {Array.from({ length: 2 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-0.5 h-0.5 rounded-full"
                  style={{
                    background: effectiveTheme === 'dark' ? '#fbbf24' : '#6366f1',
                    left: `${25 + i * 25}%`,
                    top: `${15 + i * 20}%`,
                  }}
                  animate={{
                    y: [-3, -8, -3],
                    opacity: [0.4, 0.8, 0.4],
                    scale: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.4,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
            
            {/* Screen reader only text */}
            <span className="sr-only">Current theme: {theme}</span>
        </div>
    )
}

export default ThemeSwapper