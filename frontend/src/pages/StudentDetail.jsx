import { Link, useParams } from "react-router-dom";
import {
  Bar, BarChart, Cell, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { api } from "../api";
import { useApi } from "../useApi";
import { ErrorNote, Loading, RiskBadge, ScoreBar, num, pct } from "../components/bits";

const MONTH = { "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct" };

export default function StudentDetail() {
  const { roll } = useParams();
  const { data: s, error, loading } = useApi(() => api.student(roll), [roll]);

  if (loading) return <Loading what="student" />;
  if (error) return <ErrorNote error={error} />;

  const diff = +(s.success_score - s.baseline_score).toFixed(1);
  const contributions = [...s.components]
    .map((c) => ({ label: c.label, value: +c.contribution.toFixed(1) }))
    .sort((a, b) => a.value - b.value);
  const attendance = s.attendance_trend.map((p) => ({ ...p, label: MONTH[p.period.slice(5)] || p.period }));

  return (
    <div className="page">
      <Link to="/students" className="text-link back">All students</Link>

      <header className="student-head">
        <div>
          <h1>{s.name}</h1>
          <p className="muted">
            {s.roll_no}, {s.department}, year {s.year}
          </p>
          <div className="tags">
            <RiskBadge level={s.risk_level} />
            <span className="tag">{s.segment_name}</span>
          </div>
        </div>
        <div className="score-card">
          <span className="score-big">{num(s.success_score)}</span>
          <span className="score-sub">
            Success score.{" "}
            {diff >= 0 ? `${diff} above` : `${Math.abs(diff)} below`} the year {s.year} average of {s.baseline_score}
          </span>
        </div>
      </header>

      <div className="grid-2">
        <section className="panel">
          <h2>Why this score</h2>
          <p className="muted small">
            Points gained or lost against the year {s.year} average, by component. Together they explain the{" "}
            {Math.abs(diff)} point gap {diff >= 0 ? "above" : "below"} average.
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={contributions} layout="vertical" margin={{ top: 4, right: 16, left: 20, bottom: 0 }}>
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="label" width={130} tick={{ fontSize: 12 }} />
              <ReferenceLine x={0} stroke="var(--ink)" />
              <Tooltip formatter={(v) => [`${v > 0 ? "+" : ""}${v} pts`, "Effect on score"]} />
              <Bar dataKey="value">
                {contributions.map((c) => (
                  <Cell key={c.label} fill={c.value >= 0 ? "var(--green)" : "var(--red)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Components</h2>
          <p className="muted small">Each scored 0 to 100. The tick marks the year average.</p>
          <ul className="component-list">
            {s.components.map((c) => (
              <li key={c.key}>
                <div className="component-top">
                  <span>{c.label}</span>
                  <span className="muted small">weight {Math.round(c.weight * 100)}%</span>
                  <span className="strong">{num(c.score, 0)}</span>
                </div>
                <ScoreBar value={c.score} avg={c.year_avg} />
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid-2">
        <section className="panel">
          <h2>Flags</h2>
          {s.flags.length === 0 && <p className="muted">Nothing flagged.</p>}
          <ul className="flags">
            {s.flags.map((f, i) => (
              <li key={i} className={`flag flag-${f.severity}`}>{f.text}</li>
            ))}
          </ul>
          <div className="risk-pair">
            <RiskModelBox title="Academic risk" prob={s.academic_risk} factors={s.academic_factors} />
            <RiskModelBox
              title="Placement risk"
              prob={s.placement_risk}
              factors={s.placement_factors}
              note={s.year < 3 ? "Starts from year 3" : null}
            />
          </div>
        </section>

        <section className="panel">
          <h2>Suggested next steps</h2>
          <ol className="actions">
            {s.recommendations.map((r, i) => (
              <li key={i}>
                <strong>{r.area}.</strong> {r.action}
              </li>
            ))}
          </ol>
          {s.segment_info?.action && (
            <p className="segment-note">
              <span className="muted">Segment playbook: </span>
              {s.segment_info.action}
            </p>
          )}
        </section>
      </div>

      <div className="grid-2">
        <section className="panel">
          <h2>Attendance by month</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={attendance} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <ReferenceLine y={75} stroke="var(--amber)" strokeDasharray="4 4" label={{ value: "75% required", fontSize: 11, position: "insideBottomRight" }} />
              <Tooltip />
              <Line dataKey="value" name="Attendance %" stroke="var(--navy)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </section>
        <section className="panel">
          <h2>LMS logins by week</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={s.lms_trend} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" name="Logins" fill="var(--green)" />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>

      <div className="grid-2">
        <section className="panel">
          <h2>Subjects this semester</h2>
          <table className="table compact">
            <thead>
              <tr>
                <th>Subject</th>
                <th className="num">Marks</th>
                <th className="num">Attendance</th>
              </tr>
            </thead>
            <tbody>
              {s.subjects.map((sub) => (
                <tr key={sub.subject}>
                  <td>{sub.subject}</td>
                  <td className={`num ${sub.marks != null && sub.marks < 40 ? "warn" : ""}`}>{num(sub.marks, 0)}</td>
                  <td className={`num ${sub.attendance_pct < 75 ? "warn" : ""}`}>{num(sub.attendance_pct, 0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="panel">
          <h2>Raw indicators</h2>
          <dl className="indicators">
            {Object.entries(s.indicators).map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v == null ? "Not attempted" : Number.isInteger(v) ? v : num(v)}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}

function RiskModelBox({ title, prob, factors, note }) {
  return (
    <div className="risk-box">
      <div className="risk-box-top">
        <span>{title}</span>
        <span className="strong">{prob == null ? "–" : pct(prob)}</span>
      </div>
      {note && <p className="muted small">{note}</p>}
      {prob != null && factors.length > 0 && (
        <p className="small">
          Pushed up by: {factors.map((f) => f.label.toLowerCase()).join(", ")}
        </p>
      )}
      {prob != null && factors.length === 0 && <p className="small muted">No single factor stands out.</p>}
    </div>
  );
}
