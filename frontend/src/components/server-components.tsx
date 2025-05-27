import { getCurrentLanguage } from "@/utils/getCurrentLocale";
import getTranslations from "@/utils/translation";
import React from "react";

const ServerComponent = async () => {
    const lang = await getCurrentLanguage();
    console.log("ServerComponent lang:", lang);
    if (!lang) {
        throw new Error("Language not found");
    }
    const translations = await getTranslations(lang);
    return <h1>{translations.common.welcome}</h1>;
};

export default ServerComponent;