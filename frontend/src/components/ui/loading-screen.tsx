import Image from 'next/image'

// Simple loading screen server component
interface LoadingScreenProps {
    isLoading?: boolean
}

export default function LoadingScreen({ isLoading = true }: LoadingScreenProps) {
    if (!isLoading) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-gray-900">
            <div className="flex flex-col items-center space-y-6">
                {/* Logo */}
                <div className="relative w-24 h-24 md:w-32 md:h-32">
                    <Image
                        src="/assets/logo/logo_web.jpg"
                        alt="Enterview Logo"
                        fill
                        className="object-contain rounded-full"
                        priority
                    />
                </div>
                
                {/* Spinner */}
                <div className="relative">
                    <div className="w-8 h-8 border-4 border-gray-200 dark:border-gray-700 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
                
                {/* Loading Text */}
                <div className="text-gray-600 dark:text-gray-400 text-sm font-medium">
                    Loading...
                </div>
            </div>
        </div>
    )
}
