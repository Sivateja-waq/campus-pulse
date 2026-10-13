import { useState } from "react";
import { api } from "../api";
import { useApi } from "../useApi";
import { ErrorNote, Loading } from "../components/bits";

export default function DataSources() {
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const { data, error, loading } = useApi(api.dataReport, [version]);

  const act = async (fn, done) => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fn();
      setMessage({ ok: true, text: done(res) });
      setVersion((v) => v + 1);
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };

  
if (loading && !data) return <Loading what="data report" />;
if (error) return <ErrorNote error={error} />;

if (data?.empty) {
  return (
    <div className="page">
      <header className="page-head">
        <h1>Data sources</h1>
        <p className="lede">
          No data pipeline has run yet. Upload the required CSV files to get started.
        </p>
        <button
          className="btn"
          disabled={busy}
          onClick={() =>
            act(api.rerun, r =>
              `Recalculated scores for ${r.students_processed.toLocaleString()} students.`
            )
          }
        >
          {busy ? "Working..." : "Recalculate scores"}
        </button>
        {message && (
          <p className={message.ok ? "ok-note" : "error-note"}>
            {message.text}
          </p>
        )}
      </header>
      <section className="panel">
        <h2>No data available yet</h2>
        <p>
          Upload controls will appear when the backend provides the source list.
          The backend currently has no pipeline report.
        </p>
      </section>
    </div>
  );
}


  return (
    <div className="page">
      <header className="page-head">
        <h1>Data sources</h1>
        <p className="lede">
          Eight exports from six campus systems, merged into one record per student. Every fix the pipeline made is
          listed so nothing happens silently.
        </p>
        <div className="head-actions">
          <button className="btn" disabled={busy} onClick={() => act(api.rerun, (r) => `Recalculated scores for ${r.students} students.`)}>
            {busy ? "Working…" : "Recalculate scores"}
          </button>
          {data.updated_at && (
            <span className="muted small">Last run {new Date(data.updated_at).toLocaleString()}</span>
          )}
        </div>
        {message && <p className={message.ok ? "ok-note" : "error-note"}>{message.text}</p>}
      </header>

      <section className="panel">
        <h2>What happened to each file</h2>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>System</th>
                <th>File</th>
                <th className="num">Rows in</th>
                <th className="num">Rows used</th>
                <th>Cleaning applied</th>
                <th>Replace file</th>
              </tr>
            </thead>
            <tbody>
              {data.sources.map((src) => (
                <tr key={src.key}>
                  <td className="strong">{src.system}</td>
                  <td className="mono small">{src.file}</td>
                  <td className="num">{src.rows_in.toLocaleString()}</td>
                  <td className="num">{src.rows_used.toLocaleString()}</td>
                  <td className="small">
                    {src.fixes.length === 0 && <span className="muted">Clean</span>}
                    <ul className="fix-list">
                      {src.fixes.map((f, i) => (
                        <li key={i}>
                          {f.issue}: <strong>{f.rows}</strong>
                        </li>
                      ))}
                    </ul>
                    {src.unmatched_count > 0 && (
                      <p className="muted">Unknown ids: {src.unmatched_ids.join(", ")}</p>
                    )}
                  </td>
                  <td>
                    <label className="btn-quiet file-btn">
                      Upload CSV
                      <input
                        type="file"
                        accept=".csv"
                        disabled={busy}
                        onChange={(e) => {
                          const file = e.target.files[0];
                          e.target.value = "";
                          if (file) act(() => api.upload(src.key, file), () => `${src.file} replaced and scores recalculated.`);
                        }}
                      />
                    </label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Risk models</h2>
        <p className="muted small">
          Logistic regression trained on {data.alumni_rows?.toLocaleString()} records from last year's batch, checked on a
          25% hold-out. AUC of 0.5 is a coin flip, 1.0 is perfect.
        </p>
        <div className="grid-2">
          {data.models.map((m) => (
            <div key={m.name} className="model-box">
              <div className="component-top">
                <strong>{m.name}</strong>
                <span>AUC {m.auc}</span>
              </div>
              <table className="table compact">
                <thead>
                  <tr>
                    <th>Indicator</th>
                    <th className="num">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {m.coefficients.map((c) => (
                    <tr key={c.feature}>
                      <td>{c.feature}</td>
                      <td className={`num ${c.weight > 0 ? "warn" : "good"}`}>
                        {c.weight > 0 ? "+" : ""}
                        {c.weight}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="muted small">Positive weight raises risk, negative lowers it (per standard deviation).</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
