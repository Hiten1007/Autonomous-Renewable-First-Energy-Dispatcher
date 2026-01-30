export default function TimeScrubber({ value, onChange }) {
  return (
    <div className="scrubber">
      <input
        type="range"
        min="0"
        max="11"
        value={value}
        onChange={e => onChange(+e.target.value)}
      />
      <span className="mono">Window −{(11 - value) * 30} min</span>
    </div>
  );
}
