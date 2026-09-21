import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How to Beat ATS Resume Screening in 2026 | ApplyStudio",
  description:
    "ATS filters 75%+ of resumes before a human sees them. Learn 7 evidence-based tactics to pass parsing, match keywords, and get your resume shortlisted — free.",
  alternates: { canonical: "https://applystudio.app/how-to-beat-ats" },
  openGraph: {
    title: "How to Beat ATS Resume Screening in 2026 | ApplyStudio",
    description:
      "ATS filters 75%+ of resumes before a human sees them. Learn 7 evidence-based tactics to pass parsing, match keywords, and get your resume shortlisted.",
    url: "https://applystudio.app/how-to-beat-ats",
    type: "article",
  },
};

const tactics = [
  {
    n: "1",
    title: "Use a standard, single-column layout",
    body: "Applicant tracking systems parse resumes into structured fields (name, title, employer, dates). Two-column layouts, tables, text boxes, headers/footers, and graphic decorations routinely break that parse — text ends up out of order or missing entirely. A clean reverse-chronological, single-column format with real headings (Experience, Education, Skills) parses flawlessly in every major ATS. If you want a visual resume, keep a separate version for human-forward applications and always submit the ATS-safe one through portals.",
  },
  {
    n: "2",
    title: "Apply the job description's exact language",
    body: "The single highest-leverage tactic: reuse the employer's own phrasing. If the posting says “project management” and your resume says “oversaw initiatives,” the ATS may never connect the two. Mirror the job description's terms for skills, tools, and titles verbatim — but only where they honestly describe what you did. This is matching, not padding; recruiters do the same keyword scan on the way to the shortlist.",
  },
  {
    n: "3",
    title: "Tailor a fresh version for every application",
    body: "Generic resumes fail both the ATS and the recruiter. Before you apply, pull the 10–15 keywords and required skills from the posting, confirm they appear in your resume, and reorder bullets so your most relevant achievements sit at the top of each role. This is the difference between a resume that scores a 96% match and one that silently falls below the cutoff. Most candidates apply with one resume for fifty jobs; the ones who tailor get the calls.",
  },
  {
    n: "4",
    title: "Put keywords in the right places",
    body: "Where keywords appear matters. Lead with a short Skills section, integrate keywords into job-title lines and bullet points rather than burying them at the end of sentences, and make sure your summary paragraph contains the role's key terms. Parsing quality is best for standard section headings — “Professional Experience” or “Work Experience” — and worst for creative labels like “Where I've Been.”",
  },
  {
    n: "5",
    title: "Spell out acronyms at least once",
    body: "An ATS doesn't know that “PMP” and “Project Management Professional” are the same. If a certification or tool matters, write both: “Project Management Professional (PMP).” The same rule applies to degree names (“MBA, Finance”) and technical stacks (“Kubernetes (K8s)”). Including the full form costs one phrase and guarantees you match every variant of the query.",
  },
  {
    n: "6",
    title: "Quantify outcomes, not duties",
    body: "ATS scoring is increasingly driven by match percentage, but the human who reads the shortlist is still the final gate — and humans buy outcomes. Replace duty lists with numbers: “Managed a team of 9” beats “Team management,” and “Cut onboarding time 30%” beats “Improved onboarding.” A resume full of metrics also reads as senior and credible, which matters more for mid-career and above roles.",
  },
  {
    n: "7",
    title: "Save and upload the right file type",
    body: "Uploading is where many applications silently die. Use .docx (best compatibility across Workday, Greenhouse, Lever, Taleo) or a text-based PDF — never an image-only PDF, scanned document, or JPG. Name the file professionally (“Firstname-Lastname-Resume.docx”) and check one more time that dates are consistent, the file isn't password-protected, and a text extractor can read it: paste the content into Notepad and confirm it isn't gibberish.",
  },
];

const faqs = [
  {
    q: "Do ATS systems reject resumes automatically?",
    a: "Most don't “reject” outright — they rank. Candidates below a match threshold are usually screened out before a recruiter sees them, which is why scoring low on keywords feels like a rejection. The fix is a higher match rate, not a magic format.",
  },
  {
    q: "Is it cheating to mirror keywords from the job description?",
    a: "No — it's the intended workflow. Recruiters expect to see the posting's language reflected in qualified applications. The line is crossed only when you claim skills you don't actually have. Mirror honestly, never fabricate.",
  },
  {
    q: "Do human recruiters still read resumes behind the ATS?",
    a: "Yes. In most companies a recruiter reviews every resume that clears the threshold. The ATS is a filter, not the decision-maker. That's why the strongest strategy is both: high keyword match for the machine, and clean, quantifiable achievements for the person.",
  },
  {
    q: "Should I use a PDF or a Word file?",
    a: "A .docx file is the safest across systems; a properly text-based PDF is a close second. Avoid image-only PDFs entirely — many ATS can't OCR them, and you'll look like a zero-match candidate despite a perfect resume.",
  },
];

