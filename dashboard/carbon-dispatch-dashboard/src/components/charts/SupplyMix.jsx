import Panel from "../ui/Panel";

export default function SupplyMix({ index, data }) {
  const mix = data.supply_mix;

  const total =
    mix.local_renewables_mwh + mix.grid_import_mwh || 1;

  const rePct =
    (mix.local_renewables_mwh / total) * 100;

  return (
    <Panel title="Supply Origin" delay={index * 120}>
      <div className="ring-meter">
        <svg viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="76" className="ring-bg" />

          <circle
            cx="100"
            cy="100"
            r="76"
            className="ring thick"
            strokeDasharray={`${(rePct / 100) * 480} 480`}
          />
        </svg>

        <div className="ring-center mono">
          {mix.effective_re_percent}%
          <span>Renewable</span>
        </div>
      </div>
    </Panel>
  );
}
