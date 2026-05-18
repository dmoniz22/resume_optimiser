"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  const { data: session } = useSession();
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);

  const authHeaders = { Authorization: `Bearer ${(session as any)?.accessToken || ""}` };

  useEffect(() => {
    fetch(`/api/v1/resumes/${id}`, { headers: authHeaders })
      .then((r) => r.json())
      .then(setResume)
      .finally(() => setLoading(false));
  }, [id]);

  async function handleReparse() {
    await fetch(`/api/v1/resumes/${id}/reparse`, { method: "POST", headers: authHeaders });
    window.location.reload();
  }

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!resume) return <p className="text-red-600">Resume not found.</p>;

  const sd = resume.structured_data;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{resume.title}</h1>
        <button
          onClick={handleReparse}
          className="rounded-md border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Re-parse
        </button>
      </div>

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
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700"
          >
            Parse Now
          </button>
        </div>
      )}
    </div>
  );
}
