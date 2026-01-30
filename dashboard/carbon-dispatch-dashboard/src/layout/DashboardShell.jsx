import { useState } from "react";

import Header from "./Header";
import Sidebar from "./Sidebar";

import CarbonHero from "../components/cards/CarbonHero";
import MetricCard from "../components/cards/MetricCard";
import ReasoningCard from "../components/cards/ReasoningCard";

import SolarFlow from "../components/charts/SolarFlow";
import SupplyMix from "../components/charts/SupplyMix";
import CarbonBars from "../components/charts/CarbonBars";

import TimeScrubber from "../components/ui/TimeScrubber";
import HistoryRibbon from "../components/ui/HistoryRibbon";
import BatteryGlyph from "../components/ui/BatteryGlyph";

import { useDispatchHistory } from "../hooks/useDispatchHistory";


import ForecastVsActual from "../components/charts/ForecastVsActual";
import StackCard from "../components/cards/StackCard";


export default function DashboardShell() {
  const [activeWindow, setActiveWindow] = useState(0);

  const { data: decisionHistory, loading, source } =
    useDispatchHistory();

  if (!decisionHistory.length) return null;

  const safeIndex = Math.min(
    activeWindow,
    decisionHistory.length - 1
  );

  const current = decisionHistory[safeIndex];

  return (
    <div className="dashboard-grid">
      <Sidebar />

      <main className="dashboard-main">

        {/* STATUS BANNER */}
        {source === "local" && (
          <div className="dispatch-status subtle">
            Showing last known dispatch · syncing…
          </div>
        )}

        <Header meta={current.meta} />

        {/* HISTORY + SCRUBBER */}
        <HistoryRibbon
          active={activeWindow}
          setActive={setActiveWindow}
        />
        <TimeScrubber
          value={activeWindow}
          onChange={setActiveWindow}
        />

        {/* HERO */}
        <section className="hero reveal" style={{ animationDelay: "80ms" }}>
          <CarbonHero data={current.carbon} />
        </section>

        {/* METRICS */}
        <section className="kpi-stack">
          {[
            {
              id: "solar",
              label: "Solar Generated",
              value: `${current.solar.generated_mwh} MWh`,
              detail: `Used ${current.solar.used_directly_mwh} · Stored ${current.solar.stored_mwh} · Curtail ${current.solar.curtailed_mwh}`
            },
            {
              id: "battery",
              label: "Battery Δ",
              value: `${current.battery.delta_mwh} MWh`,
              detail: `SOC ${current.battery.soc_before_mwh} → ${current.battery.soc_after_mwh}`
            },
            {
              id: "grid",
              label: "Grid Import",
              value: `${current.supply_mix.grid_import_mwh} MWh`,
              detail: `RE Share ${current.supply_mix.effective_re_percent}%`
            },
            {
              id: "re",
              label: "Renewables",
              value: `${current.supply_mix.effective_re_percent}%`,
              detail: `Local ${current.supply_mix.local_renewables_mwh} MWh`
            }
          ].map((k, i) => (
            <StackCard key={k.id} {...k} index={i} />
          ))}
        </section>

        {/* CHARTS */}
        <section className="chart-grid">
          <SolarFlow index={0} data={current} />
          <SupplyMix index={1} data={current} />
          <CarbonBars index={2} data={current} />
          <ForecastVsActual index={3} data={current} />
        </section>

        {/* NARRATIVE */}
        <section className="narrative-row">
          <ReasoningCard index={0} data={current} />
          <ReasoningCard index={1} variant="summary" data={current} />
        </section>

      </main>
    </div>
  );
}

