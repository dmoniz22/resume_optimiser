"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

// Fully client-side ATS keyword-gap checker. No data leaves the browser.
// Heuristic approach: extract significant tokens/phrases from the job
// description, then report which ones appear in the resume.

const STOPWORDS = new Set([
  "the","a","an","and","or","but","for","with","without","from","into","your",
  "you","we","our","us","to","of","in","on","at","by","is","are","be","been",
  "being","was","were","will","would","could","should","can","may","might",
  "must","shall","have","has","had","do","does","did","this","that","these",
  "those","it","its","as","if","than","then","there","their","they","them",
  "not","no","nor","so","such","all","any","each","every","some","more","most",
  "other","only","own","same","too","very","just","about","between","under",
  "over","through","during","before","after","above","below","up","down",
  "out","off","again","further","once","here","when","where","which","who",
  "whom","whose","what","why","how","both","few","many","much","several",
  "due","per","via","e.g.","etc.","ie","etc","including","including:","across",
  "along","within","without","among","onto","upon","toward","towards","until",
  "while","because","although","however","since","experience","ability",
  "skills","responsibilities","requirements","required","preferred","must",
  "strong","proven","demonstrated","solid","excellent","good","great","ability",
  "knowledge","understanding","familiarity","working","knowledge of","plus",
  "nice","etc","etc.","role","team","work","years","year","minimum","degree",
  "bachelor","bachelor's","masters","master's","phd","relevant","related",
  "other","area","areas","environment","fast-paced","startup","company","business",
]);

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9+#.\-/ ]/g, " ")
    .split(/\s+/)
    .map((t) => t.replace(/\.+$/, "")) // drop trailing dots; keep internal ones (node.js, c++)
    .filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

function extractKeywords(jd: string): { term: string; count: number }[] {
  const tokens = tokenize(jd);
  const counts = new Map<string, number>();
  for (const t of tokens) {
    counts.set(t, (counts.get(t) ?? 0) + 1);
  }
  const sorted = Array.from(counts.entries())
    .map(([term, count]) => ({ term, count }))
    .sort((a, b) => b.count - a.count);

  // Keep the most significant terms (top ~60 by frequency). Skill keywords
  // typically repeat across a JD's skills + responsibilities sections, so
  // frequency ranking surfaces the terms the employer actually cares about.
  return sorted.slice(0, 60);
}

function inResume(resumeLower: string, term: string): boolean {
  // Word-ish boundary check so "java" doesn't match inside "javascript" — but
  // allow tool names like "c++"/"node.js" to match on substring.
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  if (term.includes("+") || term.includes(".") || term.includes("#")) {
    return resumeLower.includes(term);
  }
  return new RegExp(`\\b${escaped}\\b`).test(resumeLower);
}

