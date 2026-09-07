import React, { useState, useEffect } from 'react';
import { RefreshCw, Play, PauseCircle, RotateCcw, Database, Server, FileCode, Sliders, ListTree, Terminal } from 'lucide-react';

const KARNATAKA_DISTRICTS = [
  "ALL",
  "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
  "Bidar", "Chamarajanagar", "Chikkaballapura", "Chikkamagaluru", "Chitradurga",
  "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan",
  "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal",
  "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
  "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
];

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('Tumakuru'); // Default target single district for Milestone 1
  const [batchSize, setBatchSize] = useState(10); // Default BATCH_SIZE=10

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/admin/metrics', {
        headers: {
          'Authorization': 'Basic ' + btoa('admin:admin123')
        }
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Error fetching admin metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (endpoint, label, payload = null) => {
    setActionStatus(`Executing ${label}...`);
    try {
      const options = {
        method: 'POST',
        headers: {
          'Authorization': 'Basic ' + btoa('admin:admin123'),
          'Content-Type': 'application/json'
        }
      };
      if (payload) {
        options.body = JSON.stringify(payload);
      }

      const res = await fetch(`/api/admin/${endpoint}`, options);
      const data = await res.json();
      if (res.ok && data.success) {
        setActionStatus(`Success: ${data.message}`);
        fetchMetrics();
      } else {
        setActionStatus(`Error: ${data.message || 'Operation failed'}`);
      }
    } catch (err) {
      setActionStatus(`Failed to execute ${label}`);
    }
  };

  if (loading && !metrics) {
    return <div className="admin-card">Loading admin dashboard statistics...</div>;
  }

  return (
    <div className="admin-card">
      <div className="admin-header">
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server className="text-primary" size={24} /> CEO Karnataka Large-Scale Ingestion Dashboard
          </h2>
          <p style={{ fontSize: 14, color: 'var(--text-muted)', marginTop: 4 }}>
            Control discovery jobs, PDF processing queues, batch sizes, and progress per district.
          </p>
        </div>

        <button className="btn-admin-action" onClick={fetchMetrics}>
          <RefreshCw size={16} /> Refresh Metrics
        </button>
      </div>

      {/* Source & Control Settings Bar */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '16px 20px', borderRadius: 8, marginBottom: 24 }}>
        <div style={{ fontSize: 14, marginBottom: 12 }}>
          <strong>Configured Source URL:</strong>{' '}
          <a href={metrics?.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)', fontWeight: 600 }}>
            {metrics?.source_url}
          </a>
        </div>

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders size={16} className="text-primary" />
            <label style={{ fontSize: 14, fontWeight: 600 }}>Target District:</label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 14 }}
            >
              {KARNATAKA_DISTRICTS.map((dist) => (
                <option key={dist} value={dist}>{dist === 'ALL' ? 'ALL 34 DISTRICTS' : dist}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 14, fontWeight: 600 }}>Queue Batch Size:</label>
            <select
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 14 }}
            >
              <option value={10}>10 (Milestone 1 Test Batch)</option>
              <option value={100}>100 (Medium Batch)</option>
              <option value={1000}>1,000 (Large Batch)</option>
              <option value={5000}>5,000 (Production Scale)</option>
            </select>
          </div>
        </div>
      </div>

      {actionStatus && (
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', padding: '12px 16px', borderRadius: 8, marginBottom: 24, fontSize: 14, fontWeight: 500 }}>
          {actionStatus}
        </div>
      )}

      {/* Primary Control Buttons */}
      <div className="admin-actions" style={{ marginBottom: 28 }}>
        <button
          className="btn-admin-action"
          style={{ background: '#2563eb', color: '#fff' }}
          onClick={() => handleAction('start-discovery', `Start Discovery for ${selectedDistrict}`, { district: selectedDistrict, batch_size: batchSize })}
        >
          <Play size={16} /> Start Discovery ({selectedDistrict})
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('pause-discovery', 'Pause Discovery')}>
          <PauseCircle size={16} /> Pause Discovery
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('resume-discovery', 'Resume Discovery')}>
          <Play size={16} /> Resume Discovery
        </button>

        <button
          className="btn-admin-action"
          style={{ background: '#059669', color: '#fff' }}
          onClick={() => handleAction('start-processing', `Start PDF Processing (Batch=${batchSize})`, { batch_size: batchSize })}
        >
          <Server size={16} /> Start PDF Processing
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('pause-processing', 'Pause Processing')}>
          <PauseCircle size={16} /> Pause Processing
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('resume-processing', 'Resume Processing')}>
          <Server size={16} /> Resume Processing
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('retry-failed', 'Retry Failed')}>
          <RotateCcw size={16} /> Retry Failed Items
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('reindex', 'Re-index Database')}>
          <Database size={16} /> Re-index Database
        </button>

        <button className="btn-admin-action" onClick={() => handleAction('seed-test-data', 'Seed Test Data')}>
          <FileCode size={16} /> Seed Mock Test Data
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">Total Source Pages Discovered</div>
          <div className="stat-value">{metrics?.crawl_queue_total || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Total PDFs Discovered</div>
          <div className="stat-value">{metrics?.documents_discovered || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">PDFs Processed / Indexed</div>
          <div className="stat-value" style={{ color: '#059669' }}>{metrics?.documents_processed || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">PDFs Pending Processing</div>
          <div className="stat-value" style={{ color: '#d97706' }}>{metrics?.documents_pending || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">OCR Processed Documents</div>
          <div className="stat-value" style={{ color: '#4f46e5' }}>{metrics?.ocr_documents_count || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Failed Documents</div>
          <div className="stat-value" style={{ color: '#dc2626' }}>{metrics?.documents_failed || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Total Records Indexed</div>
          <div className="stat-value" style={{ color: 'var(--primary)' }}>{metrics?.total_records_indexed || 0}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Crawl Queue Pending</div>
          <div className="stat-value" style={{ color: '#d97706' }}>{metrics?.crawl_queue_pending || 0}</div>
        </div>
      </div>

      {/* Progress Tables */}
      {metrics?.district_progress?.length > 0 && (
        <div style={{ marginTop: 28, marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <ListTree size={20} className="text-primary" /> District-Level Indexing Progress
          </h3>
          <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead style={{ background: '#f8fafc' }}>
                <tr>
                  <th style={{ textAlign: 'left', padding: '10px 12px' }}>District</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Discovered PDFs</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Processed</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Pending</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Failed</th>
                </tr>
              </thead>
              <tbody>
                {metrics.district_progress.map((row) => (
                  <tr key={row.district} style={{ borderTop: '1px solid #e2e8f0' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600 }}>{row.district}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{row.pdfs}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', color: '#059669', fontWeight: 600 }}>{row.processed}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', color: '#d97706' }}>{row.pending}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', color: '#dc2626' }}>{row.failed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {metrics?.subdistrict_progress?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <ListTree size={20} className="text-primary" /> Subdistrict / Taluk Progress Breakdown
          </h3>
          <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8, maxHeight: 320 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead style={{ background: '#f8fafc', position: 'sticky', top: 0 }}>
                <tr>
                  <th style={{ textAlign: 'left', padding: '10px 12px' }}>District</th>
                  <th style={{ textAlign: 'left', padding: '10px 12px' }}>Subdistrict / Taluk</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>PDFs</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Processed</th>
                  <th style={{ textAlign: 'right', padding: '10px 12px' }}>Pending</th>
                </tr>
              </thead>
              <tbody>
                {metrics.subdistrict_progress.map((row) => (
                  <tr key={`${row.district}-${row.subdistrict}`} style={{ borderTop: '1px solid #e2e8f0' }}>
                    <td style={{ padding: '10px 12px' }}>{row.district}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.subdistrict}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>{row.pdfs}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', color: '#059669', fontWeight: 600 }}>{row.processed}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', color: '#d97706' }}>{row.pending}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Crawler Logs Stream */}
      {metrics?.recent_events?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Terminal size={20} className="text-primary" /> Live Crawler Event Logs
          </h3>
          <div style={{ border: '1px solid #1e293b', borderRadius: 8, padding: 14, background: '#0f172a', color: '#f8fafc', fontFamily: 'monospace', fontSize: 13, maxHeight: 240, overflowY: 'auto' }}>
            {metrics.recent_events.map((event, idx) => (
              <div key={`${event.timestamp}-${idx}`} style={{ marginBottom: 6, borderBottom: '1px solid #1e293b', paddingBottom: 4 }}>
                <span style={{ color: '#94a3b8' }}>[{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : 'NOW'}]</span>{' '}
                <span style={{ color: event.status === 'FAILED' ? '#f87171' : event.status === 'SUCCESS' ? '#4ade80' : '#60a5fa', fontWeight: 'bold' }}>
                  {event.status}
                </span>{' '}
                <span style={{ color: '#fbbf24' }}>[{event.stage}]</span> {event.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

