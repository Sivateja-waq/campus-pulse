import { Link } from "react-router-dom";
import { api } from "../api";
import { useApi } from "../useApi";
import { ErrorNote, Loading } from "../components/bits";

export default function Segments() {
  const { data, error, loading } = useApi(api.segments);
  if (loading) return <Loading what="segments" />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div className="page">
      <header className="page-head">
        <h1>Segments</h1>
        <p className="lede">
          Groups that need the same kind of help, so one intervention can reach all of them. A student sits in the
          first group they match, top to bottom.
        </p>
      </header>

      <div className="segment-list">
        {data.segments.map((s) => (
          <article key={s.key} className={`segment segment-${s.key}`}>
            <div className="segment-main">
              <h2>{s.name}</h2>
              <p className="muted">{s.description}</p>
              <p>
                <span className="muted">What to do: </span>
                {s.action}
              </p>
            </div>
            <dl className="segment-stats">
              <div>
                <dt>Students</dt>
                <dd className="segment-big">{s.count}</dd>
              </div>
              <div>
                <dt>Avg score</dt>
                <dd>{s.avg_score}</dd>
              </div>
              <div>
                <dt>Avg CGPA</dt>
                <dd>{s.avg_cgpa}</dd>
              </div>
              <div>
                <dt>Avg attendance</dt>
                <dd>{s.avg_attendance}%</dd>
              </div>
              <div>
                <dt>High risk</dt>
                <dd>{s.high_risk}</dd>
              </div>
            </dl>
            {s.count > 0 && (
              <Link to={`/students?segment=${s.key}`} className="text-link">
                View the {s.count} students
              </Link>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
