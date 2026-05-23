"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

interface Section {
  title: string;
  bullets: { text: string; is_quantified: boolean; is_role_title?: boolean }[];
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
  const [editMode, setEditMode] = useState(false);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");

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
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 360000);
    try {
      const res = await fetch(`/api/v1/resumes/${id}/reparse`, {
        method: "POST",
        headers: authHeaders,
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (res.ok) {
        const data = await res.json();
        setResume(data);
      } else {
        const err = await res.json().catch(() => ({ detail: "Re-parse failed" }));
        alert(err.detail || "Re-parse failed");
      }
    } catch (e: any) {
      if (e.name === "AbortError") {
        alert("Re-parse timed out. The AI is taking too long — a basic parse has been applied.");
      } else {
        alert("Could not connect. Please try again.");
      }
    } finally {
      clearTimeout(timeout);
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

  async function handleSaveEdits() {
    if (!resume?.structured_data) return;
    setSaveState("saving");
    const res = await fetch(`/api/v1/resumes/${id}`, {
      method: "PUT",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({ structured_data: resume.structured_data }),
    });
    if (res.ok) {
      const data = await res.json();
      setResume(data);
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } else {
      setSaveState("idle");
      alert("Failed to save");
    }
    setEditMode(false);
  }

  function updateField(path: string, value: any) {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    const keys = path.split(".");
    let obj: any = sd;
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      const next = keys[i + 1];
      if (/^\d+$/.test(next)) {
        if (!obj[k]) obj[k] = [];
      } else {
        if (!obj[k]) obj[k] = {};
      }
      obj = obj[k];
    }
    obj[keys[keys.length - 1]] = value;
    setResume({ ...resume, structured_data: sd });
  }

  function addSection() {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.sections = sd.sections || [];
    sd.sections.push({ title: "New Section", bullets: [{ text: "", is_quantified: false }] });
    setResume({ ...resume, structured_data: sd });
  }

  function removeSection(idx: number) {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.sections.splice(idx, 1);
    setResume({ ...resume, structured_data: sd });
  }

  function addBullet(sectionIdx: number) {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.sections[sectionIdx].bullets.push({ text: "", is_quantified: false });
    setResume({ ...resume, structured_data: sd });
  }

  function removeBullet(sectionIdx: number, bulletIdx: number) {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.sections[sectionIdx].bullets.splice(bulletIdx, 1);
    setResume({ ...resume, structured_data: sd });
  }

  function addEducation() {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.education = sd.education || [];
    sd.education.push({ degree: "", school: "", year: new Date().getFullYear() });
    setResume({ ...resume, structured_data: sd });
  }

  function removeEducation(idx: number) {
    if (!resume?.structured_data) return;
    const sd = JSON.parse(JSON.stringify(resume.structured_data));
    sd.education.splice(idx, 1);
    setResume({ ...resume, structured_data: sd });
  }

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!resume) return <p className="text-red-600">Resume not found.</p>;

  const sd = resume.structured_data;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{resume.title}</h1>
        <div className="flex gap-2">
          {sd && !editMode && (
            <>
              <button onClick={openOptimize} className="rounded-md bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700">
                Optimize
              </button>
              <button onClick={() => setEditMode(true)} className="rounded-md border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">
                Edit
              </button>
            </>
          )}
          {editMode && (
            <>
              <button onClick={handleSaveEdits} disabled={saveState === "saving"} className="rounded-md bg-green-600 px-4 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50">
                {saveState === "saving" ? "Saving..." : saveState === "saved" ? "Saved!" : "Save Changes"}
              </button>
              <button onClick={() => setEditMode(false)} className="rounded-md border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">
                Cancel
              </button>
            </>
          )}
          {!editMode && (
            <button
              onClick={handleReparse}
              disabled={reparsing}
              className="rounded-md border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              {reparsing ? "Parsing..." : "Re-parse"}
            </button>
          )}
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
              <select value={selectedJd} onChange={(e) => setSelectedJd(e.target.value)} className="flex-1 rounded-md border px-3 py-2">
                <option value="">-- Choose a job description --</option>
                {jds.map((jd: any) => (
                  <option key={jd.id} value={jd.id}>
                    {jd.title || "Untitled"} {jd.company ? `at ${jd.company}` : ""}
                  </option>
                ))}
              </select>
              <button onClick={handleOptimize} disabled={!selectedJd || optimizing} className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50">
                {optimizing ? "Optimizing..." : "Optimize"}
              </button>
            </div>
          )}
        </div>
      )}

      {sd ? (
        <div className="space-y-6">
          <div className={`rounded-lg bg-white p-4 shadow-sm ${editMode ? "ring-2 ring-indigo-200" : ""}`}>
            {editMode ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Full Name</label>
                  <input value={sd.full_name || ""} onChange={(e) => updateField("full_name", e.target.value || null)} className="w-full rounded border px-2 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Email</label>
                  <input value={sd.email || ""} onChange={(e) => updateField("email", e.target.value || null)} className="w-full rounded border px-2 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Phone</label>
                  <input value={sd.phone || ""} onChange={(e) => updateField("phone", e.target.value || null)} className="w-full rounded border px-2 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Location</label>
                  <input value={sd.location || ""} onChange={(e) => updateField("location", e.target.value || null)} className="w-full rounded border px-2 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Years Experience</label>
                  <input type="number" value={sd.years_of_experience || ""} onChange={(e) => updateField("years_of_experience", e.target.value ? parseFloat(e.target.value) : null)} className="w-full rounded border px-2 py-1.5 text-sm" />
                </div>
              </div>
            ) : (
              <>
                {sd.full_name && <h2 className="text-xl font-semibold">{sd.full_name}</h2>}
                {sd.email && <p className="text-sm text-gray-600">{sd.email}</p>}
                {sd.phone && <p className="text-sm text-gray-600">{sd.phone}</p>}
                {sd.location && <p className="text-sm text-gray-600">{sd.location}</p>}
                {sd.years_of_experience && <p className="mt-1 text-xs text-indigo-600">{sd.years_of_experience} years experience</p>}
              </>
            )}
          </div>

          {sd.skills_detected && (
            <div className={`rounded-lg bg-white p-4 shadow-sm ${editMode ? "ring-2 ring-indigo-200" : ""}`}>
              <h3 className="mb-2 font-medium">Skills Detected</h3>
              {editMode ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Hard Skills (comma-separated)</label>
                    <textarea
                      value={(sd.skills_detected.hard || []).join(", ")}
                      onChange={(e) => updateField("skills_detected.hard", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))}
                      className="w-full rounded border px-2 py-1.5 text-sm"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Soft Skills (comma-separated)</label>
                    <textarea
                      value={(sd.skills_detected.soft || []).join(", ")}
                      onChange={(e) => updateField("skills_detected.soft", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))}
                      className="w-full rounded border px-2 py-1.5 text-sm"
                      rows={2}
                    />
                  </div>
                </div>
              ) : (
                <>
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
                </>
              )}
            </div>
          )}

          {sd.sections?.map((section, i) => (
            <div key={i} className={`rounded-lg bg-white p-4 shadow-sm ${editMode ? "ring-2 ring-indigo-200" : ""}`}>
              {editMode ? (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <input
                      value={section.title}
                      onChange={(e) => updateField(`sections.${i}.title`, e.target.value)}
                      className="flex-1 rounded border px-2 py-1 text-sm font-medium"
                    />
                    <button onClick={() => removeSection(i)} className="text-xs text-red-600 hover:underline">Remove Section</button>
                  </div>
                  {section.bullets.map((bullet, j) => (
                    <div key={j} className="flex gap-2 mb-2 items-start">
                      <label className="flex items-center gap-1 mt-1.5">
                        <input
                          type="checkbox"
                          checked={bullet.is_role_title || false}
                          onChange={(e) => updateField(`sections.${i}.bullets.${j}.is_role_title`, e.target.checked)}
                          className="h-3 w-3"
                        />
                        <span className="text-xs text-gray-400">Role</span>
                      </label>
                      <textarea
                        value={bullet.text}
                        onChange={(e) => updateField(`sections.${i}.bullets.${j}.text`, e.target.value)}
                        className="flex-1 rounded border px-2 py-1 text-sm"
                        rows={2}
                      />
                      <button onClick={() => removeBullet(i, j)} className="mt-1 text-xs text-red-600 hover:underline">×</button>
                    </div>
                  ))}
                  <button onClick={() => addBullet(i)} className="mt-2 text-xs text-indigo-600 hover:underline">+ Add Bullet</button>
                </div>
              ) : (
                <>
                  <h3 className="mb-3 font-medium text-gray-900">{section.title}</h3>
                  <ul className="space-y-2">
                    {section.bullets.map((bullet, j) => (
                      <li key={j} className={`flex gap-2 text-sm text-gray-700 ${bullet.is_role_title ? "font-bold" : ""}`}>
                        {!bullet.is_role_title && <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gray-400" />}
                        {bullet.text}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          ))}
          {editMode && (
            <button onClick={addSection} className="w-full rounded-lg border-2 border-dashed border-gray-300 p-4 text-sm text-gray-500 hover:border-indigo-300 hover:text-indigo-600">
              + Add Section
            </button>
          )}

          {sd.education && sd.education.length > 0 && (
            <div className={`rounded-lg bg-white p-4 shadow-sm ${editMode ? "ring-2 ring-indigo-200" : ""}`}>
              <h3 className="mb-2 font-medium">Education</h3>
              {editMode ? (
                <div className="space-y-3">
                  {sd.education.map((edu, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <input value={edu.degree || ""} onChange={(e) => updateField(`education.${i}.degree`, e.target.value)} placeholder="Degree" className="flex-1 rounded border px-2 py-1.5 text-sm" />
                      <input value={edu.school || ""} onChange={(e) => updateField(`education.${i}.school`, e.target.value)} placeholder="School" className="flex-1 rounded border px-2 py-1.5 text-sm" />
                      <input type="number" value={edu.year || ""} onChange={(e) => updateField(`education.${i}.year`, e.target.value ? parseInt(e.target.value) : null)} placeholder="Year" className="w-20 rounded border px-2 py-1.5 text-sm" />
                      <button onClick={() => removeEducation(i)} className="text-xs text-red-600 hover:underline">×</button>
                    </div>
                  ))}
                  <button onClick={addEducation} className="text-xs text-indigo-600 hover:underline">+ Add Education</button>
                </div>
              ) : (
                sd.education.map((edu, i) => (
                  <p key={i} className="text-sm text-gray-700">
                    {edu.degree} — {edu.school}{edu.year ? ` (${edu.year})` : ""}
                  </p>
                ))
              )}
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
