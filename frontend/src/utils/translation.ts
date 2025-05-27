import "server-only";

import { Locale } from "@/i18n.config";

// Define the dictionaries object with asynchronous imports for Vietnamese and English dictionaries
const dictionaries = {
  vi: () => import("@/locales/vi.json").then((module) => module.default),
  en: () => import("@/locales/en.json").then((module) => module.default),
};

// Define an asynchronous function to get the translation based on the locale
const getTranslations = async (locale: Locale) => {
  // Return the Vietnamese dictionary if the locale is Vietnamese, otherwise return the English dictionary
  switch (locale) {
    case 'vi':
        console.log("Using Vietnamese translations");
        return dictionaries.vi();
    case 'en':
        console.log("Using English translations");
        return dictionaries.en();
    default:
        console.warn(`Locale ${locale} not recognized, defaulting to Vietnamese`);
        return dictionaries.vi(); // Default to Vietnamese if the locale is not recognized
  }
};

export default getTranslations;