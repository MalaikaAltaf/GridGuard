import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCaseDetail, getCaseAuditLog } from '../api';
import RiskBadge from '../components/RiskBadge';
import { ChevronLeft, Clock, AlertCircle, FileText, User, Cpu } from 'lucide-react';

const STATUS_LABELS = {
  assigned: 'Assigned',
  in_progress: 'In Progress',
  closed_confirmed: 'Confirmed Theft',
  closed_false_positive: 'False Positive',
  closed_inconclusive: 'Inconclusive',
};

function StatusChip({ status }) {
  return <span className={`status-chip ${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}

function fmt(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [auditLog, setAuditLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAudit, setShowAudit] = useState(false);

  useEffect(() => {
    setLoading(true);
    getCaseDetail(id)
      .then(d => { setCaseData(d); return getCaseAuditLog(id); })
      .then(a => setAuditLog(a))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="panel panel-body" style={{ marginTop: 8 }}>
      {[...Array(5)].map((_, i) => <div key={i} className="skeleton-row" style={{ width: i % 2 ? '50%' : '90%' }} />)}
    </div>
  );

  if (error) return (
    <div className="panel">
      <div className="state-error">
        <div className="state-icon-well err"><AlertCircle size={28} /></div>
        <div className="state-title">Case not found</div>
        <div className="state-msg">{error}</div>
        <button className="btn btn-outline" onClick={() => navigate('/cases')}>
          <ChevronLeft size={14} /> Back to Cases
        </button>
      </div>
    </div>
  );

  const isClosed = caseData?.status?.startsWith('closed_');

  return (
    <>
      <button className="btn btn-ghost btn-sm mb-4" onClick={() => navigate('/cases')}>
        <ChevronLeft size={15} /> Back to Case List
      </button>

      <div className="folder-tab">
        CASE · {caseData?.consumer_external_ref ?? id.slice(0, 8).toUpperCase()}
      </div>

      <div className="panel" style={{ borderTopLeftRadius: 0 }}>
        <div className="panel-body">
          <div className="detail-grid">
            {/* Left: Consumer info + assignment */}
            <div>
              <h3 className="plate-label mb-3">Consumer &amp; original flag</h3>
              <dl className="info-list mb-4">
                <dt>Address</dt><dd>{caseData?.consumer_address ?? '—'}</dd>
                <dt>Feeder</dt><dd>{caseData?.feeder ?? '—'}</dd>
                <dt>Meter type</dt><dd>{caseData?.meter_type ?? '—'}</dd>
                <dt>Status</dt><dd><StatusChip status={caseData?.status} /></dd>
              </dl>

              <div style={{ marginBottom: 16 }}>
                <RiskBadge band={caseData?.risk_band} score={caseData?.risk_score} />
              </div>

              <div className="explanation-slip mb-5">
                {caseData?.explanation_text_en ?? 'No explanation available.'}
              </div>

              <h3 className="plate-label mb-3">Assignment</h3>
              <dl className="info-list mb-4">
                <dt>Inspector</dt><dd>{caseData?.inspector_name ?? '—'}</dd>
                <dt>Assigned by</dt><dd>{caseData?.assigned_by_name ?? '—'}</dd>
                <dt>Assigned on</dt><dd className="mono">{fmt(caseData?.created_at)}</dd>
                {caseData?.assignment_note && (
                  <><dt>Note</dt><dd>{caseData.assignment_note}</dd></>
                )}
              </dl>

              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setShowAudit(s => !s)}
              >
                <FileText size={14} />
                {showAudit ? 'Hide audit log' : 'View full audit log'}
              </button>
            </div>

            {/* Right: Inspection outcome or pending stamp */}
            <div>
              {!isClosed ? (
                <div className="panel" style={{ padding: 24, textAlign: 'center' }}>
                  <div className="stamp">
                    <Clock size={16} /> Awaiting inspection
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginTop: 14, lineHeight: 1.6 }}>
                    The inspector hasn't submitted a site visit yet. This section fills in once the inspection is recorded.
                  </p>
                </div>
              ) : (
                <div className="panel">
                  <div className="panel-head">
                    <h3>Inspection outcome</h3>
                    <StatusChip status={caseData.status} />
                  </div>
                  <div className="panel-body">
                    {caseData.inspection_note && (
                      <>
                        <h4 className="plate-label mb-3" style={{ fontSize: '10.5px' }}>Inspector's note</h4>
                        <p style={{ fontSize: 13.5, lineHeight: 1.6, marginBottom: 16 }}>{caseData.inspection_note}</p>
                      </>
                    )}
                    {caseData.gps_lat && (
                      <div style={{ marginBottom: 14 }}>
                        <h4 className="plate-label mb-3" style={{ fontSize: '10.5px' }}>GPS location</h4>
                        <div className="gps-readout">{caseData.gps_lat}° N, {caseData.gps_lng}° E</div>
                      </div>
                    )}
                    {caseData.photo_url && (
                      <div style={{ marginBottom: 14 }}>
                        <h4 className="plate-label mb-3" style={{ fontSize: '10.5px' }}>Site photo</h4>
                        <img
                          src={caseData.photo_url}
                          alt="Inspection site"
                          style={{ width: 150, borderRadius: 6, border: '6px solid #fff', boxShadow: '0 3px 8px rgba(0,0,0,.3)', transform: 'rotate(-2deg)' }}
                        />
                      </div>
                    )}
                    <div style={{ fontSize: 12, color: 'var(--ink-faint)', fontFamily: 'var(--f-mono)', marginTop: 12 }}>
                      Submitted: {fmt(caseData.submitted_at)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Audit log */}
          {showAudit && auditLog && (
            <div style={{ marginTop: 24, borderTop: '1px solid var(--seam)', paddingTop: 20 }}>
              <h3 className="plate-label mb-4">Audit log — full history</h3>
              <div className="timeline">
                {auditLog.entries?.map((entry, i) => (
                  <div key={i} className="tl-entry">
                    <div className={`tl-node ${entry.actor_id ? 'human' : 'system'}`}>
                      {entry.actor_id ? <User size={15} /> : <Cpu size={15} />}
                    </div>
                    <div className="tl-content">
                      <div className="tl-action">{entry.action?.replace(/_/g, ' ')}</div>
                      <div className="tl-meta">
                        {entry.actor_name ?? 'System'} · {fmt(entry.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
