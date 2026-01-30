export default function ReasoningCard({ index, variant, data }) {
  const content =
    variant === "summary"
      ? data.summary
      : data.reasoning.why;

  const title = variant === "summary" ? "Summary" : "Reasoning";

  return (
    <section
      className="panel reveal"
      style={{ animationDelay: `${index * 120}ms` }}
    >
      <h3>{title}</h3>

      <p className="narrative-text">{content}</p>

      {variant !== "summary" && (
        <p className="green">Result: {data.reasoning.result}</p>
      )}
    </section>
  );
}
    