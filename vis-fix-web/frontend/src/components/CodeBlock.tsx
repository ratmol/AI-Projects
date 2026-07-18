import { isValidElement, useRef, useState, type ReactNode } from "react";

/** Replaces `pre` in the rendered markdown: language label + copy. */
export default function CodeBlock({ children }: { children?: ReactNode }) {
  const ref = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  let lang = "text";
  if (isValidElement(children)) {
    const cls = (children.props as { className?: string }).className ?? "";
    const match = cls.match(/language-([\w-]+)/);
    if (match) lang = match[1];
  }

  const copy = async () => {
    // textContent is the surest way to recover the source from highlighted spans
    await navigator.clipboard.writeText(ref.current?.textContent ?? "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="my-4 border border-line bg-surface">
      <div className="flex items-center justify-between border-b border-line px-3 py-1.5">
        <span className="label">{lang}</span>
        <button
          type="button"
          onClick={copy}
          className="font-mono text-[10px] text-muted transition-colors duration-100 hover:text-signal"
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
      <pre ref={ref} className="overflow-x-auto p-3 font-mono">
        {children}
      </pre>
    </div>
  );
}
