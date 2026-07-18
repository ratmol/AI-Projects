export type Phase = "idle" | "running" | "done" | "error";

/* A real statusline (tmux/vim), not decorative window chrome: every field
   reports actual state. */
const PHASE: Record<Phase, { text: string; dot: string }> = {
  idle: { text: "idle", dot: "bg-muted" },
  running: { text: "running", dot: "bg-signal" },
  done: { text: "exit 0", dot: "bg-ok" },
  error: { text: "exit 1", dot: "bg-alert" },
};

export default function StatusLine({ phase }: { phase: Phase }) {
  const p = PHASE[phase];
  return (
    <div className="flex items-center gap-4 border-b border-line px-4 py-2 font-mono text-[10px] text-muted">
      <span className="text-text">visfix</span>
      <span className="hidden sm:inline">google/gemini-3-flash</span>
      <span className="ml-auto flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${p.dot}`} aria-hidden />
        <span aria-live="polite">{p.text}</span>
      </span>
      <span className="hidden border-l border-line pl-4 sm:inline">5 req / 15 min</span>
    </div>
  );
}
