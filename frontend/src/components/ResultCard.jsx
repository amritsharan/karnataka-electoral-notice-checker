import React from 'react';
import { AlertTriangle, CheckCircle2, ExternalLink, FileText, Info, ShieldAlert } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function ResultCard({ searchResult, searchedEpic }) {
  const { t } = useLanguage();

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
    return (
      <div className="result-card not-found">
        <div className="result-header">
          <CheckCircle2 size={28} style={{ color: '#16a34a' }} />
          <h2 className="result-title" style={{ color: '#15803d' }}>
            ✅ {t('noNoticeTitle')}
          </h2>
        </div>

        <p className="result-explanation-text">
          {t('noNoticeDesc')} <strong>{searchedEpic}</strong>.
        </p>

        <div className="source-box" style={{ background: '#f0fdf4', borderColor: '#bbf7d0', marginTop: 20 }}>
          <a 
            href="https://ceo.karnataka.gov.in/notices_issued.html" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-view-doc"
            style={{ background: '#059669' }}
          >
            {t('btnViewOfficialSource')} <ExternalLink size={14} />
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
            ⚠️ {t('matchFoundTitle')} {isMultiple && `(${uniqueRecords.length} ${t('matchFoundReferences')})`}
          </h2>
        </div>
      </div>

      <p className="result-explanation-text">
        {t('matchDesc', { query: searchedEpic })}
      </p>

      {isMultiple && (
        <div style={{ padding: '12px 16px', background: '#fef3c7', borderRadius: 8, marginBottom: 20, fontSize: 14, fontWeight: 600, color: '#92400e' }}>
          {t('multipleRecordsBanner', { count: uniqueRecords.length })}
        </div>
      )}

      {uniqueRecords.map((rec, idx) => (
        <div key={idx} style={{ marginBottom: isMultiple && idx < uniqueRecords.length - 1 ? 32 : 0, paddingBottom: isMultiple && idx < uniqueRecords.length - 1 ? 24 : 0, borderBottom: isMultiple && idx < uniqueRecords.length - 1 ? '2px dashed #fde68a' : 'none' }}>

          {isMultiple && (
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#b45309', marginBottom: 12 }}>
              {t('referenceHeader', { index: idx + 1, docName: rec.source.document_name, page: rec.source.page })}
            </h3>
          )}

          {rec.confidence === 'LOW' && (
            <div style={{ background: '#fff3cd', borderLeft: '4px solid #ffc107', padding: '10px 14px', borderRadius: 6, marginBottom: 16, fontSize: 13, color: '#856404' }}>
              <Info size={16} inline style={{ verticalAlign: 'middle', marginRight: 6 }} />
              {t('possibleOcrMatch')}
            </div>
          )}

          <table className="details-table">
            <tbody>
              <tr>
                <th>{t('epicNumber')}</th>
                <td><strong>{rec.epic}</strong></td>
              </tr>
              {rec.name && (
                <tr>
                  <th>{t('electorName')}</th>
                  <td><strong>{rec.name}</strong></td>
                </tr>
              )}
              {rec.relative_name && (
                <tr>
                  <th>{t('relativeName')}</th>
                  <td>{rec.relative_name}</td>
                </tr>
              )}
              {rec.age && (
                <tr>
                  <th>{t('age')}</th>
                  <td>{rec.age}</td>
                </tr>
              )}
              {rec.gender && (
                <tr>
                  <th>{t('gender')}</th>
                  <td>{rec.gender === 'M' ? t('male') : rec.gender === 'F' ? t('female') : rec.gender}</td>
                </tr>
              )}
              {rec.district && (
                <tr>
                  <th>{t('district')}</th>
                  <td>{rec.district}</td>
                </tr>
              )}
              {rec.constituency && rec.constituency !== 'N/A' && (
                <tr>
                  <th>{t('assemblyConstituency')}</th>
                  <td>{rec.constituency}</td>
                </tr>
              )}
              {rec.taluk && rec.taluk !== 'N/A' && (
                <tr>
                  <th>{t('subdistrictTaluk')}</th>
                  <td>{rec.taluk}</td>
                </tr>
              )}
              {rec.part_number && rec.part_number !== 'N/A' && (
                <tr>
                  <th>{t('partNumber')}</th>
                  <td>{rec.part_number}</td>
                </tr>
              )}
              {rec.serial_number && rec.serial_number !== 'N/A' && (
                <tr>
                  <th>{t('serialNumber')}</th>
                  <td>{rec.serial_number}</td>
                </tr>
              )}
              {rec.notice_date && rec.notice_date !== 'N/A' && (
                <tr>
                  <th>{t('noticeDate')}</th>
                  <td>{rec.notice_date}</td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Notice Reason Section */}
          <div className="reason-box">
            <h3>{t('reasonHeading')}</h3>
            <div className="official-text">
              "{rec.reason}"
            </div>
            
            {rec.reason_explanation && !rec.reason_explanation.includes("does not provide enough information") && (
              <>
                <div className="meaning-title">{t('whatThisMeans')}</div>
                <div className="meaning-text">
                  {rec.reason_explanation}
                </div>
              </>
            )}
          </div>

          {/* Source Verification Box */}
          <div className="source-box">
            <div className="source-meta">
              <div><strong>{t('docNameLabel')}</strong> {rec.source.document_name}</div>
              <div><strong>{t('pageNumberLabel')}</strong> {t('pageText')} {rec.source.page}</div>
              {rec.source.district && <div><strong>{t('districtLabel')}</strong> {rec.source.district}</div>}
              {rec.source.published_date && (
                <div><strong>{t('publishedDateLabel')}</strong> {rec.source.published_date}</div>
              )}
              <div><strong>{t('sourceAuthorityLabel')}</strong> {t('sourceAuthorityValue')}</div>
            </div>

            <a 
              href={rec.source.url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn-view-doc"
            >
              <FileText size={16} /> {t('btnViewPdf')} <ExternalLink size={14} />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
