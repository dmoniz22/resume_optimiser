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

interface UserData {
  id: string;
  email: string;
  full_name: string | null;
  auth_provider: string;
  email_verified: boolean;
  tier: string;
  optimizations: number;
  created_at: string;
}

interface TierData {
  id: string;
  name: string;
  monthly_price_cents: number | null;
  credits_per_month: number | null;
  features: Record<string, any> | null;
  is_active: boolean;
}

interface ModelsData {
  rewrite: string;
  parse: string;
  extract: string;
  cover_letter: string;
  embedding: string;
  cloud_base_url: string;
  local_url: string;
}

type Tab = "overview" | "users" | "tiers" | "models";

export default function AdminPage() {
  const [key, setKey] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [authError, setAuthError] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(false);

  const [mrr, setMrr] = useState<MRRData | null>(null);
  const [users, setUsers] = useState<UserData[]>([]);
  const [tiers, setTiers] = useState<TierData[]>([]);
  const [models, setModels] = useState<ModelsData | null>(null);
  const [editTierId, setEditTierId] = useState<string | null>(null);

  function authHeaders() {
    return { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
  }

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim()) return;
    setLoading(true);
    setAuthError("");

    const h = { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };

    Promise.all([
      fetch("/api/v1/internal/agents/financial", { method: "POST", headers: h }).then((r) => (r.ok ? r.json() : null)),
      fetch("/api/v1/internal/agents/users", { headers: h }).then((r) => (r.ok ? r.json() : null)),
      fetch("/api/v1/internal/agents/tiers", { headers: h }).then((r) => (r.ok ? r.json() : null)),
      fetch("/api/v1/internal/agents/models", { headers: h }).then((r) => (r.ok ? r.json() : null)),
    ]).then(([mrrData, userData, tierData, modelData]) => {
      if (!mrrData && !userData && !tierData) {
        setAuthError("Invalid admin key");
        setLoading(false);
        return;
      }
      setMrr(mrrData);
      setUsers(Array.isArray(userData) ? userData : []);
      setTiers(Array.isArray(tierData) ? tierData : []);
      setModels(modelData);
      setAuthenticated(true);
      setLoading(false);
    });
  }

  async function assignTier(userId: string, tierName: string) {
    await fetch(`/api/v1/internal/agents/users/${userId}/tier`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ tier: tierName }),
    });
    const res = await fetch("/api/v1/internal/agents/users", { headers: authHeaders() });
    setUsers(Array.isArray(await res.json()) ? await res.json() : []);
  }

  async function deleteUser(userId: string, email: string) {
    if (!confirm(`Permanently delete ${email} and all their data?`)) return;
    await fetch(`/api/v1/internal/agents/users/${userId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    const res = await fetch("/api/v1/internal/agents/users", { headers: authHeaders() });
    setUsers(Array.isArray(await res.json()) ? await res.json() : []);
  }

  async function createUser(e: React.FormEvent) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const body: Record<string, string> = {};
    form.forEach((v, k) => { body[k] = v as string; });
    const res = await fetch("/api/v1/internal/agents/users", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      alert((await res.json()).detail || "Failed to create user");
      return;
    }
    e.currentTarget.reset();
    const usersRes = await fetch("/api/v1/internal/agents/users", { headers: authHeaders() });
    setUsers(Array.isArray(await usersRes.json()) ? await usersRes.json() : []);
  }

  async function updateTier(tierId: string, updates: Partial<TierData>) {
    await fetch(`/api/v1/internal/agents/tiers/${tierId}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(updates),
    });
    const res = await fetch("/api/v1/internal/agents/tiers", { headers: authHeaders() });
    setTiers(Array.isArray(await res.json()) ? await res.json() : []);
    setEditTierId(null);
  }

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <form onSubmit={handleLogin} className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
          <h1 className="mb-6 text-xl font-bold text-center text-gray-900">Admin Dashboard</h1>
          {authError && <p className="mb-4 text-sm text-red-600 text-center">{authError}</p>}
          <input
            type="password" value={key} onChange={(e) => setKey(e.target.value)}
            className="w-full rounded-md border px-3 py-2 mb-4" placeholder="Enter INTERNAL_API_KEY"
            autoComplete="new-password" autoFocus
          />
          <button type="submit" disabled={loading} className="w-full rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? "Loading..." : "Enter"}
          </button>
          <p className="mt-4 text-center text-xs text-gray-400">The key is <code>INTERNAL_API_KEY</code> from <code>.env</code></p>
        </form>
      </div>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "users", label: `Users (${users.length})` },
    { key: "tiers", label: "Tiers" },
    { key: "models", label: "AI Models" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold text-indigo-600">Admin Dashboard</h1>
          <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">← Back to Dashboard</a>
        </div>
        <nav className="mx-auto max-w-7xl px-4 flex gap-1 border-t">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {tab === "overview" && (
          <>
            <div className="mb-8 grid gap-6 md:grid-cols-4">
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <p className="text-sm text-gray-500">MRR</p>
                <p className="text-3xl font-bold text-green-600">${mrr?.mrr_dollars?.toFixed(2) ?? "0.00"}</p>
              </div>
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <p className="text-sm text-gray-500">Active Subscriptions</p>
                <p className="text-3xl font-bold text-gray-900">{mrr?.active_subscriptions ?? 0}</p>
              </div>
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <p className="text-sm text-gray-500">New (30d)</p>
                <p className="text-3xl font-bold text-indigo-600">{mrr?.new_subs_30d ?? 0}</p>
              </div>
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <p className="text-sm text-gray-500">Churn Rate</p>
                <p className="text-3xl font-bold text-red-600">{mrr?.churn_rate_pct ?? 0}%</p>
              </div>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">System Health</h2>
              <div className="flex flex-wrap gap-3">
                <a href="http://localhost:8000/health" target="_blank" rel="noreferrer" className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50">API Health</a>
                <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm text-green-700">Containers: 6 running</span>
                <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm text-green-700">DB: PostgreSQL 16</span>
                <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm text-green-700">{users.length} registered users</span>
              </div>
            </div>
          </>
        )}

        {tab === "users" && (
          <>
            <form onSubmit={createUser} className="mb-4 rounded-lg bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Email</label>
                  <input name="email" type="email" required className="rounded border px-2 py-1.5 text-sm w-48" placeholder="beta@example.com" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Name</label>
                  <input name="full_name" type="text" className="rounded border px-2 py-1.5 text-sm w-36" placeholder="Jane Doe" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Password</label>
                  <input name="password" type="text" className="rounded border px-2 py-1.5 text-sm w-36" placeholder="changeme123" defaultValue="changeme123" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Tier</label>
                  <select name="tier" className="rounded border px-2 py-1.5 text-sm">
                    <option value="free">Free</option>
                    <option value="pro">Pro</option>
                    <option value="career">Career</option>
                  </select>
                </div>
                <button type="submit" className="rounded-md bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700">Add User</button>
              </div>
            </form>
            <div className="rounded-lg bg-white shadow-sm overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Tier</th>
                  <th className="px-4 py-3 font-medium">Optimizations</th>
                  <th className="px-4 py-3 font-medium">Joined</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                  <th className="px-4 py-3 font-medium w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">{u.email}</td>
                    <td className="px-4 py-3 text-gray-600">{u.full_name || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.tier === "career" ? "bg-purple-100 text-purple-700" :
                        u.tier === "pro" ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-600"
                      }`}>{u.tier}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{u.optimizations}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <select
                        value={u.tier}
                        onChange={(e) => assignTier(u.id, e.target.value)}
                        className="rounded border px-2 py-1 text-xs"
                      >
                        <option value="free">Free</option>
                        <option value="pro">Pro</option>
                        <option value="career">Career</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => deleteUser(u.id, u.email)}
                        className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                        title="Delete user and all data"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No users yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
          </>
        )}

        {tab === "tiers" && (
          <div className="space-y-4">
            {tiers.map((tier) => (
              <div key={tier.id} className="rounded-lg bg-white p-6 shadow-sm">
                {editTierId === tier.id ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = new FormData(e.currentTarget);
                      updateTier(tier.id, {
                        monthly_price_cents: parseInt(form.get("price_cents") as string) || 0,
                        credits_per_month: parseInt(form.get("credits") as string) || null,
                        is_active: form.get("is_active") === "true",
                      });
                    }}
                    className="space-y-3"
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <h3 className="text-lg font-semibold capitalize">{tier.name}</h3>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${tier.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {tier.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Price (cents)</label>
                        <input name="price_cents" type="number" defaultValue={tier.monthly_price_cents ?? 0} className="w-full rounded border px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Credits/month</label>
                        <input name="credits" type="number" defaultValue={tier.credits_per_month ?? ""} placeholder="null = unlimited" className="w-full rounded border px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Active</label>
                        <select name="is_active" defaultValue={tier.is_active ? "true" : "false"} className="w-full rounded border px-2 py-1 text-sm">
                          <option value="true">Yes</option>
                          <option value="false">No</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button type="submit" className="rounded-md bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700">Save</button>
                      <button type="button" onClick={() => setEditTierId(null)} className="rounded-md border px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                    </div>
                  </form>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold capitalize">{tier.name}</h3>
                        <span className={`rounded-full px-2 py-0.5 text-xs ${tier.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                          {tier.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                      <button onClick={() => setEditTierId(tier.id)} className="text-sm text-indigo-600 hover:underline">Edit</button>
                    </div>
                    <div className="flex gap-8 text-sm text-gray-600">
                      <span>${tier.monthly_price_cents ? (tier.monthly_price_cents / 100).toFixed(2) : "0.00"}/mo</span>
                      <span>{tier.credits_per_month ?? "Unlimited"} credits</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "models" && models && (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <h2 className="mb-1 text-lg font-semibold text-gray-900">AI Model Configuration</h2>
            <p className="mb-4 text-sm text-gray-400">To change these, update <code>.env</code> and restart the backend container.</p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">Resume Parsing</p>
                <p className="font-mono text-sm">{models.parse}</p>
              </div>
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">JD Extraction</p>
                <p className="font-mono text-sm">{models.extract}</p>
              </div>
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">Bullet Rewriting</p>
                <p className="font-mono text-sm">{models.rewrite}</p>
              </div>
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">Cover Letters</p>
                <p className="font-mono text-sm">{models.cover_letter}</p>
              </div>
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">Embeddings</p>
                <p className="font-mono text-sm">{models.embedding}</p>
              </div>
              <div className="rounded border p-3">
                <p className="text-xs text-gray-500">Embedding URL</p>
                <p className="font-mono text-xs">{models.local_url}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
