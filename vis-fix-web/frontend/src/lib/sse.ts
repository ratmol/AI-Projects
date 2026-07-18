export type AnalyzeEvent =
  | {
      type: "compressed";
      data_url: string;
      original_kb: number;
      final_kb: number;
      width: number;
      height: number;
    }
  | { type: "status"; stage: string }
  | { type: "tool"; name: string; query: string }
  | { type: "token"; text: string }
  | { type: "done" }
  | { type: "error"; message: string };

/**
 * POST the image and stream back SSE events. EventSource only supports GET,
 * so we parse the text/event-stream body from fetch by hand (~20 lines,
 * cheaper than a dependency).
 */
export async function* analyze(
  file: Blob,
  prompt: string,
  signal?: AbortSignal,
): AsyncGenerator<AnalyzeEvent> {
  const form = new FormData();
  form.append("file", file, "screenshot.png");
  form.append("prompt", prompt);

  const res = await fetch("/api/analyze", { method: "POST", body: form, signal });
  if (!res.ok || !res.body) {
    let detail = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      detail = j.detail ?? j.error ?? detail; // FastAPI uses `detail`, slowapi uses `error`
    } catch {
      /* non-JSON body, keep generic message */
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let sep;
    while ((sep = buf.indexOf("\n\n")) !== -1) {
      const frame = buf.slice(0, sep);
      buf = buf.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7).trim();
        else if (line.startsWith("data: ")) data += line.slice(6);
      }
      if (data) yield { type: event, ...JSON.parse(data) } as AnalyzeEvent;
    }
  }
}
