"use client";

import { useParams, usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";
import { Globe, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { i18n, languages, type Locale } from "@/i18n.config";

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

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="icon" 
          className="relative"
          disabled={isPending}
        >
          <Globe className="h-[1.2rem] w-[1.2rem]" />
          <span className="sr-only">Change language</span>
          {isPending && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
            </div>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} side={side}>
        {i18n.locales.map((locale) => (
          <DropdownMenuItem
            key={locale}
            onClick={() => switchLanguage(locale)}
            className="cursor-pointer"
            disabled={isPending}
          >
            <span className="mr-2">{languages[locale].flag}</span>
            <span>{languages[locale].name}</span>
            {currentLocale === locale && (
              <Check className="ml-auto h-4 w-4" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}