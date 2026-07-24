import { useEffect, useRef, useState } from "react";
import DropZone from "./components/DropZone";
import HowItWorks from "./components/HowItWorks";
import ResultPanel from "./components/ResultPanel";
import RunStatus from "./components/RunStatus";
import StatusLine, { type Phase } from "./components/StatusLine";
import Trace, { type Step } from "./components/Trace";
import { analyze } from "./lib/sse";

const EXAMPLES = [
  { file: "python-traceback.png", detail: "cannot import name 'BaseSettings'" },
  { file: "npm-eresolve.png", detail: "ERESOLVE peer dependency conflict" },
  { file: "cors-console.png", detail: "blocked by CORS policy" },
];

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [steps, setSteps] = useState<Step[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [answer, setAnswer] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const startRef = useRef(0);
  const writingRef = useRef(false);
  const resultsRef = useRef<HTMLElement>(null);

  // Keeps the elapsed readout and the open step honest while a run is going.
  useEffect(() => {
    if (phase !== "running") return;
    const id = setInterval(() => setElapsed(performance.now() - startRef.current), 80);
    return () => clearInterval(id);
  }, [phase]);

  // Part of the reveal: once a run starts, bring the results into view.
  useEffect(() => {
    if (phase !== "running" || !resultsRef.current) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    resultsRef.current.scrollIntoView({
      behavior: reduce ? "auto" : "smooth",
      block: "start",
    });
  }, [phase]);

  const selectFile = (f: File) => {
    setFile(f);
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(f);
    });
  };

  /** Close the open step's duration and start a new one. */
  const push = (kind: Step["kind"], label: string) => {
    const at = performance.now() - startRef.current;
    setSteps((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.dur === null) next[next.length - 1] = { ...last, dur: at - last.at };
      return [...next, { at, dur: null, kind, label }];
    });
  };

  const closeLast = () => {
    const at = performance.now() - startRef.current;
    setElapsed(at);
    setSteps((prev) =>
      prev.map((s, i) => (i === prev.length - 1 && s.dur === null ? { ...s, dur: at - s.at } : s)),
    );
  };

  const run = async () => {
    if (!file || phase === "running") return;
    startRef.current = performance.now();
    setPhase("running");
    setAnswer("");
    setSteps([]);
    setElapsed(0);
    setNote(null);
    writingRef.current = false;
    push("work", "uploading and compressing");

    let finished = false;
    try {
      for await (const ev of analyze(file, prompt)) {
        switch (ev.type) {
          case "compressed":
            setNote(`${ev.original_kb} KB to ${ev.final_kb} KB, ${ev.width}x${ev.height}`);
            // show the exact image the model receives, not the local original
            setPreview((old) => {
              if (old) URL.revokeObjectURL(old);
              return ev.data_url;
            });
            // stop the clock here so this step measures upload and compression
            // only, rather than absorbing the wait for the model
            closeLast();
            break;
          case "status":
            push("work", "reading the screenshot");
            break;
          case "tool":
            push("search", `searching the web for ${ev.query}`);
            break;
          case "token":
            if (!writingRef.current) {
              writingRef.current = true;
              push("work", "writing the fix");
            }
            setAnswer((a) => a + ev.text);
            break;
          case "done":
            finished = true;
            closeLast();
            setPhase("done");
            break;
          case "error":
            finished = true;
            push("error", ev.message);
            closeLast();
            setPhase("error");
            break;
        }
      }
      if (!finished) {
        push("error", "connection lost before the answer finished");
        closeLast();
        setPhase("error");
      }
    } catch (err) {
      push("error", err instanceof Error ? err.message : "request failed");
      closeLast();
      setPhase("error");
    }
  };

  const loadExample = async (name: string) => {
    const res = await fetch(`/examples/${name}`);
    selectFile(new File([await res.blob()], name, { type: "image/png" }));
  };

  const copyAll = async () => {
    await navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  // Ctrl/Cmd+Enter runs from anywhere, including the context box. A ref keeps
  // the listener pointed at the current closure without rebinding every render.
  const runRef = useRef(run);
  runRef.current = run;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        void runRef.current();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const busy = phase === "running";
  const stage = busy
    ? (steps[steps.length - 1]?.label ?? "starting")
    : phase === "error"
      ? "run failed"
      : "done";

  return (
    <div className="min-h-screen">
      <StatusLine phase={phase} />

      <div className="mx-auto max-w-3xl px-6 py-16">
        <header className="mb-12">
          <h1 className="display text-5xl text-text sm:text-6xl">vis-fix</h1>
          <p className="mt-6 max-w-xl font-display text-base leading-relaxed text-muted">
            Paste a screenshot of an error. The agent reads it, checks current documentation when a
            version is involved, and returns a fix, with its work shown.
          </p>
        </header>

        <div className="space-y-6">
          <DropZone preview={preview} onSelect={selectFile} disabled={busy} />

          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            maxLength={2000}
            placeholder="optional: what were you doing when it broke?"
            className="h-20 w-full resize-none rounded-instrument border border-line bg-raised px-3 py-2 font-mono text-[12px] text-text placeholder:text-muted focus:border-muted focus:outline-none"
          />

          <button
            type="button"
            onClick={run}
            disabled={!file || busy}
            className="w-full rounded-instrument border border-signal bg-signal px-4 py-3 font-mono text-[12px] font-medium text-surface transition-colors duration-100 hover:bg-transparent hover:text-signal disabled:cursor-not-allowed disabled:border-line disabled:bg-transparent disabled:text-muted"
          >
            {busy ? "analyzing" : "analyze"}
            {!busy && (
              <span className="ml-2 opacity-60">
                {navigator.platform.includes("Mac") ? "cmd" : "ctrl"}+enter
              </span>
            )}
          </button>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-2 pt-2">
            <span className="text-[10px] uppercase tracking-[0.09em] text-muted">
              or try one
            </span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.file}
                type="button"
                onClick={() => loadExample(ex.file)}
                disabled={busy}
                title={ex.file}
                className="rounded-instrument border border-line px-2.5 py-1.5 font-mono text-[10px] text-muted transition-colors duration-100 hover:border-muted hover:text-text disabled:opacity-40"
              >
                {ex.detail}
              </button>
            ))}
          </div>

          <p className="border-t border-line pt-4 font-mono text-[10px] leading-relaxed text-muted">
            the screenshot is compressed in memory
            {note ? ` (${note})` : ""}, sent once to the model through OpenRouter, and never
            written to disk on this server.
          </p>
        </div>

        {/* min-h reserves scroll room, so the reveal lands where it should
            instead of being clamped by a page that is still short */}
        {phase !== "idle" && (
          <section
            ref={resultsRef}
            className="reveal mt-16 min-h-[calc(100vh-5rem)] scroll-mt-6"
            aria-label="result"
          >
            <div className="rounded-instrument border border-line bg-raised p-6">
              <RunStatus stage={stage} elapsed={elapsed} running={busy} />

              {answer && (
                <div className="mt-6 border-t border-line pt-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-[10px] uppercase tracking-[0.09em] text-muted">
                      diagnosis
                    </h2>
                    <button
                      type="button"
                      onClick={copyAll}
                      className="font-mono text-[10px] text-muted transition-colors duration-100 hover:text-signal"
                    >
                      {copied ? "copied" : "copy all"}
                    </button>
                  </div>
                  <ResultPanel markdown={answer} />
                </div>
              )}

              {steps.length > 0 && (
                <div className="mt-6">
                  <Trace steps={steps} elapsed={elapsed} running={busy} />
                </div>
              )}
            </div>
          </section>
        )}

        {/* Explainer sits below the fold on idle. Once a run exists the result
            is the point, so it stays out of the way down here either way. */}
        <HowItWorks />

        <footer className="mt-16 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-line pt-6 font-mono text-[10px] text-muted">
          <span>routed via OpenRouter</span>
          <span className="text-line">/</span>
          <span>web search by Tavily</span>
          <span className="text-line">/</span>
          <span>5 requests per 15 minutes</span>
          <span className="text-line">/</span>
          <span>5 MB max</span>
          <a
            href="https://github.com/ratmol/AI-Projects/tree/main/vis-fix-web"
            target="_blank"
            rel="noreferrer"
            className="ml-auto underline decoration-line underline-offset-4 transition-colors duration-100 hover:text-text"
          >
            source
          </a>
        </footer>
      </div>
    </div>
  );
}
