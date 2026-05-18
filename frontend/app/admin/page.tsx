"use client";

import { useState } from "react";

interface MRRData {
  date: string;
  mrr_dollars: number;
  active_subscriptions: number;
  paying_users: number;
  new_subs_30d: number;
  churned_30d: number;
  churn_rate_pct: number;
}

interface ResearchTrend {
  id: string;
  project_key: string;
  subreddit_browses: any;
  keyword_searches: any;
  created_at: string;
}

export default function AdminPage() {
  const [key, setKey] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [authError, setAuthError] = useState("");
  const [mrr, setMrr] = useState<MRRData | null>(null);
  const [trends, setTrends] = useState<ResearchTrend[]>([]);
  const [loadingMrr, setLoadingMrr] = useState(false);
  const [loadingTrends, setLoadingTrends] = useState(false);

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim()) return;

    setLoadingMrr(true);
    setLoadingTrends(true);
    setAuthError("");

    const headers = { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };

    fetch("/api/v1/internal/agents/financial", { method: "POST", headers })
      .then((r) => {
        if (r.status === 401) {
          setAuthError("Invalid admin key");
          setLoadingMrr(false);
          setLoadingTrends(false);
          return null;
        }
        return r.json();
      })
      .then((data) => {
        if (data) {
          setMrr(data);
          setAuthenticated(true);
        }
        setLoadingMrr(false);
      });

    fetch("/api/v1/internal/agents/research", { headers })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setTrends(Array.isArray(data) ? data : []);
        setLoadingTrends(false);
      });
  }

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <form onSubmit={handleLogin} className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
          <h1 className="mb-6 text-xl font-bold text-center text-gray-900">Admin Dashboard</h1>
          {authError && <p className="mb-4 text-sm text-red-600 text-center">{authError}</p>}
          <label className="block text-sm font-medium text-gray-700 mb-1">Admin Key</label>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            className="w-full rounded-md border px-3 py-2 mb-4"
            placeholder="Enter INTERNAL_API_KEY"
            autoFocus
          />
          <button type="submit" className="w-full rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700">
            Enter
          </button>
          <p className="mt-4 text-center text-xs text-gray-400">
            The key is <code>INTERNAL_API_KEY</code> from your <code>.env</code> file
          </p>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold text-indigo-600">Admin Dashboard</h1>
          <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">← Back to Dashboard</a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8 grid gap-6 md:grid-cols-4">
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">MRR</p>
            <p className="text-3xl font-bold text-green-600">
              {loadingMrr ? "..." : `$${mrr?.mrr_dollars?.toFixed(2) ?? "0.00"}`}
            </p>
          </div>
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Active Subscriptions</p>
            <p className="text-3xl font-bold text-gray-900">{loadingMrr ? "..." : mrr?.active_subscriptions ?? 0}</p>
          </div>
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">New (30d)</p>
            <p className="text-3xl font-bold text-indigo-600">{loadingMrr ? "..." : mrr?.new_subs_30d ?? 0}</p>
          </div>
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Churn Rate</p>
            <p className="text-3xl font-bold text-red-600">{loadingMrr ? "..." : `${mrr?.churn_rate_pct ?? 0}%`}</p>
          </div>
        </div>

        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">System Health</h2>
          <div className="flex gap-4">
            <a href="http://localhost:8000/health" target="_blank" rel="noreferrer" className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50">API Health</a>
            <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm text-green-700">Containers: 6 running</span>
            <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm text-green-700">DB: PostgreSQL 16</span>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Research Trends (Reddit)</h2>
          {loadingTrends ? (
            <p className="text-gray-500">Loading...</p>
          ) : trends.length === 0 ? (
            <p className="text-sm text-gray-400">No research data received yet. The browser agent on the laptop pushes data periodically.</p>
          ) : (
            <div className="space-y-4">
              {trends.slice(0, 5).map((t) => (
                <div key={t.id} className="rounded border p-4">
                  <p className="mb-2 text-xs text-gray-400">{new Date(t.created_at).toLocaleString()}</p>
                  {t.subreddit_browses && (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">Subreddits Browsed</p>
                      {Array.isArray(t.subreddit_browses) && t.subreddit_browses.map((s: any, i: number) => (
                        <div key={i} className="ml-2 text-sm">
                          <span className="font-medium">r/{s.subreddit}</span>
                          {s.threads && <span className="text-gray-500"> — {s.threads.length} threads</span>}
                        </div>
                      ))}
                    </div>
                  )}
                  {t.keyword_searches && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-1">Keyword Searches</p>
                      {Array.isArray(t.keyword_searches) && t.keyword_searches.map((k: any, i: number) => (
                        <div key={i} className="ml-2 text-sm">
                          <span className="font-medium">&ldquo;{k.query}&rdquo;</span>
                          {k.results && <span className="text-gray-500"> — {k.results.length} results</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
