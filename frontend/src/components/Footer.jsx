import React from 'react';

export default function Footer({ statusData }) {
  const lastUpdatedText = statusData?.last_updated
    ? new Date(statusData.last_updated).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short'
      })
    : 'Recently updated';

  const docCount = statusData?.documents_processed || statusData?.total_documents_indexed || 0;

  return (
    <footer className="site-footer">
      <div className="container footer-inner">


        {statusData?.indexing_in_progress && (statusData?.documents_processed < statusData?.documents_discovered) && (
          <div style={{ background: '#78350f', color: '#fef3c7', padding: '8px 16px', borderRadius: 6, fontSize: 13 }}>
            ⚠️ <strong>Database update in progress:</strong> Some recently published documents may not yet be indexed.
          </div>
        )}

        <div className="disclaimer-text">
          <strong>Disclaimer:</strong> This is an independent information/search tool and is not affiliated with or operated by the Election Commission of India or the Chief Electoral Officer, Karnataka. It searches information contained in publicly available government documents. For authoritative confirmation, please refer to the original CEO Karnataka publication.
        </div>
      </div>
    </footer>
  );
}
