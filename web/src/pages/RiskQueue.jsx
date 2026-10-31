import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRiskQueue } from '../api';
import RiskBadge from '../components/RiskBadge';
import { Filter, RefreshCw, AlertCircle } from 'lucide-react';

const METER_TYPES = ['Single Phase', 'Three Phase', 'CT-Metered'];
const RISK_BANDS = ['high', 'medium', 'low'];
const PAGE_SIZE = 25;

export default function RiskQueue() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ risk_band: 'all', meter_type: 'all', feeder: 'all' });
  const [feeders, setFeeders] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page,
        page_size: PAGE_SIZE,
        ...(filters.risk_band !== 'all' ? { risk_band: filters.risk_band } : {}),
        ...(filters.meter_type !== 'all' ? { meter_type: filters.meter_type } : {}),
        ...(filters.feeder !== 'all' ? { feeder: filters.feeder } : {}),
      };
      const res = await getRiskQueue(params);
      setData(res);
      // Collect unique feeders for the filter dropdown (from first full load)
      if (!feeders.length && res.items?.length) {
        const all = await getRiskQueue({ page: 1, page_size: 100 });
        const unique = [...new Set(all.items.map(i => i.feeder))].sort();
        setFeeders(unique);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => { load(); }, [load]);

  const setFilter = (key, val) => {
    setFilters(f => ({ ...f, [key]: val }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({ risk_band: 'all', meter_type: 'all', feeder: 'all' });
    setPage(1);
  };

  const totalPages = data?.total_pages ?? 1;

  return (
    <>
      <div className="screen-head">
        <div>
          <h1>Risk Queue</h1>
          <div className="screen-sub">Ranked by risk score. Highest-priority consumers surface first.</div>
        </div>
      </div>

      <div className="panel">
        {/* Filter Bar */}
        <div className="filter-bar">
          <div className="filter-item">
            <span className="plate-label">Feeder</span>
            <div className="dial-select">
              <select value={filters.feeder} onChange={e => setFilter('feeder', e.target.value)}>
                <option value="all">All feeders</option>
                {feeders.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
          </div>
          <div className="filter-item">
            <span className="plate-label">Risk band</span>
            <div className="dial-select">
              <select value={filters.risk_band} onChange={e => setFilter('risk_band', e.target.value)}>
                <option value="all">All bands</option>
                {RISK_BANDS.map(b => <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="filter-item">
            <span className="plate-label">Meter type</span>
            <div className="dial-select">
              <select value={filters.meter_type} onChange={e => setFilter('meter_type', e.target.value)}>
                <option value="all">All types</option>
                {METER_TYPES.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>
          <button className="clear-filters" onClick={clearFilters}>Clear filters</button>
          {data && (
            <div className="result-count">{data.total} consumer{data.total !== 1 ? 's' : ''}</div>
          )}
        </div>

        {/* States */}
        {loading && (
          <div style={{ padding: 18 }}>
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton-row" />)}
          </div>
        )}

        {error && !loading && (
          <div className="state-error">
            <div className="state-icon-well err"><AlertCircle size={28} /></div>
            <div className="state-title">Couldn't load the risk queue</div>
            <div className="state-msg">{error}</div>
            <button className="btn btn-retry" onClick={load}><RefreshCw size={14} />Retry</button>
          </div>
        )}

        {!loading && !error && data?.items?.length === 0 && (
          <div className="state-empty">
            <div className="state-icon-well"><Filter size={28} /></div>
            <div className="state-title">No consumers match these filters</div>
            <div className="state-msg">Try widening your risk band, feeder, or meter-type selection.</div>
            <button className="btn btn-outline btn-sm" onClick={clearFilters}>Clear filters</button>
          </div>
        )}

        {!loading && !error && data?.items?.length > 0 && (
          <>
            <div className="table-wrap">
              <table className="rq">
                <thead>
                  <tr>
                    <th>Consumer</th>
                    <th>Feeder</th>
                    <th>Meter type</th>
                    <th className="num">Score</th>
                    <th>Risk band</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row, idx) => (
                    <tr
                      key={row.id}
                      onClick={() => navigate(`/consumer/${row.id}`)}
                      className={idx < 3 && page === 1 ? `rank-${idx + 1}` : ''}
                    >
                      <td>
                        <span className="ref">{row.external_ref}</span>
                        <span className="addr">{row.address}</span>
                      </td>
                      <td>{row.feeder}</td>
                      <td><span className="meter-chip">{row.meter_type}</span></td>
                      <td className="num">
                        <span className="score-well">{(row.score * 100).toFixed(0)}</span>
                      </td>
                      <td><RiskBadge band={row.risk_band} size="sm" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <div className="pg-info">
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, data.total)} of {data.total}
              </div>
              <div className="pg-controls">
                <button className="pg-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹</button>
                <span className="mono" style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
                  {page} / {totalPages}
                </span>
                <button className="pg-btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>›</button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
