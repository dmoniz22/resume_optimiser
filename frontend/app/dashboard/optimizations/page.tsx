"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";

interface Optimization {
  id: string;
  status: string;
  pre_score: number | null;
  post_score: number | null;
  model_used: string | null;
  processing_time_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

export default function OptimizationsPage() {
  const { data: session } = useSession();
  const [optimizations, setOptimizations] = useState<Optimization[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    fetch("/api/v1/optimizations", {
      headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setOptimizations(d?.optimizations || []))
      .finally(() => setLoading(false));
  }, [session]);

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: "bg-green-100 text-green-700",
      processing: "bg-blue-100 text-blue-700",
      pending: "bg-gray-100 text-gray-600",
      failed: "bg-red-100 text-red-700",
    };
    return `rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || colors.pending}`;
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Optimizations</h1>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : optimizations.length === 0 ? (
        <div className="rounded-lg bg-white p-12 text-center shadow-sm">
          <p className="text-gray-500">No optimizations yet. Upload a resume and select a job description to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {optimizations.map((opt) => (
            <Link
              key={opt.id}
              href={`/dashboard/optimize/${opt.id}`}
              className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={statusBadge(opt.status)}>{opt.status}</span>
                  {opt.pre_score != null && (
                    <span className="text-xs text-gray-500">
                      Score: {opt.pre_score.toFixed(1)} → {opt.post_score?.toFixed(1) ?? "—"}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  {new Date(opt.created_at).toLocaleString()}
                  {opt.model_used && <span className="ml-2">· {opt.model_used}</span>}
                  {opt.processing_time_ms && <span className="ml-2">· {(opt.processing_time_ms / 1000).toFixed(0)}s</span>}
                </p>
              </div>
              <svg className="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
