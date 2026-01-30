export default function HistoryRibbon({ active, setActive }) {
  return (
    <div className="history-ribbon">
      {Array.from({ length: 12 }).map((_, i) => (
        <button
          key={i}
          className={active === i ? "active" : ""}
          onClick={() => setActive(i)}
        >
          −{i * 30}m
        </button>
      ))}
    </div>
  );
}
