import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const mdStyles = `
  .md-body { color: var(--text); font-size: 15px; line-height: 1.9; }
  .md-body h1 { font-size: 26px; font-weight: 900; color: var(--text); margin: 32px 0 12px; padding-bottom: 10px; border-bottom: 2px solid var(--primary); }
  .md-body h2 { font-size: 20px; font-weight: 800; color: var(--text); margin: 28px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
  .md-body h3 { font-size: 16px; font-weight: 700; color: var(--primary); margin: 22px 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
  .md-body h4 { font-size: 15px; font-weight: 700; color: var(--text); margin: 18px 0 6px; }
  .md-body p { margin: 0 0 14px; color: var(--text-dim); }
  .md-body strong { color: var(--text); font-weight: 700; }
  .md-body em { color: var(--text-dim); font-style: italic; }
  .md-body ul { margin: 0 0 14px 0; padding-left: 0; list-style: none; }
  .md-body ul li { color: var(--text-dim); padding: 4px 0 4px 22px; position: relative; }
  .md-body ul li::before { content: "▸"; color: var(--primary); position: absolute; left: 0; font-size: 13px; top: 5px; }
  .md-body ol { margin: 0 0 14px 0; padding-left: 22px; }
  .md-body ol li { color: var(--text-dim); padding: 4px 0; }
  .md-body blockquote { border-left: 3px solid var(--primary); background: var(--surface2); margin: 16px 0; padding: 12px 18px; border-radius: 0 8px 8px 0; color: var(--text-dim); font-style: italic; }
  .md-body code { background: var(--surface2); color: var(--primary); padding: 2px 7px; border-radius: 5px; font-family: monospace; font-size: 13px; }
  .md-body pre { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; overflow-x: auto; margin: 14px 0; }
  .md-body pre code { background: none; padding: 0; color: var(--text); }
  .md-body hr { border: none; border-top: 1px solid var(--border); margin: 28px 0; }
  .md-body table { width: 100%; border-collapse: collapse; margin: 16px 0; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
  .md-body thead { background: var(--surface2); }
  .md-body th { padding: 11px 14px; text-align: left; font-size: 12px; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.6px; border-bottom: 1px solid var(--border); }
  .md-body td { padding: 10px 14px; color: var(--text-dim); border-bottom: 1px solid var(--border); font-size: 14px; }
  .md-body tr:last-child td { border-bottom: none; }
  .md-body tr:nth-child(even) td { background: rgba(255,255,255,0.015); }
  .md-body a { color: var(--primary); text-decoration: underline; }
`;

function estimateReadTime(text) {
  const words = (text || "").split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
}

export default function ReadingMaterial({ selectedResource, onBack }) {
  const [scrollPct, setScrollPct] = useState(0);
  const [readTime] = useState(() => estimateReadTime(selectedResource?.content_text));

  useEffect(() => {
    const el = document.getElementById("rm-scroll-container");
    if (!el) return;
    const handler = () => {
      const pct = el.scrollTop / (el.scrollHeight - el.clientHeight) * 100;
      setScrollPct(Math.min(100, Math.round(pct)));
    };
    el.addEventListener("scroll", handler);
    return () => el.removeEventListener("scroll", handler);
  }, []);

  if (!selectedResource) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", maxWidth: 860 }}>
      <style>{mdStyles}</style>

      {/* ── Top bar ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
        <button className="btn btn-ghost btn-sm" onClick={onBack}>
          <i className="fas fa-arrow-left"></i> Back to Course
        </button>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 12, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 6 }}>
          <i className="fas fa-clock" style={{ color: "var(--primary)" }}></i>
          {readTime} min read
        </span>
        <span style={{ fontSize: 12, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 6 }}>
          <i className="fas fa-book-open" style={{ color: "var(--primary)" }}></i>
          {scrollPct}% read
        </span>
      </div>

      {/* ── Progress bar ── */}
      <div style={{ height: 3, background: "var(--border)", borderRadius: 99, marginBottom: 28, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${scrollPct}%`, background: "var(--primary)", borderRadius: 99, transition: "width 0.3s ease" }} />
      </div>

      {/* ── Document header card ── */}
      <div style={{ background: "linear-gradient(135deg, var(--surface2) 0%, var(--surface) 100%)", border: "1px solid var(--border)", borderRadius: 14, padding: "24px 28px", marginBottom: 28 }}>
        <span style={{ fontSize: 10, fontWeight: 800, color: "var(--primary)", textTransform: "uppercase", letterSpacing: "1.5px", display: "block", marginBottom: 8 }}>
          {selectedResource.resource_type === "video" ? "📹 Video" : "📄 Training Handbook"}
        </span>
        <h1 style={{ fontSize: 22, fontWeight: 900, color: "var(--text)", margin: "0 0 10px" }}>
          {selectedResource.title}
        </h1>
        {selectedResource.description && (
          <p style={{ fontSize: 14, color: "var(--text-dim)", margin: 0, lineHeight: 1.6 }}>
            {selectedResource.description}
          </p>
        )}
      </div>

      {/* ── Video embed ── */}
      {selectedResource.resource_type === "video" && selectedResource.content_url && (
        <div style={{ position: "relative", paddingBottom: "56.25%", height: 0, borderRadius: 12, overflow: "hidden", background: "var(--surface2)", border: "1px solid var(--border)", marginBottom: 28 }}>
          <iframe
            src={selectedResource.content_url}
            style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", border: "none" }}
            allowFullScreen
          />
        </div>
      )}

      {/* ── External link ── */}
      {selectedResource.content_url && selectedResource.resource_type !== "video" && (
        <div style={{ marginBottom: 20 }}>
          <a href={selectedResource.content_url} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
            <i className="fas fa-external-link-alt"></i> Open External Resource
          </a>
        </div>
      )}

      {/* ── Markdown body ── */}
      {selectedResource.content_text && (
        <div
          id="rm-scroll-container"
          style={{
            flex: 1,
            overflowY: "auto",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: "32px 36px",
            scrollbarWidth: "thin",
            scrollbarColor: "var(--border) transparent",
          }}
        >
          <div className="md-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {selectedResource.content_text}
            </ReactMarkdown>
          </div>
        </div>
      )}

      {/* ── No content fallback ── */}
      {!selectedResource.content_text && !selectedResource.content_url && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-dim)" }}>
          <i className="fas fa-file-slash" style={{ fontSize: 40, marginBottom: 16, display: "block", opacity: 0.4 }}></i>
          <p>No content available for this resource yet.</p>
        </div>
      )}
    </div>
  );
}
