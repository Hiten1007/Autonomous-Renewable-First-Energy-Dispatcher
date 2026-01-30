export default function Header({ meta }) {
  return (
    <header className="dashboard-header reveal">
      <div>
        <h1>Carbon Dispatch</h1>
        <p className="subtitle">
          Region {meta.region} · {meta.window_minutes} min window
        </p>
      </div>

      <time className="mono">{meta.timestamp}</time>
    </header>
  );
}
