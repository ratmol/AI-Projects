import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  preview: string | null;
  onSelect: (f: File) => void;
  disabled: boolean;
};

export default function DropZone({ preview, onSelect, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const pick = useCallback(
    (f: File | null | undefined) => {
      if (f && f.type.startsWith("image/")) onSelect(f);
    },
    [onSelect],
  );

  // Paste-from-clipboard anywhere on the page — devs screenshot to clipboard.
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      if (disabled) return;
      for (const item of e.clipboardData?.items ?? []) {
        if (item.type.startsWith("image/")) {
          e.preventDefault();
          pick(item.getAsFile());
          return;
        }
      }
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [pick, disabled]);

  return (
    <>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (!disabled) pick(e.dataTransfer.files[0]);
        }}
        className={`block w-full rounded-instrument border border-dashed p-3 text-left transition-colors duration-100 disabled:opacity-50 ${
          dragOver ? "border-signal bg-raised" : "border-line bg-raised hover:border-muted"
        }`}
      >
        {preview ? (
          <span className="block space-y-2">
            {/* data marks stay sharp — no radius on the image */}
            <img src={preview} alt="selected screenshot" className="w-full border border-line" />
            <span className="block font-mono text-[10px] text-muted">
              click, drop or paste to replace
            </span>
          </span>
        ) : (
          <span className="block space-y-1.5 py-12 text-center">
            <span className="block font-mono text-[12px] text-text">
              drop a screenshot of the error
            </span>
            <span className="block font-mono text-[10px] text-muted">
              paste works too — <kbd className="text-signal">ctrl+v</kbd>
            </span>
          </span>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => pick(e.target.files?.[0])}
      />
    </>
  );
}
