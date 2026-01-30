export default function BatteryGlyph({ before, after }) {
  const pct = Math.min(100, (after / 40) * 100);

  return (
    <div className="battery">
      <div className="battery-shell">
        <div
          className="battery-fill"
          style={{ height: `${pct}%` }}
        />
      </div>

      <span className="mono">{after} MWh</span>
    </div>
  );
}
