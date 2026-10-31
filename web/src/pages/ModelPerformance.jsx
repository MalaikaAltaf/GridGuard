import { useState, useEffect } from 'react';
import { getModelPerformance } from '../api';
import { AlertCircle, RefreshCw } from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, Legend,
} from 'recharts';

// SVG arc gauge component
function ArcGauge({ value, color, label, sub }) {
  const r = 70;
  const cx = 100;
  const cy = 90;
  const startAngle = 200;
  const endAngle = 340;
  const range = endAngle - startAngle;

  const toRad = (deg) => (deg * Math.PI) / 180;
  const arcPath = (start, end, radius) => {
    const s = { x: cx + radius * Math.cos(toRad(start)), y: cy + radius * Math.sin(toRad(start)) };
    const e = { x: cx + radius * Math.cos(toRad(end)),   y: cy + radius * Math.sin(toRad(end)) };
    const large = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`;
  };

  const fillEnd = startAngle + (value / 100) * range;

  return (
    <div className="panel gauge-card">
      <svg viewBox="0 0 200 110" width="180" height="99" style={{ overflow: 'visible' }}>
        {/* Background track */}
        <path d={arcPath(startAngle, startAngle + range, r)} fill="none" stroke="var(--panel-well-dk)" strokeWidth="10" strokeLinecap="round" />
        {/* Value arc */}
        <path d={arcPath(startAngle, fillEnd, r)} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round" />
        {/* Center value */}
        <text x={cx} y={cy - 8} textAnchor="middle" fill={color} fontSize="26" fontWeight="700" fontFamily="var(--f-mono)">
          {value}%
        </text>
      </svg>
      <div className="gauge-label">{label}</div>
      <div className="gauge-sub">{sub}</div>
    </div>
  );
}

export default function ModelPerformance() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getModelPerformance();
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const trendData = data?.trend?.map(p => ({
    name: new Date(p.date).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
    confirmed: parseFloat(p.confirmed_rate?.toFixed(1) ?? 0),
    falsePos: parseFloat(p.false_positive_rate?.toFixed(1) ?? 0),
    inconclusive: parseFloat(p.inconclusive_rate?.toFixed(1) ?? 0),
  })) ?? [];

  return (
    <>
      <div className="screen-head">
        <div>
          <h1>Model Performance</h1>
          <div className="screen-sub">How often closed cases confirm the AI's flags — the honesty check on the queue above.</div>
        </div>
      </div>

      {loading && (
        <div className="gauge-row mb-5">
          {[1, 2, 3].map(i => (
            <div key={i} className="panel" style={{ padding: 24 }}>
              <div className="skeleton-row" style={{ height: 99 }} />
            </div>
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="panel">
          <div className="state-error">
            <div className="state-icon-well err"><AlertCircle size={28} /></div>
            <div className="state-title">Couldn't load analytics</div>
            <div className="state-msg">{error}</div>
            <button className="btn btn-retry" onClick={load}><RefreshCw size={14} />Retry</button>
          </div>
        </div>
      )}

      {!loading && !error && data?.total_cases === 0 && (
        <div className="panel">
          <div className="state-empty">
            <div className="state-icon-well">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width={28}><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
            </div>
            <div className="state-title">No closed cases yet</div>
            <div className="state-msg">Rates can't be calculated until at least one case is closed with an outcome. This is not a 0% confirmed rate — it's simply not measurable yet.</div>
          </div>
        </div>
      )}

      {!loading && !error && data?.total_cases > 0 && (
        <>
          <div className="gauge-row mb-5">
            <ArcGauge
              value={Math.round(data.confirmed_rate)}
              color="var(--risk-low-dim)"
              label="Confirmed theft"
              sub={`${data.confirmed_count} of ${data.total_cases} closed cases`}
            />
            <ArcGauge
              value={Math.round(data.false_positive_rate)}
              color="var(--copper-deep)"
              label="False positive"
              sub={`${data.false_positive_count} of ${data.total_cases} closed cases`}
            />
            <ArcGauge
              value={Math.round(data.inconclusive_rate)}
              color="var(--ink-soft)"
              label="Inconclusive"
              sub={`${data.inconclusive_count} of ${data.total_cases} closed cases`}
            />
          </div>

          <div className="panel" style={{ padding: '16px 18px 18px' }}>
            <h3 className="plate-label mb-3">Outcome rates — weekly trend (last 12 weeks)</h3>
            <div className="graph-paper">
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={trendData} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
                  <CartesianGrid stroke="rgba(0,0,0,.06)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'var(--f-mono)', fill: 'var(--ink-faint)' }} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'var(--f-mono)', fill: 'var(--ink-faint)' }} unit="%" domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: 'var(--panel-raised)', border: '1px solid var(--seam)', borderRadius: 8, fontFamily: 'var(--f-mono)', fontSize: 12 }}
                    formatter={v => [`${v}%`]}
                  />
                  <Legend wrapperStyle={{ fontFamily: 'var(--f-mono)', fontSize: 11 }} />
                  <Line type="monotone" dataKey="confirmed" name="Confirmed" stroke="var(--risk-low)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="falsePos" name="False Positive" stroke="var(--copper)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="inconclusive" name="Inconclusive" stroke="var(--seam-dark)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </>
  );
}
