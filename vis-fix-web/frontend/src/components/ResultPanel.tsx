import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import CodeBlock from "./CodeBlock";

export default function ResultPanel({ markdown }: { markdown: string }) {
  return (
    <div className="answer">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{ pre: CodeBlock }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
