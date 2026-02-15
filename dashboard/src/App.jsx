import React, { useEffect, useMemo, useState } from "react";

const DEFAULT_LIMIT = 100;

function useDashboardData() {
  const [records, setRecords] = useState([]);
  const [status, setStatus] = useState("idle");
    const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = async () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
    console.log("API Base URL:", baseUrl); // Debugging
    const apiKey = import.meta.env.VITE_DASHBOARD_API_KEY || "";
    const url = `${baseUrl}/dashboard/records?limit=${DEFAULT_LIMIT}`;

    setStatus("loading");
    setError("");

    try {
      const response = await fetch(url, {
        headers: {
          "x-api-key": apiKey
        }
      });

      if (!response.ok) {
        throw new Error(`API error ${response.status}`);
      }

      const payload = await response.json();
      const items = Array.isArray(payload.records) ? payload.records : [];
      setRecords(items);
      setLastUpdated(new Date());
      setStatus("ready");
    } catch (err) {
      setStatus("error");
      setError(err.message || "Failed to load data");
    }
  };

  return { records, status, error, lastUpdated, reload: load };
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function IntelligenceList({ title, items }) {
  return (
    <div className="intel-block">
      <div className="intel-title">{title}</div>
      {items.length === 0 ? (
        <div className="intel-empty">No entries</div>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function App() {
  const { records, status, error, lastUpdated, reload } = useDashboardData();
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    reload();
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return records;
    const needle = query.toLowerCase();
    return records.filter((record) => {
      const text = JSON.stringify(record).toLowerCase();
      return text.includes(needle);
    });
  }, [records, query]);

  const selected = filtered.find((item) => item.sessionId === selectedId) || filtered[0];

  const totalScams = records.filter((item) => item.scamDetected).length;
  const totalMessages = records.reduce((sum, item) => sum + (item.totalMessagesExchanged || 0), 0);

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Live Telegram Extractor</p>
          <h1>Scam Intelligence Dashboard</h1>
          <p className="subtitle">
            Streamed final sessions with extracted UPI, phone, and link signals.
          </p>
        </div>
        <div className="hero-actions">
          <button className="ghost" onClick={reload} disabled={status === "loading"}>
            {status === "loading" ? "Refreshing" : "Refresh"}
          </button>
          <div className="timestamp">
            Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "-"}
          </div>
        </div>
      </header>

      <section className="stats">
        <StatCard label="Total Sessions" value={records.length} />
        <StatCard label="Scams Detected" value={totalScams} />
        <StatCard label="Total Messages" value={totalMessages} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Sessions</h2>
            <p className="panel-subtitle">
              Filter by phone numbers, UPI IDs, or any keyword.
            </p>
          </div>
          <input
            className="search"
            placeholder="Search everything"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        {status === "error" ? (
          <div className="state error">{error}</div>
        ) : null}
        {status === "loading" ? (
          <div className="state">Loading dashboard data...</div>
        ) : null}

        <div className="grid">
          <div className="session-list">
            {filtered.map((item) => (
              <button
                key={item.sessionId}
                className={`session-item ${selected?.sessionId === item.sessionId ? "active" : ""}`}
                onClick={() => setSelectedId(item.sessionId)}
              >
                <div>
                  <div className="session-id">{item.sessionId}</div>
                  <div className="session-meta">
                    Updated {formatDate(item.updatedAt)}
                  </div>
                </div>
                <span className={`badge ${item.scamDetected ? "danger" : "muted"}`}>
                  {item.scamDetected ? "Scam" : "Clean"}
                </span>
              </button>
            ))}
          </div>

          {selected ? (
            <div className="session-detail">
              <div className="detail-header">
                <div>
                  <h3>{selected.sessionId}</h3>
                  <div className="detail-meta">
                    Created {formatDate(selected.createdAt)} | Updated {formatDate(selected.updatedAt)}
                  </div>
                </div>
                <div className="detail-count">
                  {selected.totalMessagesExchanged} messages
                </div>
              </div>

              <div className="intel-grid">
                <IntelligenceList
                  title="UPI IDs"
                  items={selected.extractedIntelligence?.upiIds || []}
                />
                <IntelligenceList
                  title="Bank Accounts"
                  items={selected.extractedIntelligence?.bankAccounts || []}
                />
                <IntelligenceList
                  title="Phone Numbers"
                  items={selected.extractedIntelligence?.phoneNumbers || []}
                />
                <IntelligenceList
                  title="Phishing Links"
                  items={selected.extractedIntelligence?.phishingLinks || []}
                />
                <IntelligenceList
                  title="Keywords"
                  items={selected.extractedIntelligence?.suspiciousKeywords || []}
                />
              </div>

              <div className="messages">
                <div className="intel-title">Raw Messages</div>
                <div className="message-stream">
                  {(selected.rawMessages || []).map((message, index) => (
                    <div key={`${message.timestamp}-${index}`} className="message">
                      <div className="message-meta">
                        <span className="sender">{message.sender}</span>
                        <span>{formatDate(message.timestamp * 1000)}</span>
                      </div>
                      <div className="message-text">{message.text}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="session-detail empty">No sessions to display.</div>
          )}
        </div>
      </section>
    </div>
  );
}
