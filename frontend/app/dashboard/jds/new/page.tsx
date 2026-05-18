"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function NewJDPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [text, setText] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setCreating(true);
    setError("");

    try {
      const res = await fetch("/api/v1/jds", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${(session as any)?.accessToken || ""}`,
        },
        body: JSON.stringify({ raw_text: text }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed");
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Add Job Description</h1>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={14}
          className="w-full max-w-2xl rounded-md border px-3 py-2 text-sm"
          placeholder="Paste the full job description here. Our AI will extract keywords and requirements automatically."
          required
        />
        <button
          type="submit"
          disabled={creating || !text.trim()}
          className="mt-4 rounded-md bg-indigo-600 px-6 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? "Extracting keywords..." : "Add Job Description"}
        </button>
      </form>
    </div>
  );
}
