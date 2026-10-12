import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useApi } from "../useApi";
import { ErrorNote, Loading, RiskBadge, num, pct } from "../components/bits";

const COLUMNS = [
  { key: "roll_no", label: "Roll no" },
  { key: "name", label: "Name" },
  { key: "department", label: "Dept" },
  { key: "year", label: "Year", num: true },
  { key: "success_score", label: "Score", num: true },
  { key: "risk", label: "Risk" },
  { key: "cgpa", label: "CGPA", num: true },
  { key: "attendance_pct", label: "Attend.", num: true },
  { key: "academic_risk", label: "Acad. risk", num: true },
  { key: "placement_risk", label: "Place. risk", num: true },
  { key: "segment", label: "Segment" },
];

export default function Students() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const filters = Object.fromEntries(params.entries());
  const query = useMemo(() => ({ sort: "risk", ...filters }), [params]); // eslint-disable-line

  const meta = useApi(api.meta);
  const list = useApi(() => api.students(query), [params.toString()]);

  const update = (key, value) => {
    const next = new URLSearchParams(params);
    value ? next.set(key, value) : next.delete(key);
    setParams(next, { replace: true });
  };

  const toggleSort = (key) => {
    const current = query.sort;
    update("sort", current === key ? `-${key}` : key);
  };

  return (
    <div className="page">
      <header className="page-head">
        <h1>Students</h1>
        <p className="lede">Sorted with the highest-risk, lowest-scoring students first. Click a row for the full picture.</p>
      </header>

      <div className="filters">
        <input
          type="search"
          placeholder="Search name or roll number"
          defaultValue={filters.q || ""}
          onChange={(e) => update("q", e.target.value)}
        />
        <Select label="Department" value={filters.department} onChange={(v) => update("department", v)}
          options={(meta.data?.departments || []).map((d) => [d, d])} />
        <Select label="Year" value={filters.year} onChange={(v) => update("year", v)}
          options={(meta.data?.years || []).map((y) => [y, `Year ${y}`])} />
        <Select label="Risk" value={filters.risk} onChange={(v) => update("risk", v)}
          options={["High", "Medium", "Low"].map((r) => [r, r])} />
        <Select label="Segment" value={filters.segment} onChange={(v) => update("segment", v)}
          options={(meta.data?.segments || []).map((s) => [s.key, s.name])} />
        {params.toString() && (
          <button className="btn-quiet" onClick={() => setParams({})}>
            Clear filters
          </button>
        )}
      </div>

      {list.loading && !list.data && <Loading what="students" />}
      {list.error && <ErrorNote error={list.error} />}
      {list.data && (
        <>
          <p className="muted small">{list.data.count} students</p>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  {COLUMNS.map((c) => (
                    <th key={c.key} className={c.num ? "num" : ""}>
                      <button className="th-sort" onClick={() => toggleSort(c.key)}>
                        {c.label}
                        {query.sort === c.key && " ↑"}
                        {query.sort === `-${c.key}` && " ↓"}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {list.data.results.map((s) => (
                  <tr key={s.roll_no} className="clickable" onClick={() => navigate(`/students/${s.roll_no}`)}>
                    <td className="mono">{s.roll_no}</td>
                    <td className="cell-name">{s.name}</td>
                    <td>{s.department}</td>
                    <td className="num">{s.year}</td>
                    <td className="num strong">{num(s.success_score)}</td>
                    <td><RiskBadge level={s.risk_level} /></td>
                    <td className="num">{num(s.cgpa, 2)}</td>
                    <td className={`num ${s.attendance_pct < 75 ? "warn" : ""}`}>{num(s.attendance_pct, 0)}%</td>
                    <td className="num">{pct(s.academic_risk)}</td>
                    <td className="num">{pct(s.placement_risk)}</td>
                    <td className="small">{s.segment_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <select aria-label={label} value={value || ""} onChange={(e) => onChange(e.target.value)}>
      <option value="">All {label.toLowerCase()}s</option>
      {options.map(([v, text]) => (
        <option key={v} value={v}>
          {text}
        </option>
      ))}
    </select>
  );
}
