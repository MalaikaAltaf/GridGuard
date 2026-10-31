// Reusable RiskBadge component — LED + icon + text
// Matches the exact visual from the HTML mockup

import { AlertTriangle, Diamond, Check } from 'lucide-react';

const BAND_CONFIG = {
  high: {
    cls: 'high',
    Icon: AlertTriangle,
    label: 'High',
  },
  medium: {
    cls: 'medium',
    // Diamond shape for medium
    Icon: Diamond,
    label: 'Medium',
  },
  low: {
    cls: 'low',
    Icon: Check,
    label: 'Low',
  },
};

export default function RiskBadge({ band, score, size = '' }) {
  const cfg = BAND_CONFIG[band] ?? BAND_CONFIG.low;
  const { Icon } = cfg;
  const iconSize = size === 'lg' ? 21 : size === 'sm' ? 11 : 14;

  return (
    <div className={`risk-badge${size ? ' ' + size : ''}`}>
      <span className={`risk-led ${cfg.cls}`}>
        <Icon size={iconSize} strokeWidth={2.6} />
      </span>
      <span className="risk-text">
        {cfg.label}
        {score !== undefined && (
          <small>Score {typeof score === 'number' ? (score * 100).toFixed(0) : score}</small>
        )}
      </span>
    </div>
  );
}
