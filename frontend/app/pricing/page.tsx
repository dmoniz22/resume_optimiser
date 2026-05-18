"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

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
    priceId: "pro_monthly",
    highlight: true,
  },
  {
    name: "Career",
    price: "$39",
    period: "/month",
    features: ["Everything in Pro", "Priority AI processing", "Unlimited resume storage", "PDF + DOCX + TXT export", "LinkedIn sync", "Priority support"],
    priceId: "career_monthly",
  },
];

export default function PricingPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  async function handleCheckout(priceId: string) {
    if (!session) {
      router.push("/login");
      return;
    }

    setLoading(priceId);
    try {
      const res = await fetch("/api/v1/stripe/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${(session as any)?.accessToken || ""}`,
        },
        body: JSON.stringify({ price_id: priceId }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  }

  async function handlePortal() {
    if (!session) return;

    setLoading("portal");
    try {
      const res = await fetch("/api/v1/stripe/portal", {
        headers: {
          Authorization: `Bearer ${(session as any)?.accessToken || ""}`,
        },
      });
      if (res.redirected) {
        window.location.href = res.url;
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <a href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</a>
          <div className="flex items-center gap-4">
            <a href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</a>
            <a href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</a>
          </div>
        </div>
      </header>

      <div className="px-4 py-16">
        <h1 className="mb-4 text-center text-4xl font-bold text-gray-900">Simple, transparent pricing</h1>
        <p className="mb-2 text-center text-gray-600">Start for free. Upgrade when you need more. Cancel anytime.</p>
        <p className="mb-12 text-center text-sm text-gray-400">20% off with annual billing</p>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-xl border p-8 ${tier.highlight ? "border-indigo-500 shadow-lg ring-1 ring-indigo-500 bg-white" : "bg-white shadow-sm"}`}
            >
              <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
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
                <button
                  onClick={() => handleCheckout(tier.priceId!)}
                  disabled={loading === tier.priceId}
                  className={`mt-8 block w-full rounded-lg px-4 py-2.5 text-center text-sm font-medium ${
                    tier.highlight
                      ? "bg-indigo-600 text-white hover:bg-indigo-700"
                      : "bg-gray-800 text-white hover:bg-gray-900"
                  } disabled:opacity-50`}
                >
                  {loading === tier.priceId ? "Redirecting..." : "Get Started"}
                </button>
              ) : (
                <a
                  href="/signup"
                  className="mt-8 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-center text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Sign Up Free
                </a>
              )}
            </div>
          ))}
        </div>

        {session && (
          <div className="mx-auto mt-12 max-w-md text-center">
            <button
              onClick={handlePortal}
              disabled={loading === "portal"}
              className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
            >
              {loading === "portal" ? "Loading..." : "Manage Billing"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
