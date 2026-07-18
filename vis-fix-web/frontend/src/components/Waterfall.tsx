export type Step = {
  at: number; // ms since run start
  dur: number | null; // null while still running
  kind: "work" | "search" | "ok" | "error";
  label: string;
};

/* The one accent carries normal work; external I/O reads lighter; pass/fail
   use the two state tokens. No colour is decorative here — each encodes data. */
const BAR: Record<Step["kind"], string> = {
  work: "bg-signal",
  search: "bg-signal/45",
  ok: "bg-ok",
  error: "bg-alert",
};

const secs = (ms: number) => `${(ms / 1000).toFixed(2)}s`;

/**
 * THE SIGNATURE MOMENT.
 *
 * The agent pipeline drawn as a timing waterfall, the way a network panel or a
 * logic analyser draws one: every step positioned by when it started and sized
 * by how long it took, from real measurements. It is the only animated element
 * in the UI, and everything else is deliberately still so this reads.
 */
export default function Waterfall({
  steps,
  elapsed,
  running,
}: {
  steps: Step[];
  elapsed: number;
  running: boolean;
}) {
  // Never divide by zero, and keep early bars from filling the whole track.
  const total = Math.max(elapsed, 400);

  return (
    <section className="border border-line" aria-label="pipeline trace">
      <header className="flex items-baseline justify-between border-b border-line px-3 py-2">
        <h2 className="label">trace</h2>
        <span className="font-mono text-[10px] text-muted" aria-live="polite">
          {secs(elapsed)}
        </span>
      </header>

      <div className="divide-y divide-line">
        {steps.map((s, i) => {
          const dur = s.dur ?? elapsed - s.at;
          return (
            <div key={i} className="row-in grid grid-cols-[3.25rem_1fr] gap-3 px-3 py-2 sm:grid-cols-[3.25rem_11rem_1fr_3rem]">
              <span className="font-mono text-[10px] leading-5 text-muted tabular-nums">
                +{secs(s.at)}
              </span>

              <span
                className={`truncate font-mono text-[11px] leading-5 ${
                  s.kind === "error" ? "text-alert" : "text-text"
                }`}
                title={s.label}
              >
                {s.label}
              </span>

              {/* measurement track: faint gridlines + the bar itself */}
              <div className="relative col-span-2 h-5 sm:col-span-1">
                <div className="absolute inset-y-0 left-0 right-0 flex justify-between" aria-hidden>
                  {[0, 1, 2, 3, 4].map((n) => (
                    <span key={n} className="w-px bg-line" />
                  ))}
                </div>
                <div
                  className={`absolute top-1/2 h-1.5 -translate-y-1/2 ${BAR[s.kind]} ${
                    s.dur === null && running ? "measuring" : ""
                  }`}
                  style={{
                    left: `${(s.at / total) * 100}%`,
                    width: `max(2px, ${(Math.max(dur, 0) / total) * 100}%)`,
                  }}
                />
              </div>

              <span className="hidden text-right font-mono text-[10px] leading-5 text-muted tabular-nums sm:block">
                {s.dur === null && running ? "" : secs(Math.max(dur, 0))}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
