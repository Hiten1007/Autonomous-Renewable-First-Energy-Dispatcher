import Panel from "../ui/Panel";

export default function ForecastVsActual({ data, index }) {
  // Use optional chaining and defaults
  const forecast = data?.forecast?.solar_mwh ?? 50; // default 50 MWh
  const actual = data?.solar?.generated_mwh ?? 48;  // default 48 MWh

  // fake mini profile inside the window
  const forecastSeries = [
    forecast * 0.85,
    forecast * 0.95,
    forecast,
    forecast * 0.92,
    forecast * 0.98
  ];

  const actualSeries = [
    actual * 0.7,
    actual * 0.9,
    actual * 1.05,
    actual * 0.97,
    actual
  ];

  const max = Math.max(...forecastSeries, ...actualSeries) * 1.15;

  const scaleY = v => 140 - (v / max) * 110;
  const scaleX = i => 30 + i * 60;

  return (
    <Panel title="Solar Forecast vs Actual" delay={index * 120}>
      <svg viewBox="0 0 320 170" className="linechart">
        {/* axes */}
        <line x1="30" y1="140" x2="300" y2="140" />
        <line x1="30" y1="20" x2="30" y2="140" />

        {/* forecast */}
        <polyline
          points={forecastSeries
            .map((v, i) => `${scaleX(i)},${scaleY(v)}`)
            .join(" ")}
          className="forecast-line"
        />

        {/* actual */}
        <polyline
          points={actualSeries
            .map((v, i) => `${scaleX(i)},${scaleY(v)}`)
            .join(" ")}
          className="actual-line"
        />

        {/* dots */}
        {actualSeries.map((v, i) => (
          <circle
            key={i}
            cx={scaleX(i)}
            cy={scaleY(v)}
            r="3"
            className="actual-dot"
          />
        ))}
      </svg>

      <div className="radial-legend">
        <span>Forecast · {forecast} MWh</span>
        <span>Actual · {actual} MWh</span>
      </div>
    </Panel>
  );
}
