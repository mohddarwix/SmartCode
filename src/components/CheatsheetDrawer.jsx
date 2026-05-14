import { useEffect } from 'react';
import { BookOpen, X } from 'lucide-react';

/**
 * Slide-in left drawer that renders a per-problem Python syntax cheatsheet.
 * The cheatsheet is markdown with `## Heading` sections and fenced code blocks.
 *
 * - `cheatsheetMd`  : markdown string from `problem.cheatsheet_md`
 * - `open` / `onToggle` : controlled open/close state
 */
export default function CheatsheetDrawer({ cheatsheetMd, open, onToggle }) {
  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onToggle(false); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onToggle]);

  if (!cheatsheetMd) return null;

  const sections = parseCheatsheet(cheatsheetMd);

  return (
    <>
      {/* Trigger tab anchored to the left edge of the workspace */}
      {!open && (
        <button
          onClick={() => onToggle(true)}
          title="Open the Python syntax cheatsheet for this problem"
          className="fixed left-0 top-1/2 -translate-y-1/2 z-40 bg-indigo-600 text-white shadow-lg rounded-r-lg px-2 py-3 hover:bg-indigo-700 transition flex flex-col items-center gap-1"
        >
          <BookOpen className="w-4 h-4" />
          <span className="text-[10px] tracking-wider [writing-mode:vertical-rl] [text-orientation:mixed]">
            CHEATSHEET
          </span>
        </button>
      )}

      {/* Backdrop dim when open (also closes on click) */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30"
          onClick={() => onToggle(false)}
          aria-hidden
        />
      )}

      {/* The drawer itself */}
      <aside
        className={`fixed left-0 top-0 bottom-0 z-40 w-[360px] max-w-[90vw] bg-white shadow-2xl border-r border-gray-200 transition-transform duration-200 ease-out ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b bg-indigo-600 text-white">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            <h2 className="font-semibold text-sm uppercase tracking-wider">Python Cheatsheet</h2>
          </div>
          <button
            onClick={() => onToggle(false)}
            className="text-white/80 hover:text-white"
            aria-label="Close cheatsheet"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto h-[calc(100%-49px)] px-4 py-4 space-y-5">
          {sections.length === 0 ? (
            <p className="text-sm text-gray-500">No cheatsheet for this problem yet.</p>
          ) : (
            sections.map((sec, idx) => (
              <section key={idx}>
                <h3 className="font-bold text-indigo-700 text-sm uppercase tracking-wide mb-2">
                  {sec.heading}
                </h3>
                {sec.blocks.map((b, j) =>
                  b.type === 'code' ? (
                    <pre
                      key={j}
                      className="bg-gray-900 text-green-300 text-xs font-mono p-3 rounded-md overflow-x-auto whitespace-pre"
                    >
                      <code>{b.lines.join('\n')}</code>
                    </pre>
                  ) : (
                    <p key={j} className="text-sm text-gray-700 my-2">{b.text}</p>
                  )
                )}
              </section>
            ))
          )}
          <p className="text-[10px] text-gray-400 pt-2 border-t">
            Reference for this problem only - tailored from the statement.
          </p>
        </div>
      </aside>
    </>
  );
}

/**
 * Minimal markdown parser for the format we generate:
 *   ## Heading
 *   ```python
 *   code...
 *   ```
 * Anything outside a fenced code block under a heading is rendered as
 * a plain paragraph.
 */
function parseCheatsheet(md) {
  const sections = [];
  let current = null;
  let inCode = false;
  let codeLines = [];

  for (const rawLine of md.split('\n')) {
    const line = rawLine.replace(/\r$/, '');

    if (!inCode && /^##\s+/.test(line)) {
      if (current) sections.push(current);
      current = { heading: line.replace(/^##\s+/, '').trim(), blocks: [] };
      continue;
    }
    if (/^```/.test(line)) {
      if (inCode) {
        if (current) current.blocks.push({ type: 'code', lines: codeLines });
        codeLines = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }
    if (line.trim() && current) {
      current.blocks.push({ type: 'text', text: line.trim() });
    }
  }
  if (current) sections.push(current);
  return sections;
}