export default function HowToBeatAtsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
          <div className="flex items-center gap-4">
            <Link href="/tools/keyword-gap" className="text-sm text-gray-600 hover:text-gray-900">Free ATS Keyword Checker</Link>
            <Link href="/blog" className="text-sm text-gray-600 hover:text-gray-900">Blog</Link>
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
            <Link href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-12">
        <p className="mb-2 text-xs font-medium uppercase text-indigo-600">ATS Guide</p>
        <h1 className="mb-4 text-4xl font-bold text-gray-900">How to Beat ATS Resume Screening (Without Gaming It)</h1>
        <p className="mb-6 text-gray-600">
          Updated for 2026 · 10-minute read · No fluff, no hacks — tactics that work with the machines <em>and</em> the people behind them.
        </p>

        <div className="mb-10 rounded-lg border border-indigo-200 bg-indigo-50 p-6">
          <p className="font-semibold text-gray-900">The one-sentence version</p>
          <p className="mt-2 text-gray-700">
            75%+ of resumes are filtered out by applicant tracking systems before a human sees them — but the filter is predictable, so the fix is learnable: match the job description's language, use a parse-friendly layout, and prove every claim with numbers.
          </p>
          <p className="mt-3 text-sm text-gray-600">
            Want the fast path? Run your resume against a job description with our{" "}
            <Link href="/tools/keyword-gap" className="font-medium text-indigo-600 underline">free ATS keyword-gap checker</Link>{" "}
            before you apply.
          </p>
        </div>

        <h2 className="mb-4 text-2xl font-bold text-gray-900">What the ATS actually does</h2>
        <p className="mb-4 text-gray-700">
          An applicant tracking system (ATS) is a database. It receives your application, extracts structured fields from your resume (experience, education, skills, contact info), and scores how well those fields match the job requisition. Recruiters then see a ranked list. When the posting attracts hundreds of applicants, the recruiter's time budget means only the top-scoring resumes get a real read.
        </p>
        <p className="mb-10 text-gray-700">
          Two myths to drop first: ATS systems don't “hunt for hidden tricks,” and there is no secret font that guarantees a pass. Modern systems (Workday, Greenhouse, Lever, iCIMS, Taleo) mostly parse plain text well — the failures come from layout, missing language, and mismatched terms. Beat the parser and the keyword match, and you clear the filter honestly.
        </p>

        <h2 className="mb-6 text-2xl font-bold text-gray-900">The 7 tactics that actually move your match score</h2>
        <div className="space-y-6">
          {tactics.map((t) => (
            <div key={t.n} className="rounded-lg border bg-white p-6 shadow-sm">
              <h3 className="mb-2 text-lg font-semibold text-gray-900">
                <span className="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-600">{t.n}</span>
                {t.title}
              </h3>
              <p className="text-sm leading-relaxed text-gray-600">{t.body}</p>
            </div>
          ))}
        </div>

        <div className="my-10 rounded-lg border border-indigo-200 bg-indigo-50 p-6">
          <h3 className="text-lg font-semibold text-gray-900">Check your match before you hit submit</h3>
          <p className="mt-2 text-sm text-gray-700">
            Paste your resume and the job description into our{" "}
            <Link href="/tools/keyword-gap" className="font-medium text-indigo-600 underline">free keyword-gap checker</Link>{" "}
            and see exactly which keywords you're missing — in about 30 seconds. Then fix your resume, re-check, and apply with confidence.
          </p>
        </div>

        <h2 className="mb-6 text-2xl font-bold text-gray-900">Frequently asked questions</h2>
        <div className="space-y-4">
          {faqs.map((f) => (
            <div key={f.q} className="rounded-lg border bg-white p-6 shadow-sm">
              <h3 className="mb-2 font-semibold text-gray-900">{f.q}</h3>
              <p className="text-sm leading-relaxed text-gray-600">{f.a}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 rounded-xl bg-gray-900 p-8 text-center">
          <h2 className="text-2xl font-bold text-white">Ready to stop being filtered out?</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-gray-300">
            Resume Optimizer rewrites your bullets to match the job description's keywords — with a zero-fabrication guarantee. Paste your resume and a JD and see your match score instantly.
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <Link href="/signup" className="rounded-lg bg-indigo-500 px-8 py-3 text-sm font-medium text-white hover:bg-indigo-400">Get Started Free</Link>
            <Link href="/tools/keyword-gap" className="rounded-lg border border-gray-600 px-8 py-3 text-sm font-medium text-gray-200 hover:bg-gray-800">Try the Free Checker</Link>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-gray-400">
          More on our <Link href="/blog" className="underline">resume advice blog</Link> ·{" "}
          <Link href="/tools/keyword-gap" className="underline">Free ATS keyword checker</Link>
        </p>
      </div>
    </div>
  );
}
