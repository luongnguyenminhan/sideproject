

"use client"
import { useEffect, useState } from 'react'

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
        } else if (theme === 'dark') {
            newTheme = 'system'
        } else {
            newTheme = 'light'
        }
        
        setTheme(newTheme)
        applyTheme(newTheme)
    }

    // Don't render anything until mounted to prevent hydration mismatch
    if (!mounted) {
        return (
            <div className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-lg">
                <div className="h-6 w-6 bg-gray-200 dark:bg-gray-600 rounded animate-pulse" />
            </div>
        )
    }

    const effectiveTheme = getEffectiveTheme()
    
    const getThemeIcon = () => {
        if (theme === 'system') {
            return (
                // System icon
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
            )
        } else if (effectiveTheme === 'dark') {
            return (
                // Sun icon for dark mode (click to switch)
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            )
        } else {
            return (
                // Moon icon for light mode (click to switch)
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
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
            <button
                onClick={handleThemeChange}
                className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-700 hover:scale-105"
                aria-label="Toggle theme"
                title={getTooltipText()}
            >
                {getThemeIcon()}
            </button>
            
            {/* Optional: Show current theme indicator */}
            <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 shadow-sm">
                {theme === 'system' && (
                    <div className="w-full h-full bg-blue-500 rounded-full" />
                )}
                {theme === 'dark' && (
                    <div className="w-full h-full bg-indigo-600 rounded-full" />
                )}
                {theme === 'light' && (
                    <div className="w-full h-full bg-yellow-400 rounded-full" />
                )}
            </div>
            
            {/* Screen reader only text */}
            <span className="sr-only">Current theme: {theme}</span>
        </div>
    )
}

export default ThemeSwapper