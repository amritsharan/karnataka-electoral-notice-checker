import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SearchCard from './components/SearchCard';
import ResultCard from './components/ResultCard';
import Footer from './components/Footer';

export default function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [searchedQuery, setSearchedQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const API_BASE = import.meta.env.VITE_API_URL || '';

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`, {
        headers: {
          'Bypass-Tunnel-Reminder': 'true',
          'ngrok-skip-browser-warning': 'true'
        }
      });
      const contentType = res.headers.get('content-type') || '';
      if (res.ok && contentType.includes('application/json')) {
        const data = await res.json();
        setStatusData(data);
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async (queryInput, mode = 'epic') => {
    setIsLoading(true);
    setErrorMessage('');
    setSearchedQuery(queryInput);
    setSearchResult(null);

    const endpoint = mode === 'epic' ? `${API_BASE}/api/check-epic` : `${API_BASE}/api/check-name`;
    const payload = mode === 'epic' ? { epic: queryInput } : { name: queryInput };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify(payload),
      });

      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error("Unable to connect to the search server. Please check backend status.");
      }

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "We couldn't complete the search. Please try again.");
      }

      const data = await res.json();
      setSearchResult(data);
      fetchStatus();
    } catch (err) {
      console.error('Search error:', err);
      setErrorMessage(err.message || "We couldn't complete the search. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />

      {statusData?.indexing_in_progress && (statusData?.documents_processed < statusData?.documents_discovered) && (
        <div className="status-banner">
          Indexing in progress ({statusData.documents_processed || 0} / {statusData.documents_discovered || 'many'} PDFs processed). Records already processed are searchable.
        </div>
      )}

      <main className="main-content">
        <div className="container">
          <SearchCard onSearch={handleSearch} isLoading={isLoading} />

          {errorMessage && (
            <div className="result-card" style={{ borderLeft: '4px solid #dc2626', background: '#fef2f2', color: '#991b1b', marginBottom: 32 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>We couldn't complete the search.</h3>
              <p style={{ fontSize: 14 }}>{errorMessage}</p>
            </div>
          )}

          {searchResult && (
            <ResultCard searchResult={searchResult} searchedEpic={searchedQuery} />
          )}
        </div>
      </main>

      <Footer statusData={statusData} />
    </div>
  );
}


