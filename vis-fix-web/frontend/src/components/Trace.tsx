export type Step = {
  at: number; // ms since run start
  dur: number | null; // null while still running
  kind: "work" | "search" | "error";
  label: string;
};

const secs = (ms: number) => `${(ms / 1000).toFixed(2)}s`;

/**
 * The agent's steps as a plain vertical list on a rail, the way a CI job
 * reports itself. Secondary to the diagnosis on purpose: it answers "what did
 * it do" without competing with the answer for attention.
 */
export default function Trace({
  steps,
  elapsed,
  running,
}: {
  steps: Step[];
  elapsed: number;
  running: boolean;
}) {
  return (
    <details open className="group border-t border-line pt-4">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-[10px] uppercase tracking-[0.09em] text-muted hover:text-text">
        <span className="transition-transform duration-100 group-open:rotate-90">›</span>
        trace
        <span className="text-line">/</span>
        {steps.length} step{steps.length === 1 ? "" : "s"}
        <span className="ml-auto tabular-nums normal-case tracking-normal">{secs(elapsed)}</span>
      </summary>

      <ol className="mt-3 ml-[3px] border-l border-line">
        {steps.map((s, i) => {
          const open = s.dur === null && running;
          const dur = s.dur ?? elapsed - s.at;
          return (
            <li key={i} className="step-in relative flex items-baseline gap-3 py-1.5 pl-4">
              <span
                aria-hidden
                className={`absolute -left-[3px] top-[9px] h-1.5 w-1.5 rounded-full ${
                  s.kind === "error" ? "bg-alert" : open ? "bg-signal pulse" : "bg-muted"
                }`}
              />
              <span
                className={`min-w-0 flex-1 truncate text-[11px] ${
                  s.kind === "error" ? "text-alert" : open ? "text-text" : "text-muted"
                }`}
                title={s.label}
              >
                {s.label}
              </span>
              <span className="shrink-0 text-[10px] tabular-nums text-muted">
                {open ? "" : secs(Math.max(dur, 0))}
              </span>
            </li>
          );
        })}
      </ol>
    </details>
  );
}
