import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../i18n/translations';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    return localStorage.getItem('app_lang') || 'en';
  });

  const setLang = (newLang) => {
    setLangState(newLang);
    localStorage.setItem('app_lang', newLang);
  };

  const t = (key, params = {}) => {
    const langDict = translations[lang] || translations.en;
    let template = langDict[key] || translations.en[key] || key;

    Object.keys(params).forEach((paramKey) => {
      template = template.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), params[paramKey]);
    });

    return template;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
