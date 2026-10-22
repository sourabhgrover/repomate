import type { Citation } from "../api/client";

export interface CitationListProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationListProps): JSX.Element {
  if (citations.length === 0) {
    return <></>;
  }

  return (
    <div className="citation-list">
      <p className="citation-header">📎 Sources</p>
      <div className="citation-items">
        {citations.map((citation, index) => (
          <div key={index} className="citation-item">
            {/* File path + line range badge */}
            <span className="citation-badge">
              <span className="citation-icon">📄</span>
              <code className="citation-path">
                {citation.file_path}:L{citation.line_start}–L{citation.line_end}
              </code>
            </span>

            {/* Chunk type label */}
            <span className={`citation-type citation-type--${citation.chunk_type}`}>
              {citation.chunk_type}
            </span>

            {/* Symbol names (function/class names) */}
            {citation.symbols.length > 0 && (
              <span className="citation-symbols">
                {citation.symbols.map((symbol, i) => (
                  <code key={i} className="citation-symbol">
                    {symbol}
                  </code>
                ))}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}