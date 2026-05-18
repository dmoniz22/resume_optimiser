import Link from "next/link";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["3 optimizations/month", "ATS score analysis", "Bullet-by-bullet rewriting", "1 resume storage", "PDF export"],
    cta: "Get Started",
    href: "/signup",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    features: ["Unlimited optimizations", "Detailed ATS score", "Cover letter generation", "10 resume storage", "PDF + DOCX export", "Multiple versions", "Standard email support"],
    cta: "Start Free Trial",
    href: "/signup",
    highlight: true,
  },
  {
    name: "Career",
    price: "$39",
    period: "/month",
    features: ["Everything in Pro", "Priority AI processing", "Unlimited resume storage", "PDF + DOCX + TXT export", "LinkedIn sync", "Priority support"],
    cta: "Start Free Trial",
    href: "/signup",
    highlight: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-xl font-bold text-indigo-600">Resume Optimizer</span>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
            <Link href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</Link>
          </div>
        </div>
      </header>

      <section className="px-4 py-20 text-center">
        <h1 className="mx-auto max-w-3xl text-5xl font-bold tracking-tight text-gray-900">
          AI-powered resumes tailored to every job
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600">
          Stop sending generic resumes. Our AI rewrites your bullets to match each job description while guaranteeing zero fabrication of your experience.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link href="/signup" className="rounded-lg bg-indigo-600 px-8 py-3 text-lg font-medium text-white hover:bg-indigo-700">
            Get Started Free
          </Link>
          <Link href="#pricing" className="rounded-lg border px-8 py-3 text-lg font-medium text-gray-700 hover:bg-gray-50">
            View Pricing
          </Link>
        </div>
      </section>

      <section className="bg-white px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">How It Works</h2>
          <div className="grid gap-8 md:grid-cols-3">
            {[
              { step: "1", title: "Upload Your Resume", desc: "Upload your existing resume in PDF, DOCX, or TXT format. Our AI parses and structures your experience automatically." },
              { step: "2", title: "Paste a Job Description", desc: "Copy any job posting. Our AI extracts key requirements, skills, and keywords to match against." },
              { step: "3", title: "Get Optimized Bullets", desc: "Each bullet is rewritten to match the target role while preserving your real experience. No fabrication. Ever." },
            ].map((item) => (
              <div key={item.step} className="rounded-lg border bg-gray-50 p-6 text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-xl font-bold text-indigo-600">{item.step}</div>
                <h3 className="mb-2 font-semibold text-gray-900">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="bg-gray-50 px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-gray-900">Simple Pricing</h2>
          <p className="mb-12 text-center text-gray-600">Start free. Upgrade when you need more.</p>
          <div className="grid gap-8 md:grid-cols-3">
            {tiers.map((tier) => (
              <div key={tier.name} className={`rounded-xl border p-8 ${tier.highlight ? "border-indigo-500 shadow-lg ring-1 ring-indigo-500" : "bg-white shadow-sm"}`}>
                <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                <p className="mt-4">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="text-gray-500">{tier.period}</span>
                </p>
                <ul className="mt-6 space-y-3">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <svg className="h-4 w-4 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href={tier.href} className={`mt-8 block w-full rounded-lg px-4 py-2.5 text-center text-sm font-medium ${tier.highlight ? "bg-indigo-600 text-white hover:bg-indigo-700" : "bg-gray-800 text-white hover:bg-gray-900"}`}>
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white px-4 py-16">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-6 text-3xl font-bold text-gray-900">The Anti-Fabrication Guarantee</h2>
          <p className="mb-4 text-lg text-gray-600">
            Unlike other tools, we never invent experience you don&apos;t have. Our validation layer catches every fabricated skill and reverts it to your original text.
          </p>
          <p className="text-sm text-gray-500">
            Your career is too important for AI hallucinations. We optimize your wording, not your history.
          </p>
        </div>
      </section>

      <footer className="border-t bg-white px-4 py-8">
        <div className="mx-auto max-w-6xl text-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} Resume Architect. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
