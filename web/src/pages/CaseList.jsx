import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCases } from '../api';
import { AlertCircle, RefreshCw, Clipboard } from 'lucide-react';

const STATUS_LABELS = {
  assigned: 'Assigned',
  in_progress: 'In Progress',
  closed_confirmed: 'Confirmed Theft',
  closed_false_positive: 'False Positive',
  closed_inconclusive: 'Inconclusive',
};

function StatusChip({ status }) {
  return (
    <span className={`status-chip ${status}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

export default function CaseList() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [feederFilter, setFeederFilter] = useState('all');
  const [feeders, setFeeders] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page,
        page_size: 25,
        ...(statusFilter !== 'all' ? { status_filter: statusFilter } : {}),
        ...(feederFilter !== 'all' ? { feeder: feederFilter } : {}),
      };
      const res = await getCases(params);
      setData(res);
      if (!feeders.length && res.items?.length) {
        const all = await getCases({ page: 1, page_size: 100 });
        const unique = [...new Set(all.items.map(i => i.feeder).filter(Boolean))].sort();
        setFeeders(unique);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, feederFilter]);

  useEffect(() => { load(); }, [load]);

  const fmt = (iso) => iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

  const totalPages = data?.total_pages ?? 1;

  return (
    <>
      <div className="screen-head">
        <div>
          <h1>Case List</h1>
          <div className="screen-sub">Every case assigned to a field inspector, and its current status.</div>
        </div>
      </div>

      <div className="panel">
        <div className="filter-bar">
          <div className="filter-item">
            <span className="plate-label">Status</span>
            <div className="dial-select">
              <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
                <option value="all">All statuses</option>
                <option value="assigned">Assigned</option>
                <option value="in_progress">In progress</option>
                <option value="closed_confirmed">Confirmed theft</option>
                <option value="closed_false_positive">False positive</option>
                <option value="closed_inconclusive">Inconclusive</option>
              </select>
            </div>
          </div>
          <div className="filter-item">
            <span className="plate-label">Feeder</span>
            <div className="dial-select">
              <select value={feederFilter} onChange={e => { setFeederFilter(e.target.value); setPage(1); }}>
                <option value="all">All feeders</option>
                {feeders.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
          </div>
          {data && <div className="result-count">{data.total} case{data.total !== 1 ? 's' : ''}</div>}
        </div>

        {loading && (
          <div style={{ padding: 18 }}>
            {[...Array(5)].map((_, i) => <div key={i} className="skeleton-row" />)}
          </div>
        )}

        {error && !loading && (
          <div className="state-error">
            <div className="state-icon-well err"><AlertCircle size={28} /></div>
            <div className="state-title">Couldn't load cases</div>
            <div className="state-msg">{error}</div>
            <button className="btn btn-retry" onClick={load}><RefreshCw size={14} />Retry</button>
          </div>
        )}

        {!loading && !error && data?.items?.length === 0 && (
          <div className="state-empty">
            <div className="state-icon-well"><Clipboard size={28} /></div>
            <div className="state-title">No cases yet</div>
            <div className="state-msg">Assign a flagged consumer from the Risk Queue to open your first case.</div>
            <button className="btn btn-outline btn-sm" onClick={() => navigate('/risk-queue')}>Go to Risk Queue</button>
          </div>
        )}

        {!loading && !error && data?.items?.length > 0 && (
          <>
            <div className="table-wrap">
              <table className="rq">
                <thead>
                  <tr>
                    <th>Consumer</th>
                    <th>Inspector</th>
                    <th>Risk band</th>
                    <th>Status</th>
                    <th>Date created</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map(row => (
                    <tr key={row.id} onClick={() => navigate(`/cases/${row.id}`)}>
                      <td>
                        <span className="ref">{row.consumer_external_ref}</span>
                        <span className="addr">{row.feeder}</span>
                      </td>
                      <td>{row.inspector_name ?? '—'}</td>
                      <td>
                        <span className={`meter-chip`} style={{ background: row.risk_band === 'high' ? '#f1dcd8' : row.risk_band === 'medium' ? '#f3e6d6' : '#dde9dd', borderColor: 'transparent' }}>
                          {row.risk_band?.toUpperCase() ?? '—'}
                        </span>
                      </td>
                      <td><StatusChip status={row.status} /></td>
                      <td className="mono" style={{ fontSize: 12 }}>{fmt(row.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <div className="pg-info">
                Page {page} of {totalPages} · {data.total} total
              </div>
              <div className="pg-controls">
                <button className="pg-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹</button>
                <span className="mono" style={{ fontSize: 12, color: 'var(--ink-soft)' }}>{page} / {totalPages}</span>
                <button className="pg-btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>›</button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