export default function KeywordGapTool() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [ran, setRan] = useState(false);

  const result = useMemo(() => {
    if (!resume.trim() || !jd.trim()) return null;
    const keywords = extractKeywords(jd);
    const resumeLower = resume.toLowerCase();
    const matched: { term: string; count: number }[] = [];
    const missing: { term: string; count: number }[] = [];
    for (const k of keywords) {
      if (inResume(resumeLower, k.term)) matched.push(k);
      else missing.push(k);
    }
    const score = keywords.length ? Math.round((matched.length / keywords.length) * 100) : 0;
    return { keywords, matched, missing, score };
  }, [resume, jd]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
          <div className="flex items-center gap-4">
            <Link href="/how-to-beat-ats" className="text-sm text-gray-600 hover:text-gray-900">How to Beat ATS</Link>
            <Link href="/blog" className="text-sm text-gray-600 hover:text-gray-900">Blog</Link>
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
            <Link href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-4 py-12">
        <p className="mb-2 text-xs font-medium uppercase text-indigo-600">Free Tool</p>
        <h1 className="mb-4 text-4xl font-bold text-gray-900">ATS Keyword Gap Checker</h1>
        <p className="mb-8 text-gray-600">
          Paste your resume and a job description to see which keywords you're matching — and which ones are missing. Runs entirely in your browser; nothing is uploaded.
        </p>

        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <label htmlFor="resume-input" className="mb-2 block text-sm font-semibold text-gray-900">
              Your resume (paste plain text)
            </label>
            <textarea
              id="resume-input"
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              rows={14}
              placeholder="Paste your resume text here…"
              className="w-full rounded-lg border border-gray-300 bg-white p-3 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="jd-input" className="mb-2 block text-sm font-semibold text-gray-900">
              Job description
            </label>
            <textarea
              id="jd-input"
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              rows={14}
              placeholder="Paste the job description here…"
              className="w-full rounded-lg border border-gray-300 bg-white p-3 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={() => setRan(true)}
            disabled={!resume.trim() || !jd.trim()}
            className="rounded-lg bg-indigo-600 px-8 py-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            Check keyword match
          </button>
          {!resume.trim() || !jd.trim() ? (
            <p className="mt-2 text-xs text-gray-500">Paste both boxes to enable the check.</p>
          ) : null}
        </div>

        {result && (
          <div className="mt-10 rounded-xl border bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-gray-900">Your keyword match</h2>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">Score</span>
                <span className={`text-3xl font-bold ${result.score >= 70 ? "text-green-600" : result.score >= 40 ? "text-amber-500" : "text-red-500"}`}>
                  {result.score}%
                </span>
              </div>
            </div>
            <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-gray-200">
              <div
                className={`h-full rounded-full ${result.score >= 70 ? "bg-green-500" : result.score >= 40 ? "bg-amber-400" : "bg-red-400"}`}
                style={{ width: `${result.score}%` }}
              />
            </div>
            <p className="mt-3 text-sm text-gray-600">
              {result.matched.length} of {result.keywords.length} significant keywords from the job description found in your resume.
              {result.score < 70 ? " Below ~70% you're likely to fall under the ATS cutoff — see the missing list below and weave those terms in." : " That's a strong match — the ATS should rank you well."}
            </p>

            {result.missing.length > 0 ? (
              <div className="mt-6">
                <h3 className="mb-2 font-semibold text-red-700">Missing from your resume ({result.missing.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {result.missing.map((k) => (
                    <span key={k.term} className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">
                      {k.term}
                      {k.count > 1 ? <span className="ml-1 text-red-400">×{k.count}</span> : null}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {result.matched.length > 0 ? (
              <div className="mt-6">
                <h3 className="mb-2 font-semibold text-green-700">Found ({result.matched.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {result.matched.map((k) => (
                    <span key={k.term} className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 ring-1 ring-green-200">
                      {k.term}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mt-8 rounded-lg border border-indigo-200 bg-indigo-50 p-5">
              <p className="text-sm font-semibold text-gray-900">Want the full rewrite?</p>
              <p className="mt-1 text-sm text-gray-700">
                ApplyStudio rewrites your bullets around the job description's keywords — with a zero-fabrication guarantee — and scores the result.{" "}
                <Link href="/signup" className="font-medium text-indigo-600 underline">Try it free</Link>{" "}
                or read{" "}
                <Link href="/how-to-beat-ats" className="font-medium text-indigo-600 underline">how to beat ATS screening</Link>.
              </p>
            </div>
          </div>
        )}

        {!result && ran && (
          <p className="mt-6 text-sm text-gray-500">Paste text into both boxes, then check again.</p>
        )}

        <div className="mt-14 grid gap-10 md:grid-cols-2">
          <div>
            <h2 className="mb-3 text-xl font-bold text-gray-900">How the check works</h2>
            <p className="text-sm leading-relaxed text-gray-600">
              The checker pulls the most significant keywords from the job description — the
              terms that repeat most often, which is what the employer&apos;s ATS and its
              recruiter actually screen for — then compares them against your resume text.
              You get three things back:
            </p>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              <li>• <strong className="text-gray-900">A match score</strong> — the percentage of the job description&apos;s top keywords that appear in your resume.</li>
              <li>• <strong className="text-gray-900">Matched keywords</strong> — what you&apos;re already aligned on, so you can see your strengths at a glance.</li>
              <li>• <strong className="text-gray-900">Missing keywords</strong> — the exact gaps to close before you submit.</li>
            </ul>
          </div>
          <div>
            <h2 className="mb-3 text-xl font-bold text-gray-900">Interpreting your score</h2>
            <div className="space-y-2 text-sm text-gray-600">
              <p><strong className="text-green-700">70%+</strong> — Strong match. The ATS should rank you well for this posting. Consider applying as-is or with light touch-ups.</p>
              <p><strong className="text-amber-600">40–69%</strong> — Borderline. You&apos;re in the conversation but likely below the cutoff for competitive postings. Weave the missing terms in where they honestly fit.</p>
              <p><strong className="text-red-600">Below 40%</strong> — At risk of being filtered before a human reads you. Treat the missing list as your edit checklist — then re-check.</p>
            </div>
          </div>
        </div>

        <div className="mt-14">
          <h2 className="mb-4 text-xl font-bold text-gray-900">How to close keyword gaps without stuffing</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border bg-white p-5">
              <h3 className="mb-2 font-semibold text-gray-900">Mirror the job description&apos;s terms</h3>
              <p className="text-sm text-gray-600">
                If the posting says &ldquo;project management&rdquo; and your resume says &ldquo;oversaw
                initiatives,&rdquo; rephrase to the employer&apos;s wording. Matching language is
                what recruiters expect — it&apos;s not gaming the system.
              </p>
            </div>
            <div className="rounded-lg border bg-white p-5">
              <h3 className="mb-2 font-semibold text-gray-900">Weave keywords into bullets</h3>
              <p className="text-sm text-gray-600">
                A skills list is good, but keywords embedded in your achievement bullets are
                stronger: &ldquo;Cut deployment time 40% using CI/CD and Docker&rdquo; beats a
                bare list of the same tools.
              </p>
            </div>
            <div className="rounded-lg border bg-white p-5">
              <h3 className="mb-2 font-semibold text-gray-900">Never claim what you don&apos;t have</h3>
              <p className="text-sm text-gray-600">
                Adding every missing keyword without the experience to back it up trades an ATS
                pass for a failed interview. Every term on your resume must survive a question
                in the room.
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-600">
            Want someone else to do the weaving?{" "}
            <Link href="/signup" className="font-medium text-indigo-600 underline">ApplyStudio rewrites your bullets</Link>{" "}
            around the job description — with a zero-fabrication guarantee — then scores the result. Or read the full{" "}
            <Link href="/how-to-beat-ats" className="font-medium text-indigo-600 underline">guide to beating ATS screening</Link>.
          </p>
        </div>

        <div className="mt-14">
          <h2 className="mb-4 text-xl font-bold text-gray-900">Why keyword matching matters</h2>
          <p className="mb-3 text-sm leading-relaxed text-gray-600">
            Applicant tracking systems rank every application by how well it matches the job
            requisition — and 75%+ of resumes are filtered out before a recruiter sees them.
            Most rejections aren&apos;t about your experience; they&apos;re about your resume
            not using the hiring team&apos;s vocabulary. A keyword-gap check before you apply is
            the cheapest way to move your candidacy from the reject pile to the shortlist.
          </p>
          <p className="text-sm leading-relaxed text-gray-600">
            This is the same gap analysis our AI-powered optimizer performs on every resume it
            processes — you&apos;re seeing the free, manual version of what the full tool does
            in seconds.
          </p>
        </div>

        <p className="mt-10 text-center text-xs text-gray-400">
          Privacy note: this tool runs 100% in your browser. Your resume and job description never leave your device.
        </p>
      </div>
    </div>
  );
}
