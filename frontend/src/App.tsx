import "./App.css";

const scaffoldFeatures = [
  "FastAPI backend with /api/health endpoint",
  "SQLite bootstrap tables for day logs, meals, activities, and uploads",
  "React + TypeScript shell ready for day-log UI work",
  "Shared API contract docs for cross-branch consistency"
];

function App() {
  return (
    <main className="app-shell" aria-label="app shell">
      <section className="hero">
        <p className="eyebrow">Foundation Scaffold</p>
        <h1>Personal Endurance Trainer Log</h1>
        <p>
          This frontend intentionally stays small so feature branches can focus on
          day-log experiences without guessing setup, folders, or API entry points.
        </p>
      </section>

      <section className="panel" aria-label="scaffold checklist">
        <h2>Ready for parallel feature work</h2>
        <ul>
          {scaffoldFeatures.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      </section>

      <section className="panel panel-compact" aria-label="next steps">
        <h2>Immediate next step</h2>
        <p>
          Build the day-log flow in <code>frontend/src</code> while keeping
          contracts aligned with <code>docs/api-contract.md</code>.
        </p>
      </section>
    </main>
  );
}

export default App;
