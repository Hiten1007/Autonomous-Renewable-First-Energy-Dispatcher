export default function MetricCard({ label, value, index }) {
  return (
    <div
      className="metric-card reveal"
      style={{ animationDelay: `${index * 120}ms` }}
    >
      <p className="metric-label">{label}</p>
      <h3 className="mono">{value}</h3>
    </div>
  );
}
