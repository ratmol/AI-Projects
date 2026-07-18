import { useEffect, useRef, useState } from "react";
import DropZone from "./components/DropZone";
import ResultPanel from "./components/ResultPanel";
import StatusLine, { type Phase } from "./components/StatusLine";
import Waterfall, { type Step } from "./components/Waterfall";
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
  const startRef = useRef(0);
  const writingRef = useRef(false);

  // Drives the growing bar of the step currently being measured.
  useEffect(() => {
    if (phase !== "running") return;
    const id = setInterval(() => setElapsed(performance.now() - startRef.current), 80);
    return () => clearInterval(id);
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
    push("work", "upload + compress");

    let finished = false;
    try {
      for await (const ev of analyze(file, prompt)) {
        switch (ev.type) {
          case "compressed":
            setNote(`${ev.original_kb} KB → ${ev.final_kb} KB · ${ev.width}×${ev.height}`);
            // show the exact image the model receives, not the local original
            setPreview((old) => {
              if (old) URL.revokeObjectURL(old);
              return ev.data_url;
            });
            // stop the clock here — this step measured upload + compression only,
            // and must not silently absorb the wait for the model to respond
            closeLast();
            break;
          case "status":
            push("work", "analyze screenshot");
            break;
          case "tool":
            push("search", `search: ${ev.query}`);
            break;
          case "token":
            if (!writingRef.current) {
              writingRef.current = true;
              push("work", "write fix");
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

  const busy = phase === "running";

  return (
    <div className="min-h-screen">
      <StatusLine phase={phase} />

      <div className="mx-auto max-w-6xl px-6 py-16">
        <header className="mb-16 max-w-2xl">
          <h1 className="display text-5xl text-text sm:text-6xl">vis-fix</h1>
          <p className="mt-6 max-w-xl font-display text-base leading-relaxed text-muted">
            Paste a screenshot of an error. The agent reads it, checks current documentation when a
            version is involved, and returns a fix — with its work shown.
          </p>
        </header>

        <main className="grid gap-12 lg:grid-cols-[minmax(0,4fr)_minmax(0,6fr)] lg:gap-16">
          {/* ---------------- input ---------------- */}
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="label">screenshot</h2>
              <DropZone preview={preview} onSelect={selectFile} disabled={busy} />
            </section>

            <section className="space-y-3">
              <h2 className="label">context — optional</h2>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                maxLength={2000}
                placeholder="what were you doing when it broke?"
                className="h-20 w-full resize-none rounded-instrument border border-line bg-raised px-3 py-2 font-mono text-[12px] text-text placeholder:text-muted focus:border-muted focus:outline-none"
              />
            </section>

            <button
              type="button"
              onClick={run}
              disabled={!file || busy}
              className="w-full rounded-instrument border border-signal bg-signal px-4 py-2.5 font-mono text-[12px] font-medium text-surface transition-colors duration-100 hover:bg-transparent hover:text-signal disabled:cursor-not-allowed disabled:border-line disabled:bg-transparent disabled:text-muted"
            >
              {busy ? "analyzing" : "analyze"}
            </button>

            <section className="space-y-3">
              <h2 className="label">or load an example</h2>
              <ul className="divide-y divide-line border border-line">
                {EXAMPLES.map((ex) => (
                  <li key={ex.file}>
                    <button
                      type="button"
                      onClick={() => loadExample(ex.file)}
                      disabled={busy}
                      className="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors duration-100 hover:bg-raised disabled:opacity-40"
                    >
                      <img
                        src={`/examples/${ex.file}`}
                        alt=""
                        className="h-8 w-14 shrink-0 border border-line object-cover object-left-top"
                      />
                      <span className="min-w-0">
                        <span className="block truncate font-mono text-[11px] text-text">
                          {ex.file}
                        </span>
                        <span className="block truncate font-mono text-[10px] text-muted">
                          {ex.detail}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <p className="border-t border-line pt-4 font-mono text-[10px] leading-relaxed text-muted">
              the screenshot is compressed in memory
              {note ? ` (${note})` : ""}, sent once to the model through OpenRouter, and never
              written to disk on this server.
            </p>
          </div>

          {/* ---------------- output ---------------- */}
          <div className="min-w-0 space-y-8">
            {steps.length > 0 && <Waterfall steps={steps} elapsed={elapsed} running={busy} />}

            {answer ? (
              <section className="space-y-3">
                <h2 className="label">diagnosis</h2>
                <div className="border border-line bg-raised p-6">
                  <ResultPanel markdown={answer} />
                </div>
              </section>
            ) : (
              phase === "idle" && (
                <div className="border border-line px-6 py-20 text-center font-mono text-[11px] text-muted">
                  no run yet
                </div>
              )
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
