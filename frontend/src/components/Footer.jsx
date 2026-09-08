import React from 'react';
import { useLanguage } from '../context/LanguageContext';

export default function Footer({ statusData }) {
  const { t } = useLanguage();

  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        {statusData?.indexing_in_progress && (statusData?.documents_processed < statusData?.documents_discovered) && (
          <div style={{ background: '#78350f', color: '#fef3c7', padding: '8px 16px', borderRadius: 6, fontSize: 13 }}>
            {t('dbUpdateInProgress')}
          </div>
        )}

        <div className="disclaimer-text">
          <strong>{t('disclaimerLabel')}</strong> {t('disclaimerText')}
        </div>
      </div>
    </footer>
  );
}
