import { Link, useNavigate } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api";
import { useApi } from "../useApi";
import { ErrorNote, Loading, RISK_COLORS, RiskBadge, num } from "../components/bits";

const MONTH = { "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov" };
const monthLabel = (p) => MONTH[p.slice(5)] || p;

export default function Overview() {
  const { data, error, loading } = useApi(api.overview);
  const navigate = useNavigate();

  if (loading) return <Loading what="overview" />;
  if (error) return <ErrorNote error={error} />;
  if (data.empty) return <p className="pad">No students loaded yet. Run the pipeline from the Data sources page.</p>;

  const { kpis } = data;
  const atRiskShare = Math.round((kpis.high / kpis.students) * 100);

  return (
    <div className="page">
      <header className="page-head">
        <h1>
          {kpis.high} of {kpis.students} students need attention this week
        </h1>
        <p className="lede">
          {atRiskShare}% are flagged high risk and another {kpis.medium} are worth watching. Average success
          score is {kpis.avg_score}, average attendance {kpis.avg_attendance}%.
        </p>
      </header>

      <section className="stat-strip">
        <Stat label="High risk" value={kpis.high} tone="high" to="/students?risk=High" />
        <Stat label="Medium risk" value={kpis.medium} tone="medium" to="/students?risk=Medium" />
        <Stat label="Low risk" value={kpis.low} tone="low" to="/students?risk=Low" />
        <Stat label="Avg success score" value={kpis.avg_score} />
        <Stat label="Avg attendance" value={`${kpis.avg_attendance}%`} />
      </section>

      <div className="grid-2">
        <section className="panel">
          <h2>What the data is saying</h2>
          <ul className="insights">
            {data.insights.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>Start with these students</h2>
          <table className="table compact">
            <thead>
              <tr>
                <th>Student</th>
                <th className="num">Score</th>
                <th className="num">Attend.</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {data.watchlist.map((s) => (
                <tr key={s.roll_no} className="clickable" onClick={() => navigate(`/students/${s.roll_no}`)}>
                  <td>
                    <div className="cell-name">{s.name}</div>
                    <div className="muted small">{s.roll_no}</div>
                  </td>
                  <td className="num">{num(s.success_score)}</td>
                  <td className="num">{num(s.attendance_pct, 0)}%</td>
                  <td className="small">{s.segment_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Link to="/students?risk=High" className="text-link">
            See all {kpis.high} high-risk students
          </Link>
        </section>
      </div>

      <div className="grid-2">
        <section className="panel">
          <h2>Success score distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.score_distribution} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="range" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Students" fill="var(--navy)" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Risk by department</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.risk_by_department} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="department" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {["High", "Medium", "Low"].map((lvl) => (
                <Bar key={lvl} dataKey={lvl} stackId="r" fill={RISK_COLORS[lvl]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>

      <div className="grid-2">
        <section className="panel">
          <h2>Average attendance by month</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.attendance_trend} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="period" tickFormatter={monthLabel} tick={{ fontSize: 12 }} />
              <YAxis domain={[60, 100]} tick={{ fontSize: 12 }} unit="%" />
              <Tooltip labelFormatter={monthLabel} />
              <Line dataKey="value" name="Attendance %" stroke="var(--navy)" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Average LMS logins per week</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.lms_trend} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 5]} allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line dataKey="value" name="Logins" stroke="var(--green)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="panel">
        <h2>Segments</h2>
        <div className="segment-row">
          {data.segments.map((s) => (
            <Link key={s.key} to={`/students?segment=${s.key}`} className="segment-chip">
              <span className="segment-count">{s.count}</span>
              <span>{s.name}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, tone, to }) {
  const body = (
    <>
      <span className="stat-value">{value}</span>
      <span className="stat-label">
        {tone && <RiskBadge level={tone[0].toUpperCase() + tone.slice(1)} />}
        {!tone && label}
      </span>
    </>
  );
  return to ? (
    <Link to={to} className={`stat stat-${tone || "plain"}`}>
      {body}
    </Link>
  ) : (
    <div className="stat">{body}</div>
  );
}
