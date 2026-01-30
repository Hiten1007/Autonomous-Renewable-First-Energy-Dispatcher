import Panel from "../ui/Panel";
import { useDispatchHistory } from "../../hooks/useDispatchHistory";

export default function GridIntensityStrip() {
  const { data: decisionHistory } =
    useDispatchHistory();

  if (!decisionHistory.length) return null;

  const max = Math.max(
    ...decisionHistory.map(
      d => d.carbon.grid_intensity_gco2_per_kwh
    )
  );


  return (
    <Panel title="Grid Carbon Intensity">
      <div className="horizon-strip">
        {decisionHistory.map((d, i) => (
          <div
            key={i}
            className="horizon-bar"
            style={{
              height: `${
                (d.carbon.grid_intensity_gco2_per_kwh /
                  max) *
                100
              }%`
            }}
          />
        ))}
      </div>
    </Panel>
  );
}
