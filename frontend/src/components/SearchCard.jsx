import React, { useState } from 'react';
import { Search, Loader2, AlertCircle } from 'lucide-react';

export default function SearchCard({ onSearch, isLoading }) {
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
      setErrorMsg('Please enter an EPIC number.');
      return;
    }

    if (cleanQuery.length < 5) {
      setErrorMsg('Please enter a valid EPIC number (e.g. ABC1234567).');
      return;
    }

    setErrorMsg('');
    onSearch(cleanQuery, 'epic');
  };

  return (
    <div className="search-card">
      <h2 className="search-title">
        <Search size={22} className="text-primary" />
        Check Your EPIC Number
      </h2>
      
      <p className="search-description">
        Enter your Voter ID / EPIC number for instant verification against published notice records.
      </p>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="input-group">
          <input
            type="text"
            className="epic-input"
            placeholder="e.g. ABC1234567"
            value={queryInput}
            onChange={handleInputChange}
            maxLength={15}
            aria-label="Enter EPIC Number"
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
                Checking...
              </>
            ) : (
              'CHECK STATUS'
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


