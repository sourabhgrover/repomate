import { useState, useRef } from "react";
import { startIndex, getStatus } from "./api/client";
import type { StatusResponse } from "./api/client";
import { ChatWindow } from "./components/ChatWindow";

export function App(): JSX.Element {
  const [owner, setOwner] = useState("");
  const [repoName, setRepoName] = useState("");
  const [ref, setRef] = useState("main");

  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStatus, setIndexStatus] = useState<StatusResponse | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [activeRepoId, setActiveRepoId] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }

  async function handleIndex() {
    if (!owner.trim() || !repoName.trim() || isIndexing) return;

    setIsIndexing(true);
    setIndexError(null);
    setIndexStatus(null);
    setActiveRepoId(null);

    try {
      // 1. Kick off the background ingestion job
      const { job_id } = await startIndex({
        owner: owner.trim(),
        name: repoName.trim(),
        ref: ref.trim() || "main",
      });

      // 2. Poll GET /status every 3 seconds until completed or failed
      pollingRef.current = setInterval(async () => {
        try {
          const status = await getStatus(job_id);
          setIndexStatus(status);

          if (status.status === "completed") {
            stopPolling();
            setIsIndexing(false);
            setActiveRepoId(`${owner.trim()}/${repoName.trim()}`);
          } else if (status.status === "failed") {
            stopPolling();
            setIsIndexing(false);
            setIndexError(status.error_message || "Ingestion failed.");
          }
        } catch (err: any) {
          stopPolling();
          setIsIndexing(false);
          setIndexError(err.message || "Failed to poll job status.");
        }
      }, 3000);
    } catch (err: any) {
      setIsIndexing(false);
      setIndexError(err.message || "Failed to start indexing.");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleIndex();
  }

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app-header">
        <h1 className="app-title">🤖 RepoMate-Lite</h1>
        <p className="app-subtitle">
          Ask natural-language questions about any GitHub repository.
        </p>
      </header>

      {/* ── Repository Indexing Panel ── */}
      <section className="index-panel">
        <div className="index-inputs">
          <input
            className="index-input"
            type="text"
            placeholder="Owner (e.g. pallets)"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isIndexing}
          />
          <input
            className="index-input"
            type="text"
            placeholder="Repository (e.g. click)"
            value={repoName}
            onChange={(e) => setRepoName(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isIndexing}
          />
          <input
            className="index-input index-input--ref"
            type="text"
            placeholder="Branch (default: main)"
            value={ref}
            onChange={(e) => setRef(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isIndexing}
          />
          <button
            className="index-btn"
            onClick={handleIndex}
            disabled={isIndexing || !owner.trim() || !repoName.trim()}
          >
            {isIndexing ? "⏳ Indexing..." : "⚡ Index Repo"}
          </button>
        </div>

        {/* ── Status Bar ── */}
        {indexStatus && (
          <div className={`index-status index-status--${indexStatus.status}`}>
            {indexStatus.status === "queued" && "🕐 Job queued..."}
            {indexStatus.status === "running" &&
              `⚙️ Indexing... ${indexStatus.files_processed} files processed, ${indexStatus.chunks_created} chunks created`}
            {indexStatus.status === "completed" &&
              `✅ Done! ${indexStatus.files_processed} files, ${indexStatus.chunks_created} chunks indexed.`}
            {indexStatus.status === "failed" && `❌ Failed: ${indexStatus.error_message}`}
          </div>
        )}

        {indexError && (
          <div className="index-status index-status--failed">
            ❌ {indexError}
          </div>
        )}
      </section>

      {/* ── Chat Window (shown only after successful indexing) ── */}
      {activeRepoId ? (
        <main className="chat-section">
          <p className="chat-repo-label">
            💬 Chatting about: <strong>{activeRepoId}</strong>
          </p>
          <ChatWindow repoId={activeRepoId} />
        </main>
      ) : (
        <main className="app-placeholder">
          <p>👆 Index a repository above to start asking questions!</p>
        </main>
      )}
    </div>
  );
}