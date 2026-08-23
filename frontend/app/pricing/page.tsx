"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["3 optimizations/month", "Basic ATS score", "Bullet-by-bullet rewriting", "1 resume storage", "PDF export"],
    priceId: null,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    features: ["Unlimited optimizations", "Detailed ATS score", "Cover letter generation", "10 resume storage", "PDF + DOCX export", "Multiple versions", "Standard email support"],
    priceId: "pro_monthly", highlight: true,
  },
  {
    name: "Career",
    price: "$39",
    period: "/month",
    features: ["Everything in Pro", "Priority AI processing", "Unlimited resume storage", "PDF + DOCX + TXT export", "LinkedIn sync", "Priority support"],
    priceId: "career_monthly",
  },
];

const faqs = [
  {
    q: "Is Resume Optimizer really free?",
    a: "Yes. The Free plan never charges a card and never expires: 3 ATS-scored optimizations per month, bullet-by-bullet rewriting, one stored resume, and PDF export. You only upgrade when you need unlimited optimizations.",
  },
  {
    q: "How does the ATS score work?",
    a: "Paste a job description and the AI compares your resume against the exact skills, keywords, and structure the posting asks for. You get a score before and after rewriting, so you can see what the changes bought you.",
  },
  {
    q: "Will the AI fabricate experience?",
    a: "No. Rewrites only sharpen what is already true in your resume — wording, order, and keyword alignment. The system never invents employers, titles, dates, or achievements.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. Pro and Career are month-to-month with one-click cancellation from your account page, and a 30-day money-back guarantee if you are not satisfied.",
  },
];

export default function PricingPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  async function handleCheckout(priceId: string) {
    if (!session) { router.push("/login"); return; }
    setLoading(priceId);
    try {
      const res = await fetch("/api/v1/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
        body: JSON.stringify({ price_id: priceId }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch (err) { console.error(err); }
    finally { setLoading(null); }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-6">
            <Link href={session ? "/dashboard" : "/"} className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
            <Link href="/blog" className="hidden text-sm text-gray-600 hover:text-gray-900 sm:block">Blog</Link>
            {session && (
              <nav className="hidden sm:flex items-center gap-4">
                <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">Resumes</Link>
                <Link href="/dashboard/optimizations" className="text-sm text-gray-600 hover:text-gray-900">Optimizations</Link>
                <Link href="/dashboard/jds/new" className="text-sm text-gray-600 hover:text-gray-900">Add JD</Link>
              </nav>
            )}
          </div>
          <div className="flex items-center gap-4">
            {session ? (
              <Link href="/dashboard/account" className="text-sm text-gray-600 hover:text-gray-900">
                {(session as any)?.user?.email}
              </Link>
            ) : (
              <>
                <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
                <Link href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</Link>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="px-4 py-16">
        <h1 className="mb-2 text-center text-4xl font-bold text-gray-900">Simple, transparent pricing</h1>
        <p className="mb-12 text-center text-gray-600">Start for free. Upgrade when you need more. 20% off with annual billing.</p>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
          {tiers.map((tier) => (
            <div key={tier.name} className={`rounded-xl border p-8 ${tier.highlight ? "border-indigo-500 shadow-lg ring-1 ring-indigo-500 bg-white" : "bg-white shadow-sm"}`}>
              <h2 className="text-xl font-bold text-gray-900">{tier.name}</h2>
              <p className="mt-4">
                <span className="text-4xl font-bold">{tier.price}</span>
                <span className="text-gray-500">{tier.period}</span>
              </p>
              <ul className="mt-6 space-y-3">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="h-4 w-4 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              {tier.priceId ? (
                <button onClick={() => handleCheckout(tier.priceId!)} disabled={loading === tier.priceId}
                  className={`mt-8 block w-full rounded-lg px-4 py-2.5 text-center text-sm font-medium ${tier.highlight ? "bg-indigo-600 text-white hover:bg-indigo-700" : "bg-gray-800 text-white hover:bg-gray-900"} disabled:opacity-50`}>
                  {loading === tier.priceId ? "Redirecting..." : session ? "Upgrade" : "Get Started"}
                </button>
              ) : (
                <Link href="/signup" className="mt-8 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-center text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Sign Up Free
                </Link>
              )}
            </div>
          ))}
        </div>

        <div className="mx-auto mt-12 max-w-3xl rounded-lg bg-indigo-50 px-6 py-5 text-center">
          <p className="text-sm text-gray-700">
            <span className="font-semibold text-indigo-700">Every plan includes</span> zero-fabrication rewriting, ATS-friendly PDF export, and your data stays yours — no training on your resume content.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-3xl">
          <h2 className="mb-6 text-2xl font-bold text-gray-900">Frequently asked questions</h2>
          <div className="space-y-6">
            {faqs.map((f) => (
              <div key={f.q}>
                <h3 className="text-lg font-semibold text-gray-900">{f.q}</h3>
                <p className="mt-1 text-sm leading-relaxed text-gray-600">{f.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}