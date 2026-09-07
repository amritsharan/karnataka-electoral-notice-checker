import React from 'react';
import { AlertTriangle, CheckCircle2, ExternalLink, FileText, Info, ShieldAlert } from 'lucide-react';

export default function ResultCard({ searchResult, searchedEpic }) {
  if (!searchResult) return null;

  const {
    found,
    records,
    warning,
    total_documents_indexed = 0,
    total_documents_discovered = 0,
    last_updated,
    indexing_in_progress,
    indexing_complete
  } = searchResult;

  if (!found) {
    const notFoundMessage = indexing_in_progress
      ? `This record was not found in the documents processed so far. Indexing is still in progress (${total_documents_indexed} / ${total_documents_discovered || 'many'} PDFs processed), so the complete repository has not yet been checked.`
      : 'No match found in the complete indexed dataset.';

    return (
      <div className="result-card not-found">
        {warning && (
          <div className="name-warning-banner" style={{ marginBottom: 16 }}>
            <ShieldAlert size={18} className="warning-icon" />
            <span>{warning}</span>
          </div>
        )}

        <div className="result-header">
          <CheckCircle2 size={28} className="text-green-600" />
          <h2 className="result-title">
            {indexing_complete ? '✅ No Match Found in Complete Dataset' : 'ℹ️ No Match in Documents Processed So Far'}
          </h2>
        </div>

        <p className="result-explanation-text">
          {notFoundMessage} (Searched: <strong>{searchedEpic}</strong>)
        </p>

        <div className="source-box" style={{ background: '#f0fdf4', borderColor: '#bbf7d0', marginBottom: 20 }}>
          <div className="source-meta">
            <div>PDFs indexed so far: <strong>{total_documents_indexed}</strong></div>
            <div>Total PDFs discovered: <strong>{total_documents_discovered || total_documents_indexed}</strong></div>
            <div>Indexing state: <strong>{indexing_in_progress ? 'Indexing in progress...' : 'Complete'}</strong></div>
            <div>Last updated: <strong>{last_updated ? new Date(last_updated).toLocaleString() : 'Recently'}</strong></div>
          </div>

          <a 
            href="https://ceo.karnataka.gov.in/notices_issued.html" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-view-doc"
            style={{ background: '#059669' }}
          >
            View Official CEO Karnataka Source <ExternalLink size={14} />
          </a>
        </div>
      </div>
    );
  }

  const uniqueRecords = Array.from(
    new Map(
      (records || []).map(rec => [
        `${(rec.epic || '').toUpperCase()}-${(rec.name || '').toUpperCase()}-${(rec.constituency || '').toUpperCase()}-${rec.part_number}-${rec.serial_number}-${(rec.reason || '').toUpperCase()}-${(rec.source?.document_name || '').toLowerCase()}`,
        rec
      ])
    ).values()
  );

  const isMultiple = uniqueRecords.length > 1;

  return (
    <div className="result-card found">
      {warning && (
        <div className="name-warning-banner" style={{ marginBottom: 20 }}>
          <ShieldAlert size={18} className="warning-icon" />
          <span>{warning}</span>
        </div>
      )}

      <div className="result-header">
        <AlertTriangle size={28} style={{ color: '#d97706' }} />
        <div>
          <h2 className="result-title">
            ⚠️ Match Found in Notice Records {isMultiple && `(${uniqueRecords.length} References Found)`}
          </h2>
        </div>
      </div>

      <p className="result-explanation-text">
        Query (<strong>{searchedEpic}</strong>) appears in published notice documents from CEO Karnataka.
      </p>

      {isMultiple && (
        <div style={{ padding: '12px 16px', background: '#fef3c7', borderRadius: 8, marginBottom: 20, fontSize: 14, fontWeight: 600, color: '#92400e' }}>
          Multiple Records Found ({uniqueRecords.length} documents reference this search item). Please inspect each source reference below.
        </div>
      )}

      {uniqueRecords.map((rec, idx) => (
        <div key={idx} style={{ marginBottom: isMultiple && idx < uniqueRecords.length - 1 ? 32 : 0, paddingBottom: isMultiple && idx < uniqueRecords.length - 1 ? 24 : 0, borderBottom: isMultiple && idx < uniqueRecords.length - 1 ? '2px dashed #fde68a' : 'none' }}>

          {isMultiple && (
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#b45309', marginBottom: 12 }}>
              Reference #{idx + 1}: {rec.source.document_name} (Page {rec.source.page})
            </h3>
          )}

          {rec.confidence === 'LOW' && (
            <div style={{ background: '#fff3cd', borderLeft: '4px solid #ffc107', padding: '10px 14px', borderRadius: 6, marginBottom: 16, fontSize: 13, color: '#856404' }}>
              <Info size={16} inline style={{ verticalAlign: 'middle', marginRight: 6 }} />
              <strong>Possible Match:</strong> This record was extracted via OCR from a scanned document image and may contain minor OCR character variations. Please verify the original document.
            </div>
          )}

          <table className="details-table">
            <tbody>
              <tr>
                <th>EPIC Number</th>
                <td><strong>{rec.epic}</strong></td>
              </tr>
              {rec.name && (
                <tr>
                  <th>Elector Name</th>
                  <td><strong>{rec.name}</strong></td>
                </tr>
              )}
              {rec.relative_name && (
                <tr>
                  <th>Relative / Parent Name</th>
                  <td>{rec.relative_name}</td>
                </tr>
              )}
              {rec.age && (
                <tr>
                  <th>Age</th>
                  <td>{rec.age}</td>
                </tr>
              )}
              {rec.gender && (
                <tr>
                  <th>Gender</th>
                  <td>{rec.gender === 'M' ? 'Male' : rec.gender === 'F' ? 'Female' : rec.gender}</td>
                </tr>
              )}
              {rec.district && (
                <tr>
                  <th>District</th>
                  <td>{rec.district}</td>
                </tr>
              )}
              {rec.constituency && rec.constituency !== 'N/A' && (
                <tr>
                  <th>Assembly Constituency</th>
                  <td>{rec.constituency}</td>
                </tr>
              )}
              {rec.taluk && rec.taluk !== 'N/A' && (
                <tr>
                  <th>Subdistrict / Taluk</th>
                  <td>{rec.taluk}</td>
                </tr>
              )}
              {rec.part_number && rec.part_number !== 'N/A' && (
                <tr>
                  <th>Part Number</th>
                  <td>{rec.part_number}</td>
                </tr>
              )}
              {rec.serial_number && rec.serial_number !== 'N/A' && (
                <tr>
                  <th>Serial Number</th>
                  <td>{rec.serial_number}</td>
                </tr>
              )}
              {rec.notice_date && rec.notice_date !== 'N/A' && (
                <tr>
                  <th>Notice Date</th>
                  <td>{rec.notice_date}</td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Notice Reason Section */}
          <div className="reason-box">
            <h3>Reason / Category for Notice</h3>
            <div className="official-text">
              "{rec.reason}"
            </div>
            
            {rec.reason_explanation && !rec.reason_explanation.includes("does not provide enough information") && (
              <>
                <div className="meaning-title">What this means</div>
                <div className="meaning-text">
                  {rec.reason_explanation}
                </div>
              </>
            )}
          </div>

          {/* Source Verification Box */}
          <div className="source-box">
            <div className="source-meta">
              <div><strong>Document Name:</strong> {rec.source.document_name}</div>
              <div><strong>Page Number:</strong> Page {rec.source.page}</div>
              {rec.source.district && <div><strong>District:</strong> {rec.source.district}</div>}
              {rec.source.published_date && (
                <div><strong>Published Date:</strong> {rec.source.published_date}</div>
              )}
              <div><strong>Source Authority:</strong> Chief Electoral Officer, Karnataka</div>
            </div>

            <a 
              href={rec.source.url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn-view-doc"
            >
              <FileText size={16} /> View Original Government PDF <ExternalLink size={14} />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}

