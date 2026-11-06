// src/pages/Dashboard.jsx
import { useState, useRef } from 'react';
import api from '../api';

const QC_COLOR = { ACCEPT: '#22c55e', REJECT: '#ef4444', PENDING: '#f59e0b' };

const COLUMNS = [
  { key: 'sr',           label: 'Sr.',          width: 50 },
  { key: 'parameter',    label: 'Parameter',     width: 170 },
  { key: 'x_nominal',   label: 'X (Nominal)',   width: 100 },
  { key: 'tol_x',       label: 'Tol IN X',      width: 100 },
  { key: 'y_nominal',   label: 'Y (Nominal)',   width: 100 },
  { key: 'tol_y',       label: 'Tol IN Y',      width: 100 },
  { key: 'size',        label: 'Size',          width: 80  },
  { key: 'hole_callout',label: 'Hole Callout',  width: 170 },
  { key: 'instrument',  label: 'Instrument',    width: 150 },
  { key: 'actual',      label: 'Actual',        width: 90  },
  { key: 'deviation',   label: 'Deviation',     width: 90  },
  { key: 'qc_result',   label: 'QC Result',     width: 100 },
  { key: 'remark',      label: 'Remark',        width: 130 },
];

export default function Dashboard() {
  const [file, setFile]             = useState(null);
  const [dragging, setDragging]     = useState(false);
  const [loading, setLoading]       = useState(false);
  const [data, setData]             = useState(null);
  const [error, setError]           = useState('');
  const [search, setSearch]         = useState('');
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab]   = useState('table');
  const fileRef = useRef();

  const pickFile = (f) => {
    if (f && f.type === 'application/pdf') { setFile(f); setData(null); setError(''); }
    else setError('Please select a valid PDF file.');
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      pickFile(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true); setError(''); setData(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const { data: res } = await api.post('/api/extract', fd);
      setData(res);
      setActiveTab('table');
    } catch (err) {
      setError(err.response?.data?.detail || 'Extraction failed. Check the PDF and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!file) return;
    setDownloading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await api.post('/api/report', fd, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a   = document.createElement('a');
      a.href = url;
      a.download = `${file.name.replace('.pdf', '')}_Inspection_Report.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Report generation failed.');
    } finally {
      setDownloading(false);
    }
  };

  const filteredRows = (data?.rows || []).filter((r) =>
    !search ||
    r.parameter?.toLowerCase().includes(search.toLowerCase()) ||
    r.hole_callout?.toLowerCase().includes(search.toLowerCase())
  );

  const acceptCount = (data?.rows || []).filter(r => r.qc_result === 'ACCEPT').length;
  const rejectCount = (data?.rows || []).filter(r => r.qc_result === 'REJECT').length;

  return (
    <div style={S.page}>
      {/* ── Top Nav ── */}
      <nav style={S.nav} className="nav-container">
        <div style={S.navLeft}>
          <span style={S.navLogo}>⚙️</span>
          <div>
            <div style={S.navTitle}>MJMTECHNOVA ENGINEERING PVT. LTD.</div>
            <div style={S.navSub}>Quality Inspection Automation Dashboard</div>
          </div>
        </div>
        <div style={S.navRight} className="nav-tag-badge">
          <span style={S.navTag}>IS 2102 / ISO 2768-m</span>
        </div>
      </nav>

      <div style={S.body} className="body-container">
        {/* ── Upload Panel ── */}
        <div style={S.uploadCard} className="upload-box">
          <h2 style={S.sectionTitle}>📄 Upload 2D CAD Drawing (PDF)</h2>

          <div
            style={{ ...S.dropzone, ...(dragging ? S.dropzoneActive : {}) }}
            className="dropzone-inner"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current.click()}
          >
            <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }}
              onChange={(e) => pickFile(e.target.files[0])} />
            {file ? (
              <div>
                <div style={{ fontSize: '36px' }}>📋</div>
                <p style={S.fileName}>{file.name}</p>
                <p style={S.fileSize}>{(file.size / 1024).toFixed(1)} KB — tap to change</p>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '42px', opacity: 0.4 }}>📁</div>
                <p style={S.dropText}>Tap here to browse or drag PDF</p>
                <p style={S.dropHint}>Supports 2D CAD drawings (PDF)</p>
              </div>
            )}
          </div>

          <div style={S.btnRow} className="btn-action-row">
            <button onClick={handleAnalyze} disabled={!file || loading}
              style={!file || loading ? S.btnDisabled : S.btnPrimary}>
              {loading ? '⏳ Analyzing...' : '🔍 Analyze Drawing'}
            </button>

            {data && (
              <button onClick={handleDownload} disabled={downloading}
                style={downloading ? S.btnDisabled : S.btnGreen}>
                {downloading ? '⏳ Generating...' : '⬇️ Download Excel'}
              </button>
            )}
          </div>

          {error && <div style={S.errorBox}>⚠️ {error}</div>}
        </div>

        {/* ── Metadata Cards ── */}
        {data && (
          <>
            <div style={S.metaGrid} className="meta-grid">
              {[
                { label: 'Part No.',      value: data.metadata?.part_number || '—' },
                { label: 'Material',      value: data.metadata?.material    || '—' },
                { label: 'Revision',      value: data.metadata?.revision    || '—' },
                { label: 'Net Weight',    value: data.metadata?.net_weight  || '—' },
                { label: 'Total Params',  value: data.total,                   color: '#38bdf8' },
                { label: 'ACCEPT',        value: acceptCount,                  color: '#22c55e' },
                { label: 'REJECT',        value: rejectCount,                  color: '#ef4444' },
              ].map((m) => (
                <div key={m.label} style={S.metaCard}>
                  <div style={{ ...S.metaValue, color: m.color || '#e2e8f0' }}>{m.value}</div>
                  <div style={S.metaLabel}>{m.label}</div>
                </div>
              ))}
            </div>

            {/* ── Tabs ── */}
            <div style={S.tabBar}>
              {[
                { id: 'table', label: '📊 Inspection Table' },
                { id: 'ai',    label: '🧠 AI Classifier'    },
              ].map((t) => (
                <button key={t.id} onClick={() => setActiveTab(t.id)}
                  style={{ ...S.tab, ...(activeTab === t.id ? S.tabActive : {}) }}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* ── Inspection Table ── */}
            {activeTab === 'table' && (
              <div style={S.tableCard}>
                <div style={S.toolbar} className="toolbar-wrap">
                  <input
                    placeholder="🔍 Search parameter or callout..."
                    value={search} onChange={(e) => setSearch(e.target.value)}
                    style={S.searchInput}
                  />
                  <span style={S.rowCount}>{filteredRows.length} of {data.total} rows</span>
                </div>
                <div style={S.tableWrap}>
                  <table style={S.table}>
                    <thead>
                      <tr>
                        {COLUMNS.map((c) => (
                          <th key={c.key} style={{ ...S.th, minWidth: c.width }}>{c.label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRows.map((row, i) => (
                        <tr key={row.sr} style={i % 2 === 0 ? S.trEven : S.trOdd}>
                          {COLUMNS.map((c) => (
                            <td key={c.key} style={S.td}>
                              {c.key === 'qc_result' ? (
                                <span style={{
                                  ...S.badge,
                                  background: QC_COLOR[row.qc_result] + '22',
                                  color: QC_COLOR[row.qc_result],
                                  border: `1px solid ${QC_COLOR[row.qc_result]}55`,
                                }}>{row.qc_result}</span>
                              ) : (
                                typeof row[c.key] === 'number'
                                  ? row[c.key].toFixed(3)
                                  : (row[c.key] ?? '—')
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ── AI Tab ── */}
            {activeTab === 'ai' && data.ai && (
              <div style={S.aiCard}>
                <h3 style={S.aiTitle}>🧠 AI Drawing Classification</h3>
                <div style={S.aiResult}>
                  <div>
                    <div style={S.aiLabel}>Predicted Category</div>
                    <div style={S.aiCategory}>{data.ai.predicted_category}</div>
                  </div>
                  <div>
                    <div style={S.aiLabel}>Confidence</div>
                    <div style={S.aiConf}>{(data.ai.confidence * 100).toFixed(1)}%</div>
                    <div style={S.confBar}>
                      <div style={{ ...S.confFill, width: `${data.ai.confidence * 100}%` }} />
                    </div>
                  </div>
                </div>

                <div>
                  <div style={S.aiLabel}>Class Probabilities</div>
                  {Object.entries(data.ai.top_probabilities || {}).map(([cls, prob]) => (
                    <div key={cls} style={S.probRow}>
                      <span style={S.probLabel}>{cls}</span>
                      <div style={S.probBarBg}>
                        <div style={{ ...S.probBarFill, width: `${prob * 100}%` }} />
                      </div>
                      <span style={S.probPct}>{(prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {!data && !loading && (
          <div style={S.placeholder}>
            <div style={{ fontSize: '64px', opacity: 0.15 }}>📐</div>
            <p style={{ color: '#64748b', fontSize: '16px', marginTop: '14px', lineHeight: 1.5 }}>
              Select or tap to upload a PDF drawing, then click <strong style={{ color: '#38bdf8' }}>Analyze Drawing</strong>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Inline base styles with flex/grid defaults ── */
const S = {
  page: { minHeight: '100vh', background: '#0f172a', display: 'flex', flexDirection: 'column' },
  nav: {
    background: '#1e293b', borderBottom: '1px solid #334155',
    padding: '14px 24px', display: 'flex', alignItems: 'center',
    justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 100,
    boxShadow: '0 2px 14px rgba(0,0,0,0.3)',
  },
  navLeft:  { display: 'flex', alignItems: 'center', gap: '12px' },
  navLogo:  { fontSize: '28px' },
  navTitle: { fontSize: '15px', fontWeight: '800', color: '#38bdf8', letterSpacing: '0.3px', lineHeight: 1.2 },
  navSub:   { fontSize: '11px', color: '#64748b', marginTop: '2px' },
  navRight: { display: 'flex', alignItems: 'center' },
  navTag: {
    background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.25)',
    color: '#7dd3fc', borderRadius: '20px', padding: '4px 12px', fontSize: '11px', fontWeight: '600',
  },
  body: { padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '1400px', width: '100%', margin: '0 auto' },

  uploadCard: {
    background: '#1e293b', border: '1px solid #334155', borderRadius: '14px', padding: '22px',
  },
  sectionTitle: { fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '16px' },
  dropzone: {
    border: '2px dashed #334155', borderRadius: '10px', padding: '36px 18px',
    textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s', background: '#0f172a',
  },
  dropzoneActive: { borderColor: '#2563eb', background: 'rgba(37,99,235,0.08)' },
  fileName: { fontSize: '15px', fontWeight: '600', color: '#f1f5f9', margin: '10px 0 4px', wordBreak: 'break-all' },
  fileSize: { fontSize: '12px', color: '#64748b' },
  dropText: { fontSize: '15px', color: '#94a3b8', margin: '10px 0 4px' },
  dropHint: { fontSize: '12px', color: '#475569' },
  btnRow:   { display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' },
  btnPrimary: {
    background: 'linear-gradient(135deg,#2563eb,#0ea5e9)', color: '#fff', border: 'none',
    borderRadius: '8px', padding: '12px 24px', fontSize: '14px', fontWeight: '700',
    cursor: 'pointer', boxShadow: '0 4px 14px rgba(37,99,235,0.3)', minHeight: '44px',
  },
  btnGreen: {
    background: 'linear-gradient(135deg,#16a34a,#22c55e)', color: '#fff', border: 'none',
    borderRadius: '8px', padding: '12px 24px', fontSize: '14px', fontWeight: '700',
    cursor: 'pointer', boxShadow: '0 4px 14px rgba(34,197,94,0.3)', minHeight: '44px',
  },
  btnDisabled: {
    background: '#1e293b', border: '1px solid #334155', color: '#475569',
    borderRadius: '8px', padding: '12px 24px', fontSize: '14px', cursor: 'not-allowed', minHeight: '44px',
  },
  errorBox: {
    marginTop: '14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
    color: '#fca5a5', borderRadius: '8px', padding: '10px 14px', fontSize: '13px',
  },

  metaGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px',
  },
  metaCard: {
    background: '#1e293b', border: '1px solid #334155', borderRadius: '10px',
    padding: '14px 16px', textAlign: 'center',
  },
  metaValue: { fontSize: '18px', fontWeight: '800' },
  metaLabel: { fontSize: '10px', color: '#64748b', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' },

  tabBar: { display: 'flex', gap: '8px', borderBottom: '1px solid #334155', overflowX: 'auto' },
  tab: {
    background: 'transparent', border: 'none', borderBottom: '2px solid transparent',
    color: '#64748b', padding: '10px 16px', fontSize: '13px', fontWeight: '600',
    cursor: 'pointer', whiteSpace: 'nowrap',
  },
  tabActive: { color: '#38bdf8', borderBottom: '2px solid #38bdf8', background: 'rgba(56,189,248,0.07)' },

  tableCard: {
    background: '#1e293b', border: '1px solid #334155',
    borderRadius: '0 10px 10px 10px', overflow: 'hidden',
  },
  toolbar: {
    display: 'flex', alignItems: 'center', gap: '12px',
    padding: '12px 16px', borderBottom: '1px solid #334155',
  },
  searchInput: {
    flex: 1, background: '#0f172a', border: '1px solid #475569', borderRadius: '8px',
    padding: '9px 14px', color: '#f1f5f9', fontSize: '13px', outline: 'none',
  },
  rowCount:  { fontSize: '12px', color: '#64748b', whiteSpace: 'nowrap' },
  tableWrap: { overflowX: 'auto', WebkitOverflowScrolling: 'touch' },
  table:     { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th: {
    background: '#0f172a', color: '#94a3b8', fontWeight: '700', fontSize: '11px',
    textTransform: 'uppercase', letterSpacing: '0.5px',
    padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #334155', whiteSpace: 'nowrap',
  },
  td:     { padding: '9px 12px', color: '#e2e8f0', borderBottom: '1px solid #1e293b', whiteSpace: 'nowrap' },
  trEven: { background: '#1e293b' },
  trOdd:  { background: '#192235' },
  badge:  { borderRadius: '4px', padding: '3px 8px', fontSize: '11px', fontWeight: '700' },

  aiCard: {
    background: '#1e293b', border: '1px solid #334155',
    borderRadius: '0 10px 10px 10px', padding: '20px',
  },
  aiTitle:    { fontSize: '16px', fontWeight: '700', color: '#f1f5f9', marginBottom: '18px' },
  aiResult:   { display: 'flex', gap: '30px', flexWrap: 'wrap', marginBottom: '24px' },
  aiLabel:    { fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' },
  aiCategory: { fontSize: '26px', fontWeight: '800', color: '#38bdf8' },
  aiConf:     { fontSize: '24px', fontWeight: '800', color: '#22c55e', marginBottom: '6px' },
  confBar:    { width: '180px', maxWidth: '100%', height: '7px', background: '#0f172a', borderRadius: '4px', overflow: 'hidden' },
  confFill:   { height: '100%', background: 'linear-gradient(90deg,#22c55e,#86efac)', borderRadius: '4px' },
  probRow:    { display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px' },
  probLabel:  { width: '120px', fontSize: '12px', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  probBarBg:  { flex: 1, height: '7px', background: '#0f172a', borderRadius: '4px', overflow: 'hidden' },
  probBarFill:{ height: '100%', background: 'linear-gradient(90deg,#2563eb,#38bdf8)', borderRadius: '4px' },
  probPct:    { width: '42px', fontSize: '12px', color: '#64748b', textAlign: 'right' },

  placeholder: { textAlign: 'center', padding: '60px 20px' },
};
