import Panel from "../ui/Panel";

export default function SolarFlow({ index, data }) {
  const s = data.solar;

  const values = [
    { label: "Used", value: s.used_directly_mwh },
    { label: "Stored", value: s.stored_mwh },
    { label: "Curtailed", value: s.curtailed_mwh }
  ];

  const total = values.reduce((a, b) => a + b.value, 0);

  let acc = 0;

  return (
    <Panel title="Solar Allocation" delay={index * 120}>
      <svg viewBox="0 0 200 200" className="pie">
        {values.map((slice, i) => {
          const start = (acc / total) * 2 * Math.PI;
          acc += slice.value;
          const end = (acc / total) * 2 * Math.PI;

          return (
            <PieSlice
              key={i}
              start={start}
              end={end}
              index={i}
            />
          );
        })}
      </svg>

      <div className="radial-legend">
        {values.map(v => (
          <span key={v.label}>
            {v.label} · {v.value} MWh
          </span>
        ))}
      </div>
    </Panel>
  );
}

function PieSlice({ start, end, index }) {
  const r = 80;
  const cx = 100;
  const cy = 100;

  const x1 = cx + r * Math.cos(start);
  const y1 = cy + r * Math.sin(start);

  const x2 = cx + r * Math.cos(end);
  const y2 = cy + r * Math.sin(end);

  const largeArc = end - start > Math.PI ? 1 : 0;

  return (
    <path
      d={`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`}
      className={`pie-slice slice-${index}`}
    />
  );
}
