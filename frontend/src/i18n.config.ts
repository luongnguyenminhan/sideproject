export enum Languages {
  ENGLISH = "en",
  VIETNAMESE = "vi",
}

// Define a type for LanguageType which can be either English or VIETNAMESE
export type LanguageType = Languages.VIETNAMESE | Languages.ENGLISH;

// Define a type for i18n which includes a defaultLocale and an array of locales
type i18nType = {
  defaultLocale: LanguageType; // The default language
  locales: LanguageType[]; // An array of the available languages
};

// Initialize the i18n object with the default language and the array of languages
export const i18n: i18nType = {
  defaultLocale: Languages.VIETNAMESE, // The default language is VIETNAMESE
  locales: [Languages.VIETNAMESE, Languages.ENGLISH], // The available languages are VIETNAMESE and English
};

// Define a type Locale as one of the available languages in the locales array
export type Locale = (typeof i18n)["locales"][number];