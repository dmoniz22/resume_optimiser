"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";

interface Resume {
  id: string;
  title: string;
  file_type: string | null;
  structured_data: any;
  created_at: string;
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    async function fetchResumes() {
      try {
        const res = await fetch("/api/v1/resumes", {
          headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
        });
        if (res.ok) {
          const data = await res.json();
          setResumes(data.resumes);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchResumes();
  }, [session]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Resumes</h1>
        <Link
          href="/dashboard/upload"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700"
        >
          Upload New
        </Link>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : resumes.length === 0 ? (
        <div className="rounded-lg bg-white p-12 text-center shadow-sm">
          <p className="text-gray-500 mb-4">No resumes yet. Upload your first resume to get started.</p>
          <Link
            href="/dashboard/upload"
            className="inline-block rounded-md bg-indigo-600 px-6 py-2 text-white hover:bg-indigo-700"
          >
            Upload Resume
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resumes.map((r) => (
            <Link
              key={r.id}
              href={`/dashboard/resumes/${r.id}`}
              className="rounded-lg bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="font-semibold text-gray-900 truncate">{r.title}</h3>
              <p className="mt-1 text-sm text-gray-500">
                {r.file_type?.toUpperCase()} · {new Date(r.created_at).toLocaleDateString()}
              </p>
              {r.structured_data && (
                <p className="mt-2 text-xs text-green-600">Parsed</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
