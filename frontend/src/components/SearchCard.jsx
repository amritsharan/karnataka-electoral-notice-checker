import React, { useState } from 'react';
import { Search, Loader2, AlertCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function SearchCard({ onSearch, isLoading }) {
  const { t } = useLanguage();
  const [queryInput, setQueryInput] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleInputChange = (e) => {
    setQueryInput(e.target.value.toUpperCase());
    if (errorMsg) setErrorMsg('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanQuery = queryInput.trim();

    if (!cleanQuery) {
      setErrorMsg(t('errEmptyEpic'));
      return;
    }

    if (cleanQuery.length < 5) {
      setErrorMsg(t('errInvalidEpic'));
      return;
    }

    setErrorMsg('');
    onSearch(cleanQuery, 'epic');
  };

  return (
    <div className="search-card">
      <h2 className="search-title">
        <Search size={22} className="text-primary" />
        {t('searchTitle')}
      </h2>
      
      <p className="search-description">
        {t('searchDescription')}
      </p>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="input-group">
          <input
            type="text"
            className="epic-input"
            placeholder={t('epicPlaceholder')}
            value={queryInput}
            onChange={handleInputChange}
            maxLength={15}
            aria-label={t('ariaEpicInput')}
            disabled={isLoading}
            autoFocus
          />
          <button 
            type="submit" 
            className="btn-search"
            disabled={isLoading || !queryInput.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                {t('btnChecking')}
              </>
            ) : (
              t('btnCheckStatus')
            )}
          </button>
        </div>

        {errorMsg && (
          <div className="error-hint" role="alert">
            <AlertCircle size={16} inline style={{ verticalAlign: 'middle', marginRight: 4 }} />
            {errorMsg}
          </div>
        )}
      </form>
    </div>
  );
}
