"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";

interface Bullet {
  section: string;
  bullet_index: number;
  original: string;
  optimized: string;
  keywords_added: string[];
  change_rationale: string;
}

interface OptimizationData {
  id: string;
  status: string;
  pre_score: number | null;
  post_score: number | null;
  original_bullets: { section: string; bullet_index: number; text: string }[] | null;
  optimized_bullets: Bullet[] | null;
  cover_letter_text: string | null;
  fabrication_flags: { bullet_index: number; fabricated_skills: string[]; action: string }[] | null;
  model_used: string | null;
  processing_time_ms: number | null;
  error_message: string | null;
  template: string;
}

interface TemplateInfo {
  id: string;
  name: string;
  description: string;
}

export default function OptimizationResultPage() {
  const { optimizationId } = useParams<{ optimizationId: string }>();
  const { data: session } = useSession();
  const [opt, setOpt] = useState<OptimizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("modern");
  const [selectedFormat, setSelectedFormat] = useState("pdf");
  const [editMode, setEditMode] = useState(false);
  const [editedBullets, setEditedBullets] = useState<Bullet[] | null>(null);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const authHeaders = { Authorization: `Bearer ${(session as any)?.accessToken || ""}` };

  useEffect(() => {
    fetch("/api/v1/templates").then(r => r.json()).then(setTemplates).catch(() => {});
  }, []);

  useEffect(() => {
    if (!session) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(`/api/v1/optimizations/${optimizationId}`, { headers: authHeaders });
        if (!res.ok) {
          if (!cancelled) setLoading(false);
          return;
        }
        const data = await res.json();
        if (!cancelled) {
          setOpt(data);
          setSelectedTemplate(data.template || "modern");
          setEditedBullets(data.optimized_bullets ? [...data.optimized_bullets] : null);
        }

        if (data.status === "pending" || data.status === "processing") {
          if (!cancelled) setTimeout(poll, 2000);
        } else {
          if (!cancelled) setLoading(false);
        }
      } catch {
        if (!cancelled) setLoading(false);
      }
    };

    poll();
    return () => { cancelled = true; };
  }, [optimizationId, session]);

  function enterEditMode() {
    setEditedBullets(opt?.optimized_bullets ? [...opt.optimized_bullets] : null);
    setEditMode(true);
  }

  async function saveEdits() {
    if (!editedBullets) return;
    setSaving(true);
    const res = await fetch(`/api/v1/optimizations/${optimizationId}`, {
      method: "PATCH",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({ optimized_bullets: editedBullets }),
    });
    if (res.ok) {
      const updated = await res.json();
      setOpt(updated);
      setEditedBullets(updated.optimized_bullets ? [...updated.optimized_bullets] : null);
    }
    setEditMode(false);
    setSaving(false);
  }

  async function handleDownload() {
    setDownloading(true);
    try {
      const genRes = await fetch(
        `/api/v1/optimizations/${optimizationId}/pdf?template=${selectedTemplate}&format=${selectedFormat}`,
        { method: "POST", headers: authHeaders }
      );
      if (!genRes.ok) {
        alert("Failed to generate file");
        return;
      }
      const blob = await genRes.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `optimized_resume_${optimizationId}.${selectedFormat}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  if (loading || opt?.status === "processing" || opt?.status === "pending") {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
        <p className="text-gray-600">Optimizing your resume...</p>
        <p className="mt-2 text-sm text-gray-400">This may take a minute or two.</p>
      </div>
    );
  }
  if (!opt) return <p className="text-red-600">Optimization not found.</p>;

  if (opt.status === "failed") {
    return (
      <div className="rounded-lg bg-red-50 p-6">
        <h1 className="text-xl font-bold text-red-700 mb-2">Optimization Failed</h1>
        <p className="text-red-600">{opt.error_message || "Unknown error"}</p>
      </div>
    );
  }

  const bullets = editMode && editedBullets ? editedBullets : (opt.optimized_bullets || []);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold">Optimization Results</h1>
        <div className="flex flex-wrap items-center gap-2">
          {templates.length > 0 && (
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">Template:</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="rounded border px-2 py-1.5 text-sm"
              >
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Format:</label>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="rounded border px-2 py-1.5 text-sm"
            >
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
              <option value="txt">TXT</option>
            </select>
          </div>

          {editMode ? (
            <>
              <button
                onClick={saveEdits}
                disabled={saving}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Edits"}
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
              >
                {downloading ? "Generating..." : "Download"}
              </button>
              <button
                onClick={enterEditMode}
                className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Edit Bullets
              </button>
              <button
                onClick={async () => {
                  await fetch(`/api/v1/optimizations/${optimizationId}/regenerate`, {
                    method: "POST",
                    headers: authHeaders,
                  });
                  window.location.reload();
                }}
                className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Regenerate
              </button>
            </>
          )}
        </div>
      </div>

      {templates.length > 0 && (
        <p className="mb-6 text-xs text-gray-400">{templates.find(t => t.id === selectedTemplate)?.description}</p>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-white p-4 shadow-sm text-center">
          <p className="text-sm text-gray-500">Pre-Score</p>
          <p className="text-3xl font-bold text-gray-700">{opt.pre_score?.toFixed(1) ?? "—"}</p>
        </div>
        <div className="rounded-lg bg-white p-4 shadow-sm text-center">
          <p className="text-sm text-gray-500">Post-Score</p>
          <p className="text-3xl font-bold text-green-600">{opt.post_score?.toFixed(1) ?? "—"}</p>
        </div>
        <div className="rounded-lg bg-white p-4 shadow-sm text-center">
          <p className="text-sm text-gray-500">Improvement</p>
          <p className="text-3xl font-bold text-indigo-600">
            {opt.pre_score && opt.post_score
              ? `+${(opt.post_score - opt.pre_score).toFixed(1)}`
              : "—"}
          </p>
        </div>
      </div>

      {opt.fabrication_flags && opt.fabrication_flags.length > 0 && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="font-medium text-amber-800 mb-2">Fabrication Guardrails Activated</h3>
          {opt.fabrication_flags.map((flag, i) => (
            <p key={i} className="text-sm text-amber-700">
              Bullet {flag.bullet_index}: fabricated skills &mdash; {flag.fabricated_skills.join(", ")} &mdash; reverted to original
            </p>
          ))}
        </div>
      )}

      <div className="space-y-4">
        {bullets.map((bullet, i) => (
          <div key={i} className="rounded-lg bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-medium text-gray-400">
                {bullet.section} · Bullet {bullet.bullet_index + 1}
              </span>
              {bullet.keywords_added?.length > 0 && (
                <span className="text-xs text-green-600">
                  +{bullet.keywords_added.join(", ")}
                </span>
              )}
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-medium text-gray-400">Original</p>
                <p className="rounded bg-gray-50 p-3 text-sm text-gray-700">{bullet.original}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-green-600">Optimized</p>
                {editMode ? (
                  <textarea
                    value={bullet.optimized}
                    onChange={(e) => {
                      const updated = [...(editedBullets || [])];
                      updated[i] = { ...updated[i], optimized: e.target.value };
                      setEditedBullets(updated);
                    }}
                    className="w-full rounded border p-3 text-sm text-gray-800 min-h-[80px] resize-y"
                    rows={3}
                  />
                ) : (
                  <p className="rounded bg-green-50 p-3 text-sm text-gray-800">{bullet.optimized}</p>
                )}
              </div>
            </div>

            {bullet.change_rationale && !bullet.change_rationale.includes("REVERTED") && (
              <p className="mt-2 text-xs text-gray-400 italic">{bullet.change_rationale}</p>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 text-xs text-gray-400">
        Model: {opt.model_used} · Processing time: {opt.processing_time_ms ? `${(opt.processing_time_ms / 1000).toFixed(1)}s` : "N/A"}
      </div>
    </div>
  );
}
