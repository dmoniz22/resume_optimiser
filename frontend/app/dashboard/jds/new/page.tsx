"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function NewJDPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [existingJds, setExistingJds] = useState<any[]>([]);

  const authHeaders = { Authorization: `Bearer ${(session as any)?.accessToken || ""}`, "Content-Type": "application/json" };

  useEffect(() => {
    if (!session) return;
    fetch("/api/v1/jds", { headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` } })
      .then((r) => r.json())
      .then((d) => setExistingJds(d.jds || []));
  }, [session]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setCreating(true);
    setError("");

    try {
      const res = await fetch("/api/v1/jds", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ raw_text: text }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed");
      const jd = await res.json();

      if (title && jd.id) {
        await fetch(`/api/v1/resumes/${jd.id}`, { method: "PUT", headers: authHeaders });
      }

      setText("");
      setTitle("");
      setCompany("");
      const refresh = await fetch("/api/v1/jds", {
        headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
      });
      const d = await refresh.json();
      setExistingJds(d.jds || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Job Descriptions</h1>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="mb-8 rounded-lg bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold text-gray-900">Add New</h2>
        <div className="mb-3 flex gap-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Job Title (e.g. Senior Backend Engineer)"
          />
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Company (e.g. TechCorp)"
          />
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          className="w-full rounded-md border px-3 py-2 text-sm"
          placeholder="Paste the full job description here. Keywords and requirements will be extracted automatically."
          required
        />
        <button
          type="submit"
          disabled={creating || !text.trim()}
          className="mt-3 rounded-md bg-indigo-600 px-6 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? "Extracting..." : "Add Job Description"}
        </button>
      </form>

      {existingJds.length > 0 && (
        <div className="rounded-lg bg-white shadow-sm">
          <h2 className="px-6 pt-6 font-semibold text-gray-900">Saved ({existingJds.length})</h2>
          <div className="divide-y">
            {existingJds.map((jd: any) => (
              <div key={jd.id} className="flex items-start justify-between p-4 hover:bg-gray-50">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {jd.title || "Untitled"}
                    {jd.company ? <span className="text-gray-500 font-normal"> at {jd.company}</span> : ""}
                  </p>
                  <p className="mt-1 text-xs text-gray-400 line-clamp-2">{jd.raw_text}</p>
                  {jd.extracted_keywords && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {(jd.extracted_keywords.hard_skills || []).slice(0, 5).map((s: string, i: number) => (
                        <span key={i} className="rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-600">{s}</span>
                      ))}
                      {jd.extracted_keywords.hard_skills?.length > 5 && (
                        <span className="text-xs text-gray-400">+{jd.extracted_keywords.hard_skills.length - 5} more</span>
                      )}
                    </div>
                  )}
                </div>
                <button
                  onClick={async () => {
                    await fetch(`/api/v1/jds/${jd.id}`, {
                      method: "DELETE",
                      headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
                    });
                    const refresh = await fetch("/api/v1/jds", {
                      headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
                    });
                    setExistingJds((await refresh.json()).jds || []);
                  }}
                  className="ml-4 text-xs text-red-600 hover:underline flex-shrink-0"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
