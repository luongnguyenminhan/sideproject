"use client";

import { useParams, usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faGlobe, faCheck } from "@fortawesome/free-solid-svg-icons";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { i18n, languages, type Locale } from "@/i18n.config";
import { VN, US } from "country-flag-icons/react/3x2";

interface LanguageSwitcherProps {
  align?: "start" | "center" | "end";
  side?: "top" | "right" | "bottom" | "left";
}

export default function LanguageSwitcher({ 
  align = "end", 
  side = "bottom" 
}: LanguageSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const [isPending, startTransition] = useTransition();
  
  const currentLocale = (params.locale as Locale) || i18n.defaultLocale;

  const switchLanguage = (newLocale: Locale) => {
    if (newLocale === currentLocale || isPending) return;

    startTransition(() => {
      // Thay thế locale trong pathname
      const segments = pathname.split('/');
      segments[1] = newLocale;
      const newPathname = segments.join('/');
      
      router.push(newPathname);
      router.refresh();
    });
  };

  const getFlagComponent = (locale: Locale) => {
    const countryCode = languages[locale].countryCode;
    const commonProps = { 
      className: "w-5 h-4 object-cover rounded-sm",
      title: languages[locale].name 
    };
    
    switch (countryCode) {
      case 'VN':
        return <VN {...commonProps} />;
      case 'US':
        return <US {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="icon" 
          className="relative"
          disabled={isPending}
        >
          <FontAwesomeIcon icon={faGlobe} className="h-[1.2rem] w-[1.2rem]" />
          <span className="sr-only">Change language</span>
          {isPending && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
            </div>
          )}
        </Button>
      </DropdownMenuTrigger>      <DropdownMenuContent align={align} side={side}>
        {i18n.locales.map((locale) => (
          <DropdownMenuItem
            key={locale}
            onClick={() => switchLanguage(locale)}
            className="cursor-pointer"
            disabled={isPending}
          >
            <div className="flex items-center gap-2">
              {getFlagComponent(locale)}
              <span>{languages[locale].name}</span>
            </div>
            {currentLocale === locale && (
              <FontAwesomeIcon icon={faCheck} className="ml-auto h-4 w-4" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
      </DropdownMenu>
  );
}