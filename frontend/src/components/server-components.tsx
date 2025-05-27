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
    
    return (
        <div className="space-y-6">
            <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    {translations.common.welcome}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                    This component is rendered on the server with current locale: <span className="font-semibold text-blue-600 dark:text-blue-400">{lang}</span>
                </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
                    <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Server-Side Rendering</h4>
                    <p className="text-blue-700 dark:text-blue-300 text-sm">
                        This content is generated on the server and supports full internationalization.
                    </p>
                </div>
                
                <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800">
                    <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">Dynamic Translations</h4>
                    <p className="text-green-700 dark:text-green-300 text-sm">
                        Language switching works seamlessly with server components.
                    </p>
                </div>
            </div>
            
            <div className="text-center pt-4">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    Server Component Active
                </div>
            </div>
        </div>
    );
};

export default ServerComponent;