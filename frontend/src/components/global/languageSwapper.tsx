"use client";

import { useParams, usePathname, useRouter } from "next/navigation";

import { Languages } from "@/i18n.config";

const LanguagesSwitcher = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { lang } = useParams();

  const switchLanguage = (newLang: string) => {
    const path = pathname?.replace(`/${lang}`, `/${newLang}`) ?? `/${newLang}`;
    router.push(path);
  };

  return (
    <div className="flex">
      {lang === Languages.VIETNAMESE ? (
        <button onClick={() => switchLanguage(Languages.ENGLISH)}>
          English
        </button>
      ) : (
        <button onClick={() => switchLanguage(Languages.VIETNAMESE)}>
          Tiếng Việt
        </button>
      )}
    </div>
  );
};
export default LanguagesSwitcher;