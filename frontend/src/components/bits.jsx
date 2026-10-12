// Small shared pieces used across pages.

export const RISK_COLORS = { High: "#B3412F", Medium: "#B7791F", Low: "#3D7A5A" };

export function RiskBadge({ level }) {
  return <span className={`risk risk-${level?.toLowerCase()}`}>{level}</span>;
}

export function ScoreBar({ value, max = 100, avg }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="scorebar" title={avg != null ? `Year average ${avg}` : undefined}>
      <div className="scorebar-fill" style={{ width: `${pct}%` }} />
      {avg != null && <div className="scorebar-avg" style={{ left: `${(avg / max) * 100}%` }} />}
    </div>
  );
}

export function Loading({ what = "data" }) {
  return <p className="muted pad">Loading {what}…</p>;
}

export function ErrorNote({ error }) {
  return (
    <div className="error-note">
      <strong>Couldn't reach the API.</strong> {error.message}. Check that Django is running on port 8000
      and that you've run <code>python manage.py run_pipeline</code>.
    </div>
  );
}

export const pct = (v) => (v == null ? "–" : `${Math.round(v * 100)}%`);
export const num = (v, d = 1) => (v == null ? "–" : Number(v).toFixed(d));
