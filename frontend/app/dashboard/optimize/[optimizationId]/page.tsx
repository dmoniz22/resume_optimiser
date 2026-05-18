"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";

interface OptimizationData {
  id: string;
  status: string;
  pre_score: number | null;
  post_score: number | null;
  original_bullets: { section: string; bullet_index: number; text: string }[] | null;
  optimized_bullets: { section: string; bullet_index: number; original: string; optimized: string; keywords_added: string[]; change_rationale: string }[] | null;
  cover_letter_text: string | null;
  fabrication_flags: { bullet_index: number; fabricated_skills: string[]; action: string }[] | null;
  model_used: string | null;
  processing_time_ms: number | null;
  error_message: string | null;
}

export default function OptimizationResultPage() {
  const { optimizationId } = useParams<{ optimizationId: string }>();
  const { data: session } = useSession();
  const [opt, setOpt] = useState<OptimizationData | null>(null);
  const [loading, setLoading] = useState(true);

  const authHeaders = { Authorization: `Bearer ${(session as any)?.accessToken || ""}` };

  useEffect(() => {
    fetch(`/api/v1/optimizations/${optimizationId}`, { headers: authHeaders })
      .then((r) => r.json())
      .then(setOpt)
      .finally(() => setLoading(false));
  }, [optimizationId]);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!opt) return <p className="text-red-600">Optimization not found.</p>;

  if (opt.status === "failed") {
    return (
      <div className="rounded-lg bg-red-50 p-6">
        <h1 className="text-xl font-bold text-red-700 mb-2">Optimization Failed</h1>
        <p className="text-red-600">{opt.error_message || "Unknown error"}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Optimization Results</h1>
        <div className="flex gap-2">
          <a
            href={`/api/v1/optimizations/${optimizationId}/download`}
            className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
          >
            Download PDF
          </a>
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
        </div>
      </div>

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
        {opt.optimized_bullets?.map((bullet, i) => (
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
                <p className="rounded bg-green-50 p-3 text-sm text-gray-800">{bullet.optimized}</p>
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
