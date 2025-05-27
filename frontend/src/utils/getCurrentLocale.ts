import { Locale } from "@/i18n.config";
import { headers } from "next/headers";

export const getCurrentLanguage = async (): Promise<Locale | undefined> => {
  const locale = (await headers()).get("x-Locale");
  console.log("Current locale:", locale);
  return locale as Locale | undefined;
};