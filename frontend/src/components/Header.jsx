import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function Header() {
  const { lang, setLang, t } = useLanguage();

  return (
    <header className="site-header">
      <div className="container header-inner">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={26} />
          </div>
          <div>
            <h1 className="brand-title">{t('headerTitle')}</h1>
            <p className="brand-subtitle">{t('headerSubtitle')}</p>
          </div>
        </div>

        <div className="lang-toggle-container">
          <div className="lang-toggle" role="radiogroup" aria-label="Language selection">
            <button
              type="button"
              className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => setLang('en')}
              aria-checked={lang === 'en'}
              role="radio"
            >
              English
            </button>
            <button
              type="button"
              className={`lang-btn ${lang === 'kn' ? 'active' : ''}`}
              onClick={() => setLang('kn')}
              aria-checked={lang === 'kn'}
              role="radio"
            >
              ಕನ್ನಡ
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
