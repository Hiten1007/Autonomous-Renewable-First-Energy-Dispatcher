export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">🌿</div>

      <nav>
        <a className="active">Dashboard</a>
        <a>History</a>
        <a>Forecasts</a>
        <a>Policies</a>
      </nav>
    </aside>
  );
}
