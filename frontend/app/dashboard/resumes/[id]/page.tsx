"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

interface Section {
  title: string;
  bullets: { text: string; is_quantified: boolean }[];
}

interface ResumeData {
  id: string;
  title: string;
  file_type: string;
  structured_data: {
    full_name?: string;
    email?: string;
    phone?: string;
    location?: string;
    sections?: Section[];
    skills_detected?: { hard: string[]; soft: string[] };
    years_of_experience?: number;
    education?: { degree: string; school: string; year: number }[];
  } | null;
  created_at: string;
}

export default function ResumeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: session } = useSession();
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showOptimize, setShowOptimize] = useState(false);
  const [jds, setJds] = useState<any[]>([]);
  const [selectedJd, setSelectedJd] = useState("");
  const [optimizing, setOptimizing] = useState(false);
  const [optError, setOptError] = useState("");

  const [reparsing, setReparsing] = useState(false);

  const authHeaders = { Authorization: `Bearer ${(session as any)?.accessToken || ""}` };

  useEffect(() => {
    if (!session) return;
    fetch(`/api/v1/resumes/${id}`, { headers: authHeaders })
      .then((r) => (r.ok ? r.json() : null))
      .then(setResume)
      .finally(() => setLoading(false));
  }, [id, session]);

  async function handleReparse() {
    setReparsing(true);
    const res = await fetch(`/api/v1/resumes/${id}/reparse`, { method: "POST", headers: authHeaders });
    if (res.ok) {
      window.location.reload();
    } else {
      alert("Re-parse failed. Check console for details.");
      setReparsing(false);
    }
  }

  async function handleOptimize() {
    if (!selectedJd) return;
    setOptimizing(true);
    setOptError("");

    try {
      const res = await fetch("/api/v1/optimize", {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ resume_id: id, jd_id: selectedJd }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || "Failed to start optimization");
      }
      const data = await res.json();

      await fetch(`/api/v1/optimizations/${data.id}/process`, {
        method: "POST",
        headers: authHeaders,
      });

      router.push(`/dashboard/optimize/${data.id}`);
    } catch (err: any) {
      setOptError(err.message);
    } finally {
      setOptimizing(false);
    }
  }

  function openOptimize() {
    fetch("/api/v1/jds", { headers: authHeaders })
      .then((r) => r.json())
      .then((d) => setJds(d.jds || []));
    setShowOptimize(true);
  }

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!resume) return <p className="text-red-600">Resume not found.</p>;

  const sd = resume.structured_data;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{resume.title}</h1>
        <div className="flex gap-2">
          <button
            onClick={openOptimize}
            className="rounded-md bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700"
          >
            Optimize
          </button>
          <button
            onClick={handleReparse}
            disabled={reparsing}
            className="rounded-md border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            {reparsing ? "Parsing..." : "Re-parse"}
          </button>
        </div>
      </div>

      {showOptimize && (
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <h3 className="font-medium mb-3">Select Job Description</h3>
          {optError && <p className="mb-3 text-sm text-red-600">{optError}</p>}
          {jds.length === 0 ? (
            <p className="text-sm text-gray-500">No job descriptions yet. Create one first.</p>
          ) : (
            <div className="flex gap-3 items-end">
              <select
                value={selectedJd}
                onChange={(e) => setSelectedJd(e.target.value)}
                className="flex-1 rounded-md border px-3 py-2"
              >
                <option value="">-- Choose a job description --</option>
                {jds.map((jd: any) => (
                  <option key={jd.id} value={jd.id}>
                    {jd.title || "Untitled"} {jd.company ? `at ${jd.company}` : ""}
                  </option>
                ))}
              </select>
              <button
                onClick={handleOptimize}
                disabled={!selectedJd || optimizing}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {optimizing ? "Optimizing..." : "Optimize"}
              </button>
            </div>
          )}
        </div>
      )}

      {sd ? (
        <div className="space-y-6">
          {sd.full_name && (
            <div className="rounded-lg bg-white p-4 shadow-sm">
              <h2 className="text-xl font-semibold">{sd.full_name}</h2>
              {sd.email && <p className="text-sm text-gray-600">{sd.email}</p>}
              {sd.phone && <p className="text-sm text-gray-600">{sd.phone}</p>}
              {sd.location && <p className="text-sm text-gray-600">{sd.location}</p>}
              {sd.years_of_experience && (
                <p className="mt-1 text-xs text-indigo-600">{sd.years_of_experience} years experience</p>
              )}
            </div>
          )}

          {sd.skills_detected && (
            <div className="rounded-lg bg-white p-4 shadow-sm">
              <h3 className="mb-2 font-medium">Skills Detected</h3>
              {sd.skills_detected.hard?.length > 0 && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-500">Hard Skills: </span>
                  {sd.skills_detected.hard.map((s, i) => (
                    <span key={i} className="mr-1 inline-block rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">{s}</span>
                  ))}
                </div>
              )}
              {sd.skills_detected.soft?.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-500">Soft Skills: </span>
                  {sd.skills_detected.soft.map((s, i) => (
                    <span key={i} className="mr-1 inline-block rounded bg-green-50 px-2 py-0.5 text-xs text-green-700">{s}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {sd.sections?.map((section, i) => (
            <div key={i} className="rounded-lg bg-white p-4 shadow-sm">
              <h3 className="mb-3 font-medium text-gray-900">{section.title}</h3>
              <ul className="space-y-2">
                {section.bullets.map((bullet, j) => (
                  <li key={j} className="flex gap-2 text-sm text-gray-700">
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gray-400" />
                    {bullet.text}
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {sd.education?.length > 0 && (
            <div className="rounded-lg bg-white p-4 shadow-sm">
              <h3 className="mb-2 font-medium">Education</h3>
              {sd.education.map((edu, i) => (
                <p key={i} className="text-sm text-gray-700">
                  {edu.degree} — {edu.school}{edu.year ? ` (${edu.year})` : ""}
                </p>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-lg bg-white p-8 text-center shadow-sm">
          <p className="text-gray-500 mb-4">This resume hasn&apos;t been parsed yet.</p>
          <button
            onClick={handleReparse}
            disabled={reparsing}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {reparsing ? "Parsing..." : "Parse Now"}
          </button>
        </div>
      )}
    </div>
  );
}
