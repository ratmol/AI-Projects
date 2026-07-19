/* Numbered markers are normally a tell, but this pipeline genuinely runs in
   order and the numbers are what make that readable. See DESIGN.md. */
const STAGES = [
  { n: "01", name: "compress", body: "Resized to fit 1024px and re-encoded, in memory. Vision cost scales with pixels." },
  { n: "02", name: "read", body: "The model reads the error text, the file and line, the framework and the version." },
  { n: "03", name: "search", body: "If a version is involved it searches for current docs rather than trusting training data." },
  { n: "04", name: "fix", body: "Root cause first, then a copy-pasteable fix, with sources when it searched." },
];

export default function HowItWorks() {
  return (
    <section aria-labelledby="how" className="mt-24 border-t border-line pt-10">
      <h2 id="how" className="text-[10px] uppercase tracking-[0.09em] text-muted">
        how it works
      </h2>

      <ol className="mt-6 grid gap-px overflow-hidden rounded-instrument bg-line sm:grid-cols-2 lg:grid-cols-4">
        {STAGES.map((s) => (
          <li key={s.n} className="bg-surface p-4">
            <div className="flex items-baseline gap-2">
              <span className="font-mono text-[10px] text-signal">{s.n}</span>
              <span className="font-mono text-[12px] text-text">{s.name}</span>
            </div>
            <p className="mt-2 font-display text-[13px] leading-relaxed text-muted">{s.body}</p>
          </li>
        ))}
      </ol>

      <p className="mt-6 font-display text-[13px] leading-relaxed text-muted">
        It reads what a developer actually screenshots: terminal output, stack traces, IDE error
        panels, browser consoles, failing CI logs. Cropping to just the error works better than a
        full desktop capture, and the text needs to be legible to you before it will be legible to
        the model.
      </p>
    </section>
  );
}
