export default function Panel({ title, children, delay = 0 }) {
  return (
    <section
      className="panel reveal"
      style={{ animationDelay: `${delay}ms` }}
    >
      <h3>{title}</h3>
      {children}
    </section>
  );
}
