// src/pages/Login.jsx — Company-Only Secure Portal
import { useState } from 'react';
import api from '../api';

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail.endsWith('@mjmtechnova.com')) {
      setError('Access restricted: Only authorized company emails (@mjmtechnova.com) are permitted.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/login', {
        email: trimmedEmail,
        password: password
      });

      localStorage.setItem('mjm_token', res.data.access_token);
      localStorage.setItem('mjm_user', JSON.stringify(res.data.user));
      if (onLoginSuccess) {
        onLoginSuccess(res.data.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={L.container}>
      <div style={L.card}>
        <div style={L.brandHeader}>
          <span style={L.logo}>⚙️</span>
          <h1 style={L.companyName}>MJMTECHNOVA</h1>
          <p style={L.portalTitle}>Quality Inspection Portal</p>
          <div style={L.badge}>Company Access Only</div>
        </div>

        {error && <div style={L.errorBox}>⚠️ {error}</div>}

        <form onSubmit={handleLogin} style={L.form}>
          <div style={L.field}>
            <label style={L.label}>Company Email Address</label>
            <input
              type="email"
              required
              placeholder="username@mjmtechnova.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={L.input}
            />
          </div>

          <div style={L.field}>
            <label style={L.label}>Security Password</label>
            <input
              type="password"
              required
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={L.input}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={loading ? L.btnDisabled : L.btnPrimary}
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal →'}
          </button>
        </form>

        <div style={L.footerNote}>
          <p style={L.footerText}>
            🔒 This is a private manufacturing quality assurance system.
            Unauthorized access or distribution of CAD drawings is strictly prohibited.
          </p>
        </div>
      </div>
    </div>
  );
}

const L = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'radial-gradient(circle at 50% 20%, #1e293b 0%, #0f172a 100%)',
    padding: '20px',
  },
  card: {
    background: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '16px',
    padding: '36px 32px',
    width: '100%',
    maxWidth: '440px',
    boxShadow: '0 20px 45px rgba(0,0,0,0.5)',
  },
  brandHeader: {
    textAlign: 'center',
    marginBottom: '26px',
  },
  logo: {
    fontSize: '44px',
    display: 'inline-block',
    marginBottom: '6px',
  },
  companyName: {
    fontSize: '22px',
    fontWeight: '800',
    color: '#38bdf8',
    letterSpacing: '0.8px',
    margin: 0,
  },
  portalTitle: {
    fontSize: '13px',
    color: '#94a3b8',
    marginTop: '4px',
    fontWeight: '500',
  },
  badge: {
    display: 'inline-block',
    marginTop: '10px',
    background: 'rgba(56,189,248,0.1)',
    border: '1px solid rgba(56,189,248,0.3)',
    color: '#7dd3fc',
    fontSize: '11px',
    fontWeight: '700',
    padding: '4px 12px',
    borderRadius: '20px',
    letterSpacing: '0.5px',
    textTransform: 'uppercase',
  },
  errorBox: {
    background: 'rgba(239,68,68,0.12)',
    border: '1px solid rgba(239,68,68,0.35)',
    color: '#fca5a5',
    borderRadius: '8px',
    padding: '11px 14px',
    fontSize: '13px',
    marginBottom: '20px',
    lineHeight: 1.4,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#cbd5e1',
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
  },
  input: {
    background: '#0f172a',
    border: '1px solid #475569',
    borderRadius: '8px',
    padding: '11px 14px',
    color: '#f1f5f9',
    fontSize: '14px',
    outline: 'none',
    transition: 'border 0.2s',
  },
  btnPrimary: {
    marginTop: '8px',
    background: 'linear-gradient(135deg, #2563eb, #0ea5e9)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    padding: '13px',
    fontSize: '14px',
    fontWeight: '700',
    cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(37,99,235,0.35)',
    minHeight: '46px',
  },
  btnDisabled: {
    marginTop: '8px',
    background: '#334155',
    color: '#94a3b8',
    border: 'none',
    borderRadius: '8px',
    padding: '13px',
    fontSize: '14px',
    fontWeight: '700',
    cursor: 'not-allowed',
    minHeight: '46px',
  },
  footerNote: {
    marginTop: '26px',
    borderTop: '1px solid #334155',
    paddingTop: '16px',
    textAlign: 'center',
  },
  footerText: {
    fontSize: '11px',
    color: '#64748b',
    lineHeight: 1.5,
    margin: 0,
  },
};
