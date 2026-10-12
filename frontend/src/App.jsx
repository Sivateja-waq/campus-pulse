import { NavLink, Route, Routes } from "react-router-dom";
import Overview from "./pages/Overview";
import Students from "./pages/Students";
import StudentDetail from "./pages/StudentDetail";
import Segments from "./pages/Segments";
import DataSources from "./pages/DataSources";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/students", label: "Students" },
  { to: "/segments", label: "Segments" },
  { to: "/data", label: "Data sources" },
];

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>Campus Pulse</strong>
            <small>Student success platform</small>
          </div>
        </div>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className="nav-link">
              {n.label}
            </NavLink>
          ))}
        </nav>
        <p className="sidebar-foot">Odd semester, Jul to Oct 2026</p>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/students" element={<Students />} />
          <Route path="/students/:roll" element={<StudentDetail />} />
          <Route path="/segments" element={<Segments />} />
          <Route path="/data" element={<DataSources />} />
        </Routes>
      </main>
    </div>
  );
}
