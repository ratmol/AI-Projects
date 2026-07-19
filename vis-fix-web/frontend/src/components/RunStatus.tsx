const secs = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

/**
 * What the run is doing right now. While the model is still thinking there is
 * nothing to read yet, so this carries the wait: current stage, elapsed time,
 * and an indeterminate bar that stops the moment the first token lands.
 */
export default function RunStatus({
  stage,
  elapsed,
  running,
}: {
  stage: string;
  elapsed: number;
  running: boolean;
}) {
  return (
    <div>
      <div className="flex items-baseline gap-3">
        <span className="text-[12px] text-text" aria-live="polite">
          {stage}
        </span>
        <span className="ml-auto text-[10px] tabular-nums text-muted">{secs(elapsed)}</span>
      </div>
      {running && (
        <div className="mt-2.5 h-px w-full overflow-hidden bg-line">
          <div className="bar-indeterminate h-px w-1/3 bg-signal" />
        </div>
      )}
    </div>
  );
}
