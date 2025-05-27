"use client";

import { useParams, usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Languages } from "@/i18n.config";

const LanguagesSwitcher = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { locale } = useParams();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const switchLanguage = async (newLang: string) => {
    if (isTransitioning) return;
    
    setIsTransitioning(true);
    const path = pathname?.replace(`/${locale}`, `/${newLang}`) ?? `/${newLang}`;
    
    // Add a small delay for smooth transition
    setTimeout(() => {
      router.push(path);
      setIsTransitioning(false);
    }, 200);
  };

  const isVietnamese = locale === Languages.VIETNAMESE;

  return (
    <div className="flex items-center space-x-3 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Language Labels */}
      <span className={`text-sm font-medium transition-colors duration-200 ${
        isVietnamese ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
      }`}>
        VI
      </span>
      
      {/* Toggle Switch */}
      <div className="relative">
        <button
          onClick={() => switchLanguage(isVietnamese ? Languages.ENGLISH : Languages.VIETNAMESE)}
          disabled={isTransitioning}
          className={`
            relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out
            ${isVietnamese 
              ? 'bg-blue-600 hover:bg-blue-700' 
              : 'bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500'
            }
            ${isTransitioning ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800
          `}
          aria-label="Toggle language"
        >
          <span
            className={`
              inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out
              ${isVietnamese ? 'translate-x-1' : 'translate-x-6'}
              ${isTransitioning ? 'scale-90' : 'scale-100'}
            `}
          />
        </button>
      </div>
      
      <span className={`text-sm font-medium transition-colors duration-200 ${
        !isVietnamese ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
      }`}>
        EN
      </span>
      
      {/* Loading indicator */}
      {isTransitioning && (
        <div className="ml-2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
        </div>
      )}
    </div>
  );
};
export default LanguagesSwitcher;