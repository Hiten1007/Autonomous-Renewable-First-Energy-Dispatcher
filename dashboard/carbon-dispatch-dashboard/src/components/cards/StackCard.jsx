import { useState } from "react";

export default function StackCard({
  label,
  value,
  detail,
  index
}) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={`stack-card ${open ? "open" : ""}`}
      style={{
        "--offset": `${index * 46}px`
      }}
      onClick={() => setOpen(!open)}
    >
      <div className="stack-core">
        <span className="stack-label">{label}</span>
        <strong className="stack-value">{value}</strong>
      </div>

      <div className="stack-detail">
        {detail}
      </div>
    </div>
  );
}
