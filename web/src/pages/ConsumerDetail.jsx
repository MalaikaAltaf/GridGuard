import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getExplanation, getConsumptionHistory, getInspectors, createCase,
} from '../api';
import RiskBadge from '../components/RiskBadge';
import { ChevronLeft, UserPlus, X, Loader, AlertCircle } from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';

// ── Assign Case Modal ─────────────────────────────────────────
function AssignModal({ consumer, riskScore, onClose, onSuccess }) {
  const [inspectors, setInspectors] = useState([]);
  const [selected, setSelected] = useState(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getInspectors().then(setInspectors).catch(() => {});
  }, []);

  const handleAssign = async () => {
    if (!selected) return;
    setSubmitting(true);
    setError('');
    try {
      await createCase({
        consumer_id: consumer.consumer_id,
        risk_score_id: riskScore.id ?? consumer.id,
        assigned_to: selected,
        assignment_note: note,
      });
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-panel">
        <div className="modal-head">
          <h3>Assign Case — {consumer.external_ref}</h3>
          <button className="modal-close" onClick={onClose}><X size={14} /></button>
        </div>
        <div className="modal-body">
          {error && (
            <div className="login-error" style={{ marginBottom: 14 }}>
              <AlertCircle size={14} />{error}
            </div>
          )}
          <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 14 }}>
            Select a field inspector to assign this case to:
          </p>
          {inspectors.length === 0 && (
            <div style={{ textAlign: 'center', color: 'var(--ink-faint)', padding: 20 }}>
              Loading inspectors…
            </div>
          )}
          {inspectors.map(insp => (
            <div
              key={insp.id}
              className={`inspector-option${selected === insp.id ? ' selected' : ''}`}
              onClick={() => setSelected(insp.id)}
            >
              <div className="user-avatar" style={{ width: 32, height: 32, fontSize: 12 }}>
                {insp.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{insp.name}</div>
                <div style={{ fontSize: 11, color: 'var(--ink-faint)', fontFamily: 'var(--f-mono)' }}>
                  {insp.email}
                </div>
              </div>
              <span className={`avail-dot${insp.available ? '' : ' offline'}`} title={insp.available ? 'Active' : 'Offline'} />
            </div>
          ))}
          <div className="field" style={{ marginTop: 14 }}>
            <label>Assignment note (optional)</label>
            <textarea
              placeholder="Any context for the inspector…"
              value={note}
              onChange={e => setNote(e.target.value)}
            />
          </div>
        </div>
        <div className="modal-foot">
          <button className="btn btn-outline btn-sm" onClick={onClose}>Cancel</button>
          <button
            className="btn btn-copper btn-sm"
            disabled={!selected || submitting}
            onClick={handleAssign}
          >
            {submitting ? <Loader size={13} className="spin" /> : <UserPlus size={13} />}
            Assign Case
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Consumer Detail Page ──────────────────────────────────────
export default function ConsumerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [explanation, setExplanation] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [assigned, setAssigned] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([getExplanation(id), getConsumptionHistory(id)])
      .then(([exp, hist]) => { setExplanation(exp); setHistory(hist); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const chartData = history?.trend_series?.map(p => ({
    name: new Date(p.period_start).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' }),
    kwh: p.kwh,
  })) ?? [];

  if (loading) return (
    <div className="panel panel-body" style={{ marginTop: 8 }}>
      {[...Array(4)].map((_, i) => <div key={i} className="skeleton-row" style={{ width: i % 2 ? '60%' : '90%' }} />)}
    </div>
  );

  if (error) return (
    <div className="panel">
      <div className="state-error">
        <div className="state-icon-well err"><AlertCircle size={28} /></div>
        <div className="state-title">Consumer not found</div>
        <div className="state-msg">{error}</div>
        <button className="btn btn-outline" onClick={() => navigate('/risk-queue')}>
          <ChevronLeft size={14} /> Back to Risk Queue
        </button>
      </div>
    </div>
  );

  return (
    <>
      <button className="btn btn-ghost btn-sm mb-4" onClick={() => navigate('/risk-queue')}>
        <ChevronLeft size={15} /> Back to Risk Queue
      </button>

      <div className="folder-tab">
        CONSUMER · {explanation?.external_ref ?? id.slice(0, 8).toUpperCase()}
      </div>

      <div className="panel" style={{ borderTopLeftRadius: 0 }}>
        <div className="panel-body">
          <div className="detail-grid">
            {/* Left column */}
            <div>
              <div style={{ marginBottom: 18 }}>
                <RiskBadge band={explanation?.risk_band} score={explanation?.score} size="lg" />
              </div>

              <dl className="info-list mb-5">
                <dt>Address</dt><dd>{explanation?.consumer_address ?? '—'}</dd>
                <dt>Feeder</dt><dd>{explanation?.feeder ?? '—'}</dd>
                <dt>Meter type</dt><dd>{explanation?.meter_type ?? '—'}</dd>
                <dt>Risk score</dt><dd className="mono">{explanation?.score != null ? (explanation.score * 100).toFixed(1) : '—'}</dd>
              </dl>

              <div className="explanation-slip mb-5">
                {explanation?.explanation_text_en ?? 'No explanation available.'}
              </div>

              {assigned ? (
                <div style={{ padding: '10px 14px', background: '#dde9dd', border: '1px solid var(--risk-low)', borderRadius: 8, fontSize: 13, color: 'var(--risk-low-dim)', fontWeight: 600 }}>
                  ✓ Case assigned successfully.
                </div>
              ) : (
                <button className="btn btn-copper" onClick={() => setShowModal(true)}>
                  <UserPlus size={15} /> Assign Case
                </button>
              )}
            </div>

            {/* Right column — chart */}
            <div className="panel" style={{ padding: '16px 18px 8px' }}>
              <h3 className="plate-label mb-3">Consumption trend — last 12 months (kWh)</h3>
              <div className="graph-paper">
                <ResponsiveContainer width="100%" height={160}>
                  <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
                    <defs>
                      <linearGradient id="kwhGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--copper)" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="var(--copper)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(0,0,0,.06)" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'var(--f-mono)', fill: 'var(--ink-faint)' }} />
                    <YAxis tick={{ fontSize: 10, fontFamily: 'var(--f-mono)', fill: 'var(--ink-faint)' }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--panel-raised)', border: '1px solid var(--seam)', borderRadius: 8, fontFamily: 'var(--f-mono)', fontSize: 12 }}
                      formatter={v => [`${v} kWh`]}
                    />
                    <Area type="monotone" dataKey="kwh" stroke="var(--copper)" strokeWidth={2} fill="url(#kwhGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Urdu explanation */}
              {explanation?.explanation_text_ur && (
                <div style={{ marginTop: 16, padding: '12px 14px', background: 'var(--panel-well)', borderRadius: 8, fontSize: 14, lineHeight: 1.8, textAlign: 'right', direction: 'rtl', fontFamily: 'serif', color: 'var(--ink-soft)', boxShadow: 'var(--shadow-well)' }}>
                  {explanation.explanation_text_ur}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <AssignModal
          consumer={explanation}
          riskScore={explanation}
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); setAssigned(true); }}
        />
      )}
    </>
  );
}
