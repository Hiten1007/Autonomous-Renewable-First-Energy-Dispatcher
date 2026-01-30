import Panel from "../ui/Panel";

export default function CarbonBars({ index, data }) {
  const c = data.carbon;

  const max = Math.max(
    c.baseline_kgco2,
    c.actual_kgco2,
    1
  );

  return (
    <Panel title="Carbon Comparison" delay={index * 120}>
      <div className="carbon-bars-wrap">
        <CarbonBar
          label="Baseline"
          value={c.baseline_kgco2}
          max={max}
        />
        <CarbonBar
          label="Actual"
          value={c.actual_kgco2}
          max={max}
          green
        />
      </div>
    </Panel>
  );
}

function CarbonBar({ label, value, max, green }) {
  const pct = (value / max) * 100;

  return (
    <div className="bar-col">
      <div className="bar-track">
        <div
          className={`bar-fill ${green ? "green-bar" : ""}`}
          style={{ height: `${pct}%` }}
        />
      </div>

      <span>{label}</span>
      <small className="mono">{value}</small>
    </div>
  );
}
