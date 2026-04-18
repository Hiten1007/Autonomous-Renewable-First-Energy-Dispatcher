export default function CarbonHero({ data }) {
  return (
    <div className="carbon-hero">
      <h2>Carbon Saved</h2>
      <div className="hero-number mono">
        {data.saved_kgco2.toLocaleString()} kg
      </div>

      <p className="hero-sub">
        Grid Intensity {data.grid_intensity_gco2_per_kwh} gCO₂/kWh
      </p>
    </div>
  );
} 
