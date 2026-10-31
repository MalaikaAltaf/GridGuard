import { useState, useEffect } from 'react';
import { getRiskQueue } from '../api';
import RiskBadge from '../components/RiskBadge';
import { AlertTriangle, Diamond, Check } from 'lucide-react';

// Deterministic pin positions based on consumer data
function pinPos(str, idx) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  const x = 8 + ((Math.abs(hash) % 84));
  const y = 8 + ((Math.abs(hash * 7) % 80));
  return { x, y };
}

export default function FeederMap() {
  const [consumers, setConsumers] = useState([]);
  const [tooltip, setTooltip] = useState(null);
  const [bandFilter, setBandFilter] = useState('all');
  const [feederFilter, setFeederFilter] = useState('all');
  const [feeders, setFeeders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRiskQueue({ page: 1, page_size: 100 }).then(res => {
      setConsumers(res.items ?? []);
      const unique = [...new Set(res.items.map(i => i.feeder))].sort();
      setFeeders(unique);
    }).finally(() => setLoading(false));
  }, []);

  const visible = consumers.filter(c => {
    if (bandFilter !== 'all' && c.risk_band !== bandFilter) return false;
    if (feederFilter !== 'all' && c.feeder !== feederFilter) return false;
    return true;
  });

  return (
    <>
      <div className="screen-head">
        <div>
          <h1>Feeder Map</h1>
          <div className="screen-sub">Where flagged consumers are concentrated, by feeder.</div>
        </div>
      </div>

      <div className="panel">
        <div className="filter-bar">
          <div className="filter-item">
            <span className="plate-label">Feeder</span>
            <div className="dial-select">
              <select value={feederFilter} onChange={e => setFeederFilter(e.target.value)}>
                <option value="all">All feeders</option>
                {feeders.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
          </div>
          <div className="filter-item">
            <span className="plate-label">Risk band</span>
            <div className="dial-select">
              <select value={bandFilter} onChange={e => setBandFilter(e.target.value)}>
                <option value="all">All bands</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
        </div>

        <div className="panel-body">
          {loading ? (
            <div className="skeleton-row" style={{ height: 420 }} />
          ) : (
            <div className="map-canvas" onMouseLeave={() => setTooltip(null)}>
              {/* Static grid lines already in CSS. Simulated pins. */}
              {visible.map((c, idx) => {
                const { x, y } = pinPos(c.id, idx);
                return (
                  <div
                    key={c.id}
                    className={`map-pin ${c.risk_band}`}
                    style={{ left: `${x}%`, top: `${y}%` }}
                    onMouseEnter={e => setTooltip({ c, ex: e.clientX, ey: e.clientY })}
                  >
                    <div className="pin-body">
                      <div style={{ transform: 'rotate(45deg)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {c.risk_band === 'high'   ? <AlertTriangle size={10} strokeWidth={3} /> :
                         c.risk_band === 'medium' ? <Diamond size={10} strokeWidth={3} /> :
                                                    <Check size={10} strokeWidth={3} />}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Tooltip */}
              {tooltip && (
                <div className="map-tooltip" style={{ left: '50%', top: 16, transform: 'translateX(-50%)' }}>
                  <div style={{ fontWeight: 700, fontFamily: 'var(--f-mono)', marginBottom: 4 }}>{tooltip.c.external_ref}</div>
                  <div style={{ color: 'var(--ink-soft)', fontSize: 11.5, marginBottom: 4 }}>{tooltip.c.feeder}</div>
                  <RiskBadge band={tooltip.c.risk_band} score={tooltip.c.score} size="sm" />
                </div>
              )}

              {/* Legend */}
              <div className="map-legend">
                <RiskBadge band="high"   size="sm" />
                <RiskBadge band="medium" size="sm" />
                <RiskBadge band="low"    size="sm" />
              </div>

              {/* Disclaimer overlay */}
              <div style={{
                position: 'absolute', top: 12, right: 12, background: 'rgba(246,242,231,.88)',
                border: '1px solid var(--seam)', borderRadius: 8, padding: '8px 12px',
                fontSize: 11, fontFamily: 'var(--f-mono)', color: 'var(--ink-faint)',
                maxWidth: 200, lineHeight: 1.5
              }}>
                ⚠ Simulated pin positions — demo data. Live deployment uses real GPS coordinates.
              </div>

              {visible.length === 0 && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div className="state-empty">
                    <div className="state-icon-well">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width={28} height={28}><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-2-1" /></svg>
                    </div>
                    <div className="state-title">No consumers to show</div>
                    <div className="state-msg">Try changing the filter settings above.</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
