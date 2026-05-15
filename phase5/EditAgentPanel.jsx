/**
 * Phase 5: Edit Agent UI Panel
 * Drop this into phase4/frontend/src/components/
 * 
 * Features:
 * - Free-text edit input → calls /phase5/edit
 * - Version history list with Revert buttons
 * - Shows intent classification result
 */

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8002";

export default function EditAgentPanel({ runDir, currentState, onStateUpdate }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("edit"); // "edit" | "history"

  // Fetch version history
  const fetchHistory = async () => {
    if (!runDir) return;
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/phase5/history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_dir: runDir }),
      });
      const data = await res.json();
      setHistory(data.versions || []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "history") fetchHistory();
  }, [activeTab, runDir]);

  // Apply edit
  const handleEdit = async () => {
    if (!query.trim() || !runDir) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/phase5/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          run_dir: runDir,
          current_state: currentState,
        }),
      });
      const data = await res.json();
      setResult(data);
      if (data.success && data.updated_state && onStateUpdate) {
        onStateUpdate(data.updated_state);
      }
      // Refresh history
      fetchHistory();
    } catch (err) {
      setResult({ success: false, message: `Network error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  // Revert to version
  const handleRevert = async (versionId) => {
    if (!runDir) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/phase5/revert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_dir: runDir, version_id: versionId }),
      });
      const data = await res.json();
      if (data.success) {
        setResult({ success: true, message: `Reverted to version ${versionId}` });
        if (data.restored_state && onStateUpdate) {
          onStateUpdate(data.restored_state);
        }
        fetchHistory();
      }
    } catch (err) {
      setResult({ success: false, message: `Revert error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const targetColor = (target) => {
    const colors = {
      audio: "#3b82f6",
      video_frame: "#8b5cf6",
      video: "#f59e0b",
      script: "#10b981",
    };
    return colors[target] || "#6b7280";
  };

  return (
    <div style={{
      background: "#1e1e2e",
      border: "1px solid #313244",
      borderRadius: 12,
      padding: 20,
      color: "#cdd6f4",
      fontFamily: "Inter, sans-serif",
      maxWidth: 600,
    }}>
      <h3 style={{ margin: "0 0 16px", color: "#cba6f7", fontSize: 16 }}>
        🎬 Edit Agent
      </h3>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["edit", "history"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "6px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              background: activeTab === tab ? "#cba6f7" : "#313244",
              color: activeTab === tab ? "#1e1e2e" : "#cdd6f4",
              fontWeight: activeTab === tab ? 700 : 400,
              textTransform: "capitalize",
            }}
          >
            {tab === "history" ? `📋 History (${history.length})` : "✏️ Edit"}
          </button>
        ))}
      </div>

      {/* Edit Tab */}
      {activeTab === "edit" && (
        <div>
          <div style={{ marginBottom: 12 }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleEdit()}
              placeholder='e.g. "Make the scene darker" or "Change voice to whisper"'
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid #45475a",
                background: "#181825",
                color: "#cdd6f4",
                fontSize: 14,
                boxSizing: "border-box",
              }}
            />
          </div>

          <button
            onClick={handleEdit}
            disabled={loading || !query.trim()}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: 8,
              border: "none",
              background: loading ? "#45475a" : "#cba6f7",
              color: "#1e1e2e",
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: 14,
            }}
          >
            {loading ? "Processing..." : "Apply Edit"}
          </button>

          {/* Result */}
          {result && (
            <div style={{
              marginTop: 16,
              padding: 14,
              borderRadius: 8,
              background: result.success ? "#1e3a2e" : "#3a1e1e",
              border: `1px solid ${result.success ? "#10b981" : "#f38ba8"}`,
            }}>
              <p style={{ margin: "0 0 8px", fontWeight: 600, color: result.success ? "#a6e3a1" : "#f38ba8" }}>
                {result.success ? "✓" : "✗"} {result.message}
              </p>

              {result.intent && (
                <div style={{ fontSize: 12, color: "#a6adc8" }}>
                  <span style={{
                    background: targetColor(result.intent.target),
                    color: "#fff",
                    padding: "2px 8px",
                    borderRadius: 4,
                    marginRight: 8,
                    fontWeight: 600,
                  }}>
                    {result.intent.target}
                  </span>
                  <span>{result.intent.intent}</span>
                  {result.intent.scope && (
                    <span style={{ color: "#89b4fa", marginLeft: 8 }}>@ {result.intent.scope}</span>
                  )}
                  <span style={{ marginLeft: 8, color: "#6c7086" }}>
                    ({Math.round(result.intent.confidence * 100)}% confidence)
                  </span>
                </div>
              )}

              {result.version_before && result.version_after && (
                <p style={{ margin: "8px 0 0", fontSize: 11, color: "#6c7086" }}>
                  Saved: v{result.version_before} → v{result.version_after}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <div>
          {historyLoading && <p style={{ color: "#6c7086" }}>Loading history...</p>}

          {!historyLoading && history.length === 0 && (
            <p style={{ color: "#6c7086", textAlign: "center", padding: 20 }}>
              No versions saved yet. Apply an edit to start versioning.
            </p>
          )}

          {history.slice().reverse().map((v) => (
            <div key={v.id} style={{
              padding: 12,
              marginBottom: 8,
              borderRadius: 8,
              background: "#181825",
              border: "1px solid #313244",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}>
              <div>
                <span style={{
                  background: "#313244",
                  color: "#cba6f7",
                  padding: "2px 8px",
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 700,
                  marginRight: 8,
                }}>
                  {v.version_label}
                </span>
                <span style={{ fontSize: 13 }}>{v.description}</span>
                <div style={{ fontSize: 11, color: "#6c7086", marginTop: 2 }}>
                  {v.created_at?.slice(0, 19)?.replace("T", " ")} •{" "}
                  {v.summary?.scene_count} scenes, {v.summary?.character_count} characters
                </div>
              </div>
              <button
                onClick={() => handleRevert(v.id)}
                style={{
                  padding: "4px 12px",
                  borderRadius: 6,
                  border: "1px solid #45475a",
                  background: "transparent",
                  color: "#f38ba8",
                  cursor: "pointer",
                  fontSize: 12,
                  whiteSpace: "nowrap",
                }}
              >
                ↩ Revert
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
